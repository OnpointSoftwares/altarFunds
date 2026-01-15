from django.urls import path
from .views import dashboard_view
from . import api_views

app_name = 'dashboard'

urlpatterns = [
    # Template views
    path('', dashboard_view, name='home'),
    
    # API endpoints
    path('financial-summary/', api_views.financial_summary, name='financial_summary'),
    path('monthly-trend/', api_views.monthly_trend, name='monthly_trend'),
    path('income-breakdown/', api_views.income_breakdown, name='income_breakdown'),
    path('expense-breakdown/', api_views.expense_breakdown, name='expense_breakdown'),
]
