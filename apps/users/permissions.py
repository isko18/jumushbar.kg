from rest_framework.permissions import BasePermission

class IsCustomerPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'заказчик'


class IsExecutorPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'исполнитель'