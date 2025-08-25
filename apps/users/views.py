from rest_framework import generics, mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from random import randint
from .models import User, UserRegion, UserSubRegion, Profession, LegalDocument, BalanceHistory
from .serializers import *
from core.passport_classifier.tasks import validate_passport_images_task
from apps.users.permissions import IsExecutorPermission
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from random import randint
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from decimal import Decimal, InvalidOperation

class TokenObtainPairWithRoleView(TokenObtainPairView):
    serializer_class = TokenWithRoleSerializer


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

class ResendEmailVerificationCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendEmailVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        code = f"{randint(1000, 9999)}"
        user.email_verification_code = code
        user.save()

        send_mail(
            subject="Код подтверждения Email",
            message=f"Ваш новый код подтверждения: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        return Response({"message": "Код подтверждения отправлен повторно."})


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
        profession_ids = request.data.get("profession_ids")

        if not isinstance(profession_ids, list):
            return Response({"error": "profession_ids должен быть списком"}, status=400)

        professions = Profession.objects.filter(id__in=profession_ids)

        if not professions.exists():
            return Response({"error": "Профессии не найдены"}, status=404)

        request.user.professions.set(professions)
        request.user.save()

        return Response({"message": "Профессии успешно обновлены"})


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
            return Response(
                {"detail": "Фото загружены. Идёт проверка. Вы получите уведомление после завершения."},
                status=status.HTTP_202_ACCEPTED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

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

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Код сброса отправлен на почту"})

class PasswordResetCodeVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetCodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "Код подтвержден"})

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Пароль успешно сброшен"})

class LegalDocumentsView(APIView):
    def get(self, request):
        docs = LegalDocument.objects.all()
        serializer = LegalDocumentSerializer(docs, many=True)
        return Response({doc['doc_type']: doc['content'] for doc in serializer.data})
class AddBalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        amount = request.data.get("amount")

        if not amount:
            return Response({"error": "Сумма обязательна"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount))  # 👈 конвертируем в Decimal
        except (InvalidOperation, ValueError):
            return Response({"error": "Сумма должна быть числом"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Сумма должна быть больше 0"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.balance += amount   # 👈 теперь Decimal + Decimal
        user.save()

        BalanceHistory.objects.create(
            user=user,
            amount=amount,
            transaction_type="deposit",
            comment="Пополнение через API"
        )

        return Response({
            "message": "Баланс успешно пополнен",
            "balance": str(user.balance)  # 👈 сериализуем Decimal в строку
        }, status=status.HTTP_200_OK)

class BalanceHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        history = BalanceHistory.objects.filter(user=request.user)
        data = [
            {
                "amount": h.amount,
                "type": h.get_transaction_type_display(),
                "date": h.created_at.strftime("%Y-%m-%d %H:%M"),
                "comment": h.comment,
            }
            for h in history
        ]
        return Response(data, status=status.HTTP_200_OK)
