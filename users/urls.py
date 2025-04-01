# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, LinkedInAuthView, ImportUsersView, RequestPasswordResetView, \
    ResetPasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('linkedin/callback/', LinkedInAuthView.as_view(), name='linkedin_callback'),
    path('import-users/', ImportUsersView.as_view(), name='import_users'),
    path('password-reset/request/', RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('password-reset/confirm/', ResetPasswordView.as_view(), name='reset_password'),
]