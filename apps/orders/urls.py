from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderListAPI

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'list-order', OrderListAPI, basename='list-order')

urlpatterns = router.urls
