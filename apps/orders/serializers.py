from rest_framework import serializers
from apps.orders.models import Category, Order, OrderPhoto, OrderResponse
from apps.users.models import User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title']


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
        ]
        read_only_fields = ['customer', 'created_at', 'photos']

    def create(self, validated_data):
        photo_files = self.context['request'].FILES.getlist('photo_files')
        validated_data.pop('photo_files', None)
        order = Order.objects.create(**validated_data)
        # Сохраняем фото
        for photo_file in photo_files:
            OrderPhoto.objects.create(order=order, image=photo_file)
        return order


class OrderRespondSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(pk=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Заказ не найден")
        return value

    def validate(self, data):
        request = self.context['request']
        executor = request.user
        order_id = data['order_id']

        # Проверка верификации
        if not executor.is_verified:
            raise serializers.ValidationError("Для отклика нужно пройти верификацию.")

        # Проверка, что уже откликался
        if OrderResponse.objects.filter(order_id=order_id, executor=executor).exists():
            raise serializers.ValidationError("Вы уже откликнулись на этот заказ.")

        # Проверка баланса
        required_amount = 50
        if executor.balance < required_amount:
            raise serializers.ValidationError(f"Недостаточно средств. Нужно {required_amount}, у вас {executor.balance}.")

        return data

    def save(self, **kwargs):
        executor = self.context['request'].user
        order = Order.objects.get(pk=self.validated_data['order_id'])
        required_amount = 50

        # Списание
        executor.balance -= required_amount
        executor.save()

        # Создание отклика
        response = OrderResponse.objects.create(order=order, executor=executor)

        return {
            'order_response': response,
            'customer_phone': order.phone
        }