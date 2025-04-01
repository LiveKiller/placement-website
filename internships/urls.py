from django.urls import path
from .views import DashboardView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # Add similar paths:
    # path('messages/', MessagesView.as_view()),
    # path('news/', NewsView.as_view()),
    # path('companies/', CompaniesView.as_view()),
    # path('portfolio/', PortfolioView.as_view()),
]
