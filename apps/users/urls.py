from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'regions', RegionViewSet)
router.register(r'subregions', SubRegionViewSet)
router.register(r'professions', ProfessionViewSet)

urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/verify-email/', VerifyEmailView.as_view()),
    path('user/role/', SetRoleView.as_view()),
    path('user/profession/', SetProfessionView.as_view()),
    path('user/verify/', UploadDocumentsView.as_view()),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-passport/', PassportPhotoUploadView.as_view(), name='verify-passport'),
    path('user/profile/', UserProfileView.as_view(), name='user-profile'),
    path('auth/login-request/', LoginWithCodeRequestView.as_view(), name='login-request'),
    path('auth/login-verify/', LoginWithCodeVerifyView.as_view(), name='login-verify'),
    path('auth/password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('auth/password-reset-verify/', PasswordResetCodeVerifyView.as_view(), name='password-reset-verify'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('', include(router.urls)),
]