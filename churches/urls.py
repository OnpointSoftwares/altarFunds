from django.urls import path
from . import views

app_name = 'churches'

urlpatterns = [
    # Denominations
    path('denominations/', views.DenominationListCreateView.as_view(), name='denomination-list'),
    path('denominations/<int:pk>/', views.DenominationDetailView.as_view(), name='denomination-detail'),
    
    # Churches
    path('', views.ChurchListCreateView.as_view(), name='church-list'),
    path('<int:pk>/', views.ChurchDetailView.as_view(), name='church-detail'),
    path('<int:pk>/verify/', views.ChurchVerificationView.as_view(), name='church-verify'),
    path('<int:pk>/status/', views.ChurchStatusUpdateView.as_view(), name='church-status-update'),
    path('<int:church_id>/summary/', views.church_summary, name='church-summary'),
    path('options/', views.church_options, name='church-options'),
    
    # Campuses
    path('campuses/', views.CampusListCreateView.as_view(), name='campus-list'),
    path('campuses/<int:pk>/', views.CampusDetailView.as_view(), name='campus-detail'),
    
    # Departments
    path('departments/', views.DepartmentListCreateView.as_view(), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),
    path('departments/options/', views.department_options, name='department-options'),
    
    # Small Groups
    path('small-groups/', views.SmallGroupListCreateView.as_view(), name='small-group-list'),
    path('small-groups/<int:pk>/', views.SmallGroupDetailView.as_view(), name='small-group-detail'),
    path('small-groups/options/', views.small_group_options, name='small-group-options'),
    
    # Bank Accounts
    path('bank-accounts/', views.ChurchBankAccountListCreateView.as_view(), name='bank-account-list'),
    path('bank-accounts/<int:pk>/', views.ChurchBankAccountDetailView.as_view(), name='bank-account-detail'),
    
    # M-Pesa Accounts
    path('mpesa-accounts/', views.MpesaAccountListCreateView.as_view(), name='mpesa-account-list'),
    path('mpesa-accounts/<int:pk>/', views.MpesaAccountDetailView.as_view(), name='mpesa-account-detail'),
]
