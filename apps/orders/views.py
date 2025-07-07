from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer, OrderRespondSerializer
from apps.users.permissions import IsCustomerPermission, IsExecutorPermission
from django_filters.rest_framework import DjangoFilterBackend
from apps.orders.filters import OrderFilter

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomerPermission]

    def get_queryset(self):
        return self.queryset.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class OrderListAPI(mixins.ListModelMixin,viewsets.GenericViewSet):
    queryset = Order.objects.all()
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