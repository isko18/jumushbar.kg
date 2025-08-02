from django.urls import path
from . import views

urlpatterns = [
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('public-offer/', views.public_offer_view, name='public_offer'),
    path('refund-policy/', views.refund_policy_view, name='refund_policy'),
    path('card-payment/', views.card_payment_view, name='card_payment'),
]
