# users/auth.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from db.mongo import MongoDB


class MongoDBBackend(BaseBackend):
    def authenticate(self, request, registration_number=None, password=None):
        mongo_db = MongoDB()
        user = mongo_db.get_user_by_registration_number(registration_number)

        if user and check_password(password, user.get('password')):
            return user
        return None

    def get_user(self, user_id):
        mongo_db = MongoDB()
        return mongo_db.get_user_by_id(user_id)