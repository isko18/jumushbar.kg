from django.shortcuts import render, get_object_or_404
from .models import PrivacyPolicy, PublicOffer, RefundPolicy, CardPaymentTerms, ImageBanner
from apps.settings.serializers import ImageBannerSerilaizers

from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin

def privacy_policy_view(request):
    doc = get_object_or_404(PrivacyPolicy)
    return render(request, 'legal/privacy_policy.html', {'doc': doc})

def public_offer_view(request):
    doc = get_object_or_404(PublicOffer)
    return render(request, 'legal/public_offer.html', {'doc': doc})

def refund_policy_view(request):
    doc = get_object_or_404(RefundPolicy)
    return render(request, 'legal/refund_policy.html', {'doc': doc})

def card_payment_view(request):
    doc = get_object_or_404(CardPaymentTerms)
    return render(request, 'legal/card_payment.html', {'doc': doc})

class ImageBannerAPI(GenericViewSet, ListModelMixin):
    queryset = ImageBanner.objects.all()
    serializer_class = ImageBannerSerilaizers
    permission_classes = [AllowAny]