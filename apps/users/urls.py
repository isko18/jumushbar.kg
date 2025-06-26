from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    VerifyEmailView,
    SetRoleView,
    SetProfessionView,
    UploadDocumentsView,
    CustomTokenObtainPairView,
    PassportVerificationAPIView,
    RoleViewSet,
    RegionViewSet,
    SubRegionViewSet,
    ProfessionViewSet
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'subregions', SubRegionViewSet, basename='subregion')
router.register(r'professions', ProfessionViewSet, basename='profession')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    # Регистрация и подтверждение email
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),

    # Авторизация
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Пользовательские действия
    path('user/role/', SetRoleView.as_view(), name='set-role'),
    path('user/profession/', SetProfessionView.as_view(), name='set-profession'),
    path('user/verify/', UploadDocumentsView.as_view(), name='upload-documents'),

    # Верификация паспорта
    path('verify-passport/', PassportVerificationAPIView.as_view(), name='verify-passport'),

    # Маршруты viewsets
    path('', include(router.urls)),
]
