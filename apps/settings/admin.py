from django.contrib import admin
from .models import PrivacyPolicy, PublicOffer, RefundPolicy, CardPaymentTerms, ImageBanner

admin.site.register(PrivacyPolicy)
admin.site.register(PublicOffer)
admin.site.register(RefundPolicy)
admin.site.register(CardPaymentTerms)
admin.site.register(ImageBanner)