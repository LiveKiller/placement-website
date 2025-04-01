# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from db.mongo import MongoDB


class UserSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    registration_number = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, required=False)

    def create(self, validated_data):
        mongo_db = MongoDB()
        # Hash the password
        validated_data['password'] = make_password(validated_data.get('password'))
        user_id = mongo_db.create_user(validated_data)
        return {**validated_data, 'id': user_id}

    def validate_registration_number(self, value):
        mongo_db = MongoDB()
        existing_user = mongo_db.get_user_by_registration_number(value)
        if existing_user and not self.instance:
            raise serializers.ValidationError("A user with that registration number already exists.")
        return value

    def validate_email(self, value):
        mongo_db = MongoDB()
        existing_user = mongo_db.get_user_by_email(value)
        if existing_user and not self.instance:
            raise serializers.ValidationError("A user with that email already exists.")
        return value