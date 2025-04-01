from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from internship_portal.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', RedirectView.as_view(url='dashboard/', permanent=False), name='index'),
    path('api/', include('internships.urls')),
    path('oauth/', include('social_django.urls', namespace='social')),
]