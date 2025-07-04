from rest_framework import serializers
from apps.orders.models import Category, Order, OrderPhoto


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
        child=serializers.ImageField(), write_only=True, required=False
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
            'photo_files'
        ]
        read_only_fields = ['customer', 'created_at', 'photos']

    def create(self, validated_data):
        photo_files = self.context['request'].FILES.getlist('photo_files')
        order = Order.objects.create(customer=self.context['request'].user, **validated_data)
        for photo_file in photo_files:
            OrderPhoto.objects.create(order=order, image=photo_file)
        return order
