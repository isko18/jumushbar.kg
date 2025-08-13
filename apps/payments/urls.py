from django.urls import path
from .views import FreedomPayCallbackView

urlpatterns = [
    path('callback/', FreedomPayCallbackView.as_view(), name='freedompay-callback'),
]
