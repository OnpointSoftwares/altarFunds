from django.urls import path
from .views import (
    dashboard_view,
    financial_summary,
    monthly_trend,
    income_breakdown,
    expense_breakdown
)
from .comprehensive_views import comprehensive_dashboard

app_name = 'dashboard'

urlpatterns = [
    # Template views
    path('', dashboard_view, name='home'),
    
    # API endpoints
    path('financial-summary/', financial_summary, name='financial_summary'),
    path('monthly-trend/', monthly_trend, name='monthly_trend'),
    path('income-breakdown/', income_breakdown, name='income_breakdown'),
    path('expense-breakdown/', expense_breakdown, name='expense_breakdown'),
    path('comprehensive/', comprehensive_dashboard, name='comprehensive_dashboard'),
]
