# users/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from .serializers import UserSerializer
from db.mongo import MongoDB
import requests
import json


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        registration_number = request.data.get('registration_number')
        password = request.data.get('password')

        mongo_db = MongoDB()
        user = mongo_db.get_user_by_registration_number(registration_number)

        if user and check_password(password, user.get('password')):
            refresh = RefreshToken()
            refresh['registration_number'] = user.get('registration_number')

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'registration_number': user.get('registration_number'),
                    'email': user.get('email'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name')
                }
            })

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LinkedInAuthView(APIView):
    def get(self, request):
        code = request.GET.get('code')

        if not code:
            return Response({'error': 'Authorization code not provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Exchange authorization code for access token
        token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        token_payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': 'your-callback-url',
            'client_id': 'your-linkedin-client-id',
            'client_secret': 'your-linkedin-client-secret'
        }

        token_response = requests.post(token_url, data=token_payload)
        token_data = token_response.json()

        if 'access_token' not in token_data:
            return Response({'error': 'Failed to obtain access token'}, status=status.HTTP_400_BAD_REQUEST)

        # Get user profile data
        profile_url = 'https://api.linkedin.com/v2/me'
        headers = {
            'Authorization': f"Bearer {token_data['access_token']}",
            'Content-Type': 'application/json'
        }

        profile_response = requests.get(profile_url, headers=headers)
        profile_data = profile_response.json()

        email_url = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'
        email_response = requests.get(email_url, headers=headers)
        email_data = email_response.json()

        try:
            email = email_data['elements'][0]['handle~']['emailAddress']
            first_name = profile_data.get('localizedFirstName', '')
            last_name = profile_data.get('localizedLastName', '')

            mongo_db = MongoDB()
            existing_user = mongo_db.get_user_by_email(email)

            if existing_user:
                # User exists, generate token
                refresh = RefreshToken()
                refresh['registration_number'] = existing_user.get('registration_number')

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'registration_number': existing_user.get('registration_number'),
                        'email': existing_user.get('email'),
                        'first_name': existing_user.get('first_name'),
                        'last_name': existing_user.get('last_name')
                    }
                })
            else:
                # Create new user
                # Note: For LinkedIn logins, you might want to handle registration number generation differently
                return Response({
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'message': 'User not registered. Please complete registration.'
                }, status=status.HTTP_200_OK)

        except (KeyError, IndexError):
            return Response({'error': 'Failed to fetch user data from LinkedIn'}, status=status.HTTP_400_BAD_REQUEST)


class ImportUsersView(APIView):
    def post(self, request):
        file_path = request.data.get('file_path')

        if not file_path:
            return Response({'error': 'CSV file path not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mongo_db = MongoDB()
            mongo_db.import_users_from_csv(file_path)
            return Response({'message': 'Users imported successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        mongo_db = MongoDB()
        user = mongo_db.get_user_by_email(email)

        if not user:
            return Response({'error': 'No user found with this email'}, status=status.HTTP_404_NOT_FOUND)

        # Generate a token for password reset
        # In a real application, you would send an email with a link containing this token
        # For simplicity, we're just returning the token
        refresh = RefreshToken()
        refresh['registration_number'] = user.get('registration_number')
        reset_token = str(refresh)

        return Response({'message': 'Password reset email sent', 'token': reset_token}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate token and get user information
            # This is a simplified version, in a real application you would need to properly validate the token
            token_info = RefreshToken(token)
            registration_number = token_info['registration_number']

            mongo_db = MongoDB()
            user = mongo_db.get_user_by_registration_number(registration_number)

            if not user:
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

            # Update password
            hashed_password = make_password(new_password)
            mongo_db.update_user(user.get('_id'), {'password': hashed_password})

            return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)