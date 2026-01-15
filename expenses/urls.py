from django.urls import path
from .views import (
    ExpenseListCreateView, 
    ExpenseDetailView,
    approve_expense,
    reject_expense
)

app_name = 'expenses'

urlpatterns = [
    path('', ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),
    path('<int:pk>/approve/', approve_expense, name='approve_expense'),
    path('<int:pk>/reject/', reject_expense, name='reject_expense'),
]
