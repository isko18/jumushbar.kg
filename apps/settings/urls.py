from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('image-banner/', views.ImageBannerAPI, basename='image_banner')

urlpatterns = [
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('public-offer/', views.public_offer_view, name='public_offer'),
    path('refund-policy/', views.refund_policy_view, name='refund_policy'),
    path('card-payment/', views.card_payment_view, name='card_payment'),
]

urlpatterns += router.urls