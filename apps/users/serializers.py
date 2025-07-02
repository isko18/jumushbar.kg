from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, UserRegion, UserSubRegion, Profession
from core.passport_classifier.utils import predict_passport_photo
import tempfile

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Этот email уже зарегистрирован."
            )
        ]
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone', 'full_name']

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            phone=validated_data.get('phone'),
            full_name=validated_data.get('full_name')
        )

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
    role = serializers.CharField()

    def validate_role(self, value):
        value_clean = value.strip().capitalize()
        valid_roles = [r[0] for r in User.ROLE]
        if value_clean not in valid_roles:
            raise serializers.ValidationError(f"Неверная роль. Доступны: {valid_roles}")
        return value_clean

class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ['id', 'title']

class UploadDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['passport_front', 'passport_back', 'passport_selfie']

class PassportPhotoUploadSerializer(serializers.Serializer):
    passport_selfie = serializers.ImageField(required=True)
    passport_front = serializers.ImageField(required=True)
    passport_back = serializers.ImageField(required=True)

    def validate(self, data):
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_selfie, \
             tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_front, \
             tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_back:

            for chunk in data['passport_selfie'].chunks():
                tmp_selfie.write(chunk)
            tmp_selfie.flush()

            for chunk in data['passport_front'].chunks():
                tmp_front.write(chunk)
            tmp_front.flush()

            for chunk in data['passport_back'].chunks():
                tmp_back.write(chunk)
            tmp_back.flush()
            face_ok = predict_passport_photo(tmp_selfie.name, expected_type='face')
            front_ok = predict_passport_photo(tmp_front.name, expected_type='front')
            back_ok = predict_passport_photo(tmp_back.name, expected_type='back')

            if not (face_ok and front_ok and back_ok):
                raise serializers.ValidationError("Одно или несколько фото не прошли проверку AI.")

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.passport_selfie.save(self.validated_data['passport_selfie'].name, self.validated_data['passport_selfie'])
        user.passport_front.save(self.validated_data['passport_front'].name, self.validated_data['passport_front'])
        user.passport_back.save(self.validated_data['passport_back'].name, self.validated_data['passport_back'])
        user.is_verified = True
        user.save()
        return user
        
class UserProfileSerializer(serializers.ModelSerializer):
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=UserRegion.objects.all(),
        source='subregion.region',
        write_only=True,
        required=False
    )
    profession_id = serializers.PrimaryKeyRelatedField(
        queryset=Profession.objects.all(),
        source='profession',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'full_name',
            'phone',
            'region_id',
            'profession_id',
            'currency'
        ]
        read_only_fields = ['username', 'email', 'phone']

    def update(self, instance, validated_data):
        if 'full_name' in validated_data:
            instance.full_name = validated_data['full_name']
        if 'profession' in validated_data:
            instance.profession = validated_data['profession']
        if 'subregion' in validated_data:
            instance.subregion = validated_data['subregion']
        if 'currency' in validated_data:
            instance.currency = validated_data['currency']
        instance.save()
        return instance