from rest_framework import viewsets, permissions
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from apps.users.permissions import IsCustomerPermission

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomerPermission]

    def get_queryset(self):
        return self.queryset.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)