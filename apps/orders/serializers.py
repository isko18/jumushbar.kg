from rest_framework import serializers
from apps.orders.models import Category, Order, OrderPhoto, OrderResponse, OrderRespondLog, Review
from apps.users.models import User
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import APIException

class CategorySerializer(serializers.ModelSerializer):
    order_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'order_count']


class OrderPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPhoto
        fields = ['id', 'image']


class OrderSerializer(serializers.ModelSerializer):
    photos = OrderPhotoSerializer(many=True, read_only=True)
    photo_files = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'customer',
            'description',
            'category',
            'budget',
            'is_negotiable',
            'deadline',
            'preferred_time',
            'phone',
            'location',
            'created_at',
            'photos',
            'photo_files',
            'subregion',
            'latitude',  
            'longitude', 
        ]
        read_only_fields = ['customer', 'created_at', 'photos']

    def create(self, validated_data):
        photo_files = self.context['request'].FILES.getlist('photo_files')
        validated_data.pop('photo_files', None)
        order = Order.objects.create(**validated_data)
        for photo_file in photo_files:
            OrderPhoto.objects.create(order=order, image=photo_file)
        return order


class Conflict(APIException):
    status_code = 409
    default_detail = 'Конфликт: операция уже выполнена.'
    default_code = 'conflict'


class OrderRespondSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context['request']
        executor = request.user
        order_id = data['order_id']

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            self._log_attempt(order=None, executor=executor, success=False, reason="Заказ не найден", data=data)
            raise serializers.ValidationError("Заказ не найден")

        if executor.is_blocked:
            self._log_attempt(order, executor, False, "Пользователь заблокирован", data)
            raise serializers.ValidationError("Ваш аккаунт заблокирован.")

        if order.deadline < timezone.now().date():
            self._log_attempt(order, executor, False, "Истёк дедлайн", data)
            raise serializers.ValidationError("Нельзя откликнуться на заказ с истекшим дедлайном.")

        if order.status != 'active':
            self._log_attempt(order, executor, False, f"Статус заказа: {order.get_status_display()}", data)
            raise serializers.ValidationError(f"Нельзя откликнуться на заказ со статусом: {order.get_status_display()}")

        if order.customer == executor:
            self._log_attempt(order, executor, False, "Попытка отклика на свой заказ", data)
            raise serializers.ValidationError("Нельзя откликнуться на свой собственный заказ.")

        if OrderResponse.objects.filter(order=order, executor=executor).exists():
            self._log_attempt(order, executor, False, "Повторный отклик", data)
            raise serializers.ValidationError("Вы уже откликнулись на этот заказ.")

        recent = OrderRespondLog.objects.filter(
            executor=executor,
            created_at__gt=timezone.now() - timezone.timedelta(seconds=5)
        )
        if recent.exists():
            raise serializers.ValidationError("Слишком частые отклики. Подождите немного.")

        MAX_RESPONSES = 5
        if order.responses.count() >= MAX_RESPONSES:
            self._log_attempt(order, executor, False, "Достигнут лимит откликов", data)
            raise serializers.ValidationError("Превышено количество откликов на этот заказ.")

        required_amount = self._calculate_fee(order)
        if executor.balance < required_amount:
            self._log_attempt(order, executor, False, "Недостаточно средств", data)
            raise serializers.ValidationError(f"Недостаточно средств. Нужно {required_amount}, у вас {executor.balance}.")

        data['order'] = order
        data['required_amount'] = required_amount
        return data

    def save(self, **kwargs):
        executor = self.context['request'].user
        order = self.validated_data['order']
        required_amount = self.validated_data['required_amount']
        message = self.validated_data.get('message', '')
        idempotency_key = self.validated_data.get('idempotency_key')

        with transaction.atomic():
            if idempotency_key:
                if OrderRespondLog.objects.select_for_update().filter(
                    idempotency_key=idempotency_key,
                    success=True
                ).exists():
                    raise Conflict("Повторный запрос с тем же ключом идемпотентности уже выполнен успешно.")

            order = Order.objects.select_for_update().get(pk=order.pk)
            executor.refresh_from_db()

            if order.responses.count() >= 5:
                self._log_attempt(order, executor, False, "Лимит откликов (конкуренция)", self.validated_data, idempotency_key)
                raise serializers.ValidationError("Лимит откликов уже достигнут")

            if executor.balance < required_amount:
                self._log_attempt(order, executor, False, "Недостаточно средств при списании", self.validated_data, idempotency_key)
                raise serializers.ValidationError("Недостаточно средств при списании")

            executor.balance -= required_amount
            executor.save()

            response = OrderResponse.objects.create(order=order, executor=executor, message=message)

            order.status = 'completed'
            order.save()

            self._log_attempt(order, executor, True, None, self.validated_data, idempotency_key)

        return {
            'order_response': response,
            'customer_phone': order.phone
        }


    def _calculate_fee(self, order):
        if order.budget and order.budget > 10000:
            return 100
        return 50

    def _log_attempt(self, order, executor, success, reason, data, idempotency_key=None):
        OrderRespondLog.objects.create(
            order=order,
            executor=executor,
            success=success,
            reason=reason,
            idempotency_key=idempotency_key or data.get('idempotency_key')
        )

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'order', 'executor', 'customer', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'executor', 'customer', 'created_at']

    def validate(self, data):
        order = data.get('order')
        if Review.objects.filter(order=order).exists():
            raise serializers.ValidationError("Отзыв на этот заказ уже существует.")
        if order.status != 'completed':
            raise serializers.ValidationError("Можно оставить отзыв только после завершения заказа.")
        return data

    def create(self, validated_data):
        request = self.context['request']
        order = validated_data['order']
        
        response = order.responses.first()
        if not response:
            raise serializers.ValidationError("На заказ не было откликов.")
        
        executor = response.executor
        return Review.objects.create(
            customer=request.user,
            executor=executor,
            order=order,
            rating=validated_data['rating'],
            comment=validated_data.get('comment', '')
        )