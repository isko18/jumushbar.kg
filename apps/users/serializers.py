from rest_framework import serializers
from .models import User, UserRegion, UserSubRegion, Profession, UserRole
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate

from django.contrib.auth import get_user_model
UserModel = get_user_model()

class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('Неверный email или пароль')

        if not user.check_password(password) or not user.is_active:
            raise AuthenticationFailed('Неверный email или пароль')

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'phone': user.phone,
            }
        }
    
class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'label']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone', 'full_name']

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRegion
        fields = ['id', 'title']

class SubRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubRegion
        fields = ['id', 'title', 'region']

class RoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[('исполнитель', 'исполнитель'), ('заказчик', 'заказчик')])

class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ['id', 'title']

class UploadDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['passport_front', 'passport_back', 'passport_selfie']
