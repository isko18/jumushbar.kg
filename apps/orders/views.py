from rest_framework import viewsets, permissions, mixins
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
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