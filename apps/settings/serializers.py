from rest_framework import serializers
from apps.settings.models import ImageBanner

class ImageBannerSerilaizers(serializers.ModelSerializer):
    class Meta:
        model = ImageBanner
        fields = ['id', 'image']