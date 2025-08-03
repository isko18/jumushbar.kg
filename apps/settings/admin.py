from django.contrib import admin
from .models import PrivacyPolicy, PublicOffer, RefundPolicy, CardPaymentTerms

admin.site.register(PrivacyPolicy)
admin.site.register(PublicOffer)
admin.site.register(RefundPolicy)
admin.site.register(CardPaymentTerms)
