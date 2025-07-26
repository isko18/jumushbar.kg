from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, UserRegion, UserSubRegion, Profession
from core.passport_classifier.utils import predict_passport_photo
import tempfile, random
from django.core.mail import send_mail
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
from core.passport_classifier.tasks import validate_passport_images_task
import tempfile

class TokenWithRoleSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role  
        return data

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

class ResendEmailVerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email не найден.")
        return value

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
        errors = {}

        def write_temp(image_field, suffix):
            tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            for chunk in image_field.chunks():
                tmp.write(chunk)
            tmp.flush()
            return tmp.name

        # Путь для валидации сразу
        self.temp_selfie_path = write_temp(data['passport_selfie'], '.jpg')
        self.temp_front_path = write_temp(data['passport_front'], '.jpg')
        self.temp_back_path = write_temp(data['passport_back'], '.jpg')

        face_ok, face_msg = predict_passport_photo(self.temp_selfie_path, expected_type='face', return_reason=True)
        front_ok, front_msg = predict_passport_photo(self.temp_front_path, expected_type='front', return_reason=True)
        back_ok, back_msg = predict_passport_photo(self.temp_back_path, expected_type='back', return_reason=True)

        if not face_ok:
            errors['passport_selfie'] = face_msg
        if not front_ok:
            errors['passport_front'] = front_msg
        if not back_ok:
            errors['passport_back'] = back_msg

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def save(self, **kwargs):
        user = self.context['request'].user

        # Сохраняем изображения
        user.passport_selfie.save(self.validated_data['passport_selfie'].name, self.validated_data['passport_selfie'])
        user.passport_front.save(self.validated_data['passport_front'].name, self.validated_data['passport_front'])
        user.passport_back.save(self.validated_data['passport_back'].name, self.validated_data['passport_back'])
        user.save()

        # 🟢 ВАЖНО: вызываем задачу Celery!
        from core.passport_classifier.tasks import validate_passport_images_task
        validate_passport_images_task.delay(
            user.id,
            self.temp_selfie_path,
            self.temp_front_path,
            self.temp_back_path
        )
        return user
        
class UserProfileSerializer(serializers.ModelSerializer):
    region_id = serializers.PrimaryKeyRelatedField(
        queryset=UserRegion.objects.all(),
        source='subregion.region',
        required=False
    )
    region = serializers.CharField(source='subregion.region.name', read_only=True)

    # Профессии
    professions = ProfessionSerializer(many=True, read_only=True)
    profession_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Profession.objects.all(),
        source='professions',
        write_only=True,
        required=False
    )

    # Подрегион
    subregion_id = serializers.PrimaryKeyRelatedField(
        queryset=UserSubRegion.objects.all(),
        source='subregion',
        required=False
    )
    subregion = serializers.CharField(source='subregion.name', read_only=True)

    # Доп поля
    is_passport_verified = serializers.SerializerMethodField()
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'full_name',
            'phone',
            'region_id',
            'region',
            'subregion_id',
            'subregion',
            'profession_ids',
            'professions',
            'currency',
            'balance',
            'average_rating',
            'is_passport_verified',
        ]
        read_only_fields = ['username', 'email', 'phone']

    def update(self, instance, validated_data):
        if 'full_name' in validated_data:
            instance.full_name = validated_data['full_name']
        if 'professions' in validated_data:
            instance.professions.set(validated_data['professions'])
        if 'subregion' in validated_data:
            instance.subregion = validated_data['subregion']
        if 'currency' in validated_data:
            instance.currency = validated_data['currency']
        instance.save()
        return instance

    def get_is_passport_verified(self, obj):
        if (obj.role or '').lower() != 'исполнитель':
            return False
        return all([
            obj.passport_selfie,
            obj.passport_front,
            obj.passport_back,
            obj.is_verified
        ])

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Аккаунт с таким email не существует")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        code = f"{random.randint(1000, 9999)}"
        user.email_verification_code = code
        user.save()

        send_mail(
            subject="Сброс пароля",
            message=f"Ваш код для сброса пароля: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        return user

class PasswordResetCodeVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Пользователь не найден"})

        if user.email_verification_code != data['code']:
            raise serializers.ValidationError({"code": "Код неправильный"})
        return data

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    new_password_repeat = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_repeat']:
            raise serializers.ValidationError({"new_password_repeat": "Пароли не совпадают"})
        return data

    def save(self):
        email = self.validated_data['email']
        new_password = self.validated_data['new_password']
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.email_verification_code = None
        user.save()
        return user
