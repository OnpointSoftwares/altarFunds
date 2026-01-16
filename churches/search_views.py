from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from churches.models import Church


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_churches(request):
    """Search for churches by name or code."""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({
            'error': 'Search query must be at least 2 characters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Search churches by name or code
        churches = Church.objects.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        ).filter(is_active=True)[:10]  # Limit to 10 results
        
        results = []
        for church in churches:
            results.append({
                'id': church.id,
                'name': church.name,
                'code': church.code,
                'is_verified': church.is_verified,
                'city': church.city,
                'county': church.county
            })
        
        return Response({
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Search failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
