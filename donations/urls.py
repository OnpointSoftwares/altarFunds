from django.urls import path
from .views import DonationListCreateView

app_name = 'donations'

urlpatterns = [
    path('', DonationListCreateView.as_view(), name='donation-list-create'),
]
