from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderListAPI, OrderRespondViewSet, CategoriesListAPI, ReviewViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'list-order', OrderListAPI, basename='list-order')
router.register(r'order-respond', OrderRespondViewSet, basename='order-respond')
router.register(r'categories-list', CategoriesListAPI, basename='list-categories')
router.register(r'reviews', ReviewViewSet, basename='reviews')

urlpatterns = router.urls