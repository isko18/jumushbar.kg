from rest_framework import serializers
from apps.orders.models import Category, Order, OrderPhoto, OrderResponse, OrderRespondLog, Review
from apps.users.models import User
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import APIException
from apps.users.models import BalanceHistory


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

        order = Order.objects.filter(pk=order_id).first()
        if not order:
            self._log_attempt(None, executor, False, "Заказ не найден", data)
            raise serializers.ValidationError("Заказ не найден.")

        errors = []
        if executor.is_blocked:
            errors.append("Ваш аккаунт заблокирован.")
        if order.deadline < timezone.now().date():
            errors.append("Нельзя откликнуться на заказ с истекшим дедлайном.")
        if order.status != 'active':
            errors.append(f"Нельзя откликнуться на заказ со статусом: {order.get_status_display()}")
        if order.customer == executor:
            errors.append("Нельзя откликнуться на свой собственный заказ.")
        if OrderResponse.objects.filter(order=order, executor=executor).exists():
            errors.append("Вы уже откликнулись на этот заказ.")
        if OrderRespondLog.objects.filter(
            executor=executor,
            created_at__gt=timezone.now() - timezone.timedelta(seconds=5)
        ).exists():
            errors.append("Слишком частые отклики. Подождите немного.")
        if order.responses.count() >= 5:
            errors.append("Превышено количество откликов на этот заказ.")

        required_amount = self._calculate_fee(order)
        if executor.balance < required_amount:
            errors.append(f"Недостаточно средств. Нужно {required_amount}, у вас {executor.balance}.")

        if errors:
            self._log_attempt(order, executor, False, errors[0], data)
            raise serializers.ValidationError(errors[0])

        data['order'] = order
        data['required_amount'] = required_amount
        return data

    def save(self, **kwargs):
        executor = self.context['request'].user
        order = self.validated_data['order']
        required_amount = self.validated_data['required_amount']
        message = self.validated_data.get('message', '')

        # Списываем деньги у исполнителя
        executor.balance -= required_amount
        executor.save(update_fields=['balance'])

        # 📌 Записываем историю списания
        BalanceHistory.objects.create(
            user=executor,
            amount=required_amount,
            transaction_type="withdraw",
            comment=f"Списание за отклик на заказ #{order.pk}"
        )

        # Создаём отклик
        response = OrderResponse.objects.create(
            order=order,
            executor=executor,
            message=message
        )

        # Логируем успешный отклик
        self._log_attempt(order, executor, True, "Отклик успешно создан", self.validated_data)

        return {
            'status': 'success',
            'order_id': order.pk,
            'response_id': response.pk,
            'new_balance': executor.balance
        }


    def _calculate_fee(self, order):
        return 100 if order.budget and order.budget > 10000 else 50

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

class BalanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['balance']

    def validate_balance(self, value):
        if value < 0:
            raise serializers.ValidationError("Баланс не может быть отрицательным.")
        return value
