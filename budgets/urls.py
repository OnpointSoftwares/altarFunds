from django.urls import path
from .views import BudgetListCreateView, BudgetDetailView

app_name = 'budgets'

urlpatterns = [
    path('', BudgetListCreateView.as_view(), name='budget-list-create'),
    path('<int:pk>/', BudgetDetailView.as_view(), name='budget-detail'),
]
