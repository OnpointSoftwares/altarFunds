from django.urls import path
from .views import (
    DenominationListCreateView, DenominationDetailView,
    ChurchListCreateView, ChurchDetailView, ChurchVerificationView, ChurchStatusUpdateView,
    CampusListCreateView, CampusDetailView,
    DepartmentListCreateView, DepartmentDetailView,
    SmallGroupListCreateView, SmallGroupDetailView,
    ChurchBankAccountListCreateView, ChurchBankAccountDetailView,
    MpesaAccountListCreateView, MpesaAccountDetailView,
    church_summary, church_options, department_options, small_group_options,
    ChurchRegistrationView, join_church
)
from .search_views import search_churches

app_name = 'churches'

urlpatterns = [
    path('denominations/', DenominationListCreateView.as_view(), name='denomination_list_create'),
    path('denominations/<int:pk>/', DenominationDetailView.as_view(), name='denomination_detail'),
    path('', ChurchListCreateView.as_view(), name='church_list_create'),
    path('<int:pk>/', ChurchDetailView.as_view(), name='church_detail'),
    path('<int:pk>/verify/', ChurchVerificationView.as_view(), name='church_verify'),
    path('<int:pk>/status/', ChurchStatusUpdateView.as_view(), name='church_status_update'),
    path('register/', ChurchRegistrationView.as_view(), name='register'),
    path('campuses/', CampusListCreateView.as_view(), name='campus_list_create'),
    path('campuses/<int:pk>/', CampusDetailView.as_view(), name='campus_detail'),
    path('departments/', DepartmentListCreateView.as_view(), name='department_list_create'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department_detail'),
    path('small-groups/', SmallGroupListCreateView.as_view(), name='small_group_list_create'),
    path('small-groups/<int:pk>/', SmallGroupDetailView.as_view(), name='small_group_detail'),
    path('bank-accounts/', ChurchBankAccountListCreateView.as_view(), name='bank_account_list_create'),
    path('bank-accounts/<int:pk>/', ChurchBankAccountDetailView.as_view(), name='bank_account_detail'),
    path('mpesa-accounts/', MpesaAccountListCreateView.as_view(), name='mpesa_account_list_create'),
    path('mpesa-accounts/<int:pk>/', MpesaAccountDetailView.as_view(), name='mpesa_account_detail'),
    path('<int:church_id>/summary/', church_summary, name='church_summary'),
    path('options/churches/', church_options, name='church_options'),
    path('options/departments/', department_options, name='department_options'),
    path('options/small-groups/', small_group_options, name='small_group_options'),
    path('join/', join_church, name='join_church'),
    path('search/', search_churches, name='search_churches'),
]
