from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "user": {
                "username": request.user.username,
                "email": request.user.email,
                "name": request.user.name
            },
            "stats": {
                "applications": 0,
                "messages": 0
            }
        })