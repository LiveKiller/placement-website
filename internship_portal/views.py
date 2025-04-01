
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "message": "Welcome to the Internship Portal Dashboard",
            "user": {
                "registration_number": request.user.get('registration_number'),
                "name": f"{request.user.get('first_name')} {request.user.get('last_name')}",
                "email": request.user.get('email')
            }
        })