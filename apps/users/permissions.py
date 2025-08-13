from rest_framework.permissions import BasePermission

class IsCustomerPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.role or '').lower() == 'заказчик'
        )
    
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user


class IsExecutorPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.role or '').lower() == 'исполнитель'
        )
