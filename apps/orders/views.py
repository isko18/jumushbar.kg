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

class CategoriesListAPI(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Category.objects.all()
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsCustomerPermission])
    def complete(self, request, pk=None):
        order = self.get_object()
        if order.status != 'active':
            return Response({"detail": "Заказ уже завершён или отменён."}, status=400)
        
        order.status = 'completed'
        order.save()
        return Response({"detail": "Заказ успешно завершён."}, status=200)


class OrderListAPI(mixins.ListModelMixin,viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().filter(status='active')
        now = timezone.now()

        filter_type = self.request.query_params.get('filter')
        include_all = self.request.query_params.get('include_all') == 'true'
        category_param = self.request.query_params.get('category')
        subregion_param = self.request.query_params.get('subregion')
        is_negotiable = django_filters.BooleanFilter(field_name='is_negotiable')

        if filter_type == 'new':
            queryset = queryset.filter(created_at__gte=now - timedelta(hours=24))

        elif not include_all and user.role == "Исполнитель":
            if user.profession and not category_param:
                queryset = queryset.filter(category__profession=user.profession)
            if user.subregion and not subregion_param:
                queryset = queryset.filter(subregion=user.subregion)

        return queryset.order_by('-created_at') 

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