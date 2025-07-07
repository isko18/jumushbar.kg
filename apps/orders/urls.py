from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderListAPI, OrderRespondViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'list-order', OrderListAPI, basename='list-order')
router.register(r'order-respond', OrderRespondViewSet, basename='order-respond')

urlpatterns = router.urls