# user/views.py
from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from random import randint
from .models import User, UserRegion, UserSubRegion, Profession
from .serializers import *
from core.passport_classifier.tasks import validate_passport_images_task
from apps.users.permissions import IsExecutorPermission
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from random import randint


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

class SetRoleView(generics.UpdateAPIView):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.role = serializer.validated_data['role']
        request.user.save()
        return Response({"message": "Роль обновлена"})

class SetProfessionView(generics.UpdateAPIView):
    serializer_class = ProfessionSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        profession_id = request.data.get("profession_id")
        try:
            profession = Profession.objects.get(id=profession_id)
            request.user.profession = profession
            request.user.save()
            return Response({"message": "Profession updated"})
        except Profession.DoesNotExist:
            return Response({"error": "Profession not found"}, status=404)

class UploadDocumentsView(generics.UpdateAPIView):
    serializer_class = UploadDocumentsSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Documents uploaded"})

class PassportPhotoUploadView(APIView):
    permission_classes = [IsAuthenticated, IsExecutorPermission]

    def post(self, request, *args, **kwargs):
        serializer = PassportPhotoUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Паспортные фото успешно проверены и сохранены."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsExecutorPermission]

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response({"message": "Аккаунт удалён"})



class LoginWithCodeRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email и пароль обязательны."}, status=400)

        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response({"error": "Неверные учетные данные."}, status=400)

        if not user.is_active:
            return Response({"error": "Аккаунт не активен."}, status=400)

        # генерируем код
        code = f"{randint(1000, 9999)}"
        user.email_verification_code = code
        user.save()

        # отправляем код
        send_mail(
            subject="Код подтверждения входа",
            message=f"Ваш код для входа: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

        return Response({"message": "Код отправлен на почту."}, status=200)


class LoginWithCodeVerifyView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        if not email or not code:
            return Response({"error": "Email и код обязательны."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)

        if user.email_verification_code != code:
            return Response({"error": "Неверный код."}, status=400)

        # Сброс кода
        user.email_verification_code = None
        user.save()

        # Выдача токена
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=200)