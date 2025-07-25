from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Роутер для справочников
router = DefaultRouter()
router.register(r'regions', RegionViewSet)
router.register(r'subregions', SubRegionViewSet)
router.register(r'professions', ProfessionViewSet)

# Пути к представлениям
urlpatterns = [
    path('auth/register/', RegisterView.as_view()),                      # Регистрация
    path('auth/verify-email/', VerifyEmailView.as_view()),              # Подтверждение email
    path('user/role/', SetRoleView.as_view()),                          # Установка роли
    path('user/profession/', SetProfessionView.as_view()),              # Установка профессии
    path('user/verify/', UploadDocumentsView.as_view()),                # Загрузка документов
    path('api/auth/token/', TokenObtainPairWithRoleView.as_view(), name='token_obtain_pair'),
    # path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Получение JWT токенов
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Обновление токенов
    path('verify-passport/', PassportPhotoUploadView.as_view(), name='verify-passport'),# Проверка паспорта AI
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),              # Профиль пользователя
    path('auth/login-request/', LoginWithCodeRequestView.as_view(), name='login-request'),  # Запрос входа по коду
    path('auth/login-verify/', LoginWithCodeVerifyView.as_view(), name='login-verify'),     # Подтверждение кода входа
    path('auth/password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),  # Сброс пароля шаг 1
    path('auth/password-reset-verify/', PasswordResetCodeVerifyView.as_view(), name='password-reset-verify'), # Сброс пароля шаг 2
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'), # Сброс пароля шаг 3
    path('auth/resend-verification-code/', ResendEmailVerificationCodeView.as_view(), name='resend-verification-code'),
    path('', include(router.urls)),  # Роуты справочников (регионов, подрегионов, профессий)
]
