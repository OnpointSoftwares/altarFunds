from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """Renders the main dashboard page."""
    return render(request, 'dashboard/index.html')
