from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.orders.models import Order, Category, Review
from apps.orders.serializers import OrderSerializer, OrderRespondSerializer, CategorySerializer, ReviewSerializer
from apps.users.permissions import IsCustomerPermission, IsExecutorPermission
from django_filters.rest_framework import DjangoFilterBackend
from apps.orders.filters import OrderFilter
from django.utils import timezone
from datetime import timedelta
import django_filters
from django.db.models import Count

class CategoriesListAPI(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Category.objects.annotate(order_count=Count('order'))
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomerPermission]

    def get_queryset(self):
        return self.queryset.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @action(detail=False, methods=['get'], url_path='my/active')
    def my_active_orders(self, request):
        orders = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my/completed')
    def my_completed_orders(self, request):
        orders = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_order(self, request, pk=None):
        order = self.get_object()

        if order.customer != request.user:
            return Response({'detail': 'Вы не являетесь владельцем этого заказа.'}, status=status.HTTP_403_FORBIDDEN)

        if order.status != 'active':
            return Response({'detail': 'Только активный заказ можно завершить.'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'completed'
        order.save()

        return Response({'detail': 'Заказ успешно завершён.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='return-to-active')
    def return_to_active(self, request, pk=None):
        order = self.get_object()

        if order.customer != request.user:
            return Response({'detail': 'Вы не владелец этого заказа.'}, status=status.HTTP_403_FORBIDDEN)

        if order.status != 'completed':
            return Response({'detail': 'Только завершённый заказ можно вернуть в активный.'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'active'
        order.save()
        return Response({'detail': 'Заказ снова активен.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_order(self, request, pk=None):
        order = self.get_object()

        if order.customer != request.user:
            return Response({'detail': 'Вы не являетесь владельцем этого заказа.'}, status=status.HTTP_403_FORBIDDEN)

        if order.status in ['completed', 'cancelled']:
            return Response({'detail': 'Этот заказ уже завершён или отменён.'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = 'cancelled'
        order.save()

        return Response({'detail': 'Заказ успешно отменён.'}, status=status.HTTP_200_OK)

class OrderListAPI(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

class OrderRespondViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsExecutorPermission]

    @action(detail=False, methods=['post'])
    def respond(self, request):
        serializer = OrderRespondSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({
            'message': 'Отклик успешен',
            'customer_phone': result['customer_phone']
        }, status=status.HTTP_200_OK)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomerPermission]

    def get_queryset(self):
        return self.queryset.filter(customer=self.request.user)

class BalanceUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = BalanceUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Баланс обновлён", "balance": user.balance}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
