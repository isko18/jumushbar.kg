from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from random import randint
from .models import User, UserRegion, UserSubRegion, Profession, UserRole
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    VerifyEmailSerializer,
    UserRoleSerializer,
    RegionSerializer,
    SubRegionSerializer,
    ProfessionSerializer,
    RoleSerializer,
    UploadDocumentsSerializer
)
from core.passport_classifier.tasks import validate_passport_images_task
from apps.users.permissions import IsExecutorPermission
from rest_framework.views import APIView
from rest_framework import status


# Авторизация через кастомный сериализатор
class CustomTokenObtainPairView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


# Регистрация
class RegisterView(mixins.CreateModelMixin, generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        code = f"{randint(1000, 9999)}"
        user.email_verification_code = code
        user.save()

        send_mail(
            subject='Подтверждение Email',
            message=f'Ваш код подтверждения: {code}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


# Подтверждение email
class VerifyEmailView(generics.GenericAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=404)

        if user.email_verification_code != code:
            return Response({'error': 'Неверный код подтверждения'}, status=400)

        user.is_verified = True
        user.email_verification_code = None
        user.save()
        return Response({"message": "Email подтвержден"})


# CRUD и справочники
class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [AllowAny]


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserRegion.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]


class SubRegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserSubRegion.objects.all()
    serializer_class = SubRegionSerializer
    permission_classes = [AllowAny]


class ProfessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Profession.objects.all()
    serializer_class = ProfessionSerializer
    permission_classes = [AllowAny]


# Обновление роли пользователя
class SetRoleView(generics.UpdateAPIView):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.role = serializer.validated_data['role']
        request.user.save()
        return Response({"message": "Роль обновлена"})


# Обновление профессии пользователя
class SetProfessionView(generics.UpdateAPIView):
    serializer_class = ProfessionSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        profession_id = request.data.get("profession_id")
        try:
            profession = Profession.objects.get(id=profession_id)
            request.user.profession = profession
            request.user.save()
            return Response({"message": "Профессия обновлена"})
        except Profession.DoesNotExist:
            return Response({"error": "Профессия не найдена"}, status=404)


# Загрузка документов
class UploadDocumentsView(generics.UpdateAPIView):
    serializer_class = UploadDocumentsSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Документы загружены"})


# Проверка паспорта через Celery
class PassportVerificationAPIView(APIView):
    permission_classes = [IsExecutorPermission]

    def post(self, request):
        serializer = UploadDocumentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.passport_front = serializer.validated_data['passport_front']
        user.passport_back = serializer.validated_data['passport_back']
        user.passport_selfie = serializer.validated_data['passport_selfie']
        user.save()

        validate_passport_images_task.delay(
            user.id,
            user.passport_selfie.path,
            user.passport_front.path,
            user.passport_back.path
        )

        return Response(
            {"detail": "Проверка запущена. Результат появится после обработки."},
            status=status.HTTP_202_ACCEPTED
        )
