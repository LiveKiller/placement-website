# db/mongo.py
from pymongo import MongoClient
import os
from bson import ObjectId
from datetime import datetime


class MongoDB:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['internship_portal']

    def get_users_collection(self):
        return self.db['users']

    def create_user(self, user_data):
        user_data['created_at'] = datetime.now()
        users = self.get_users_collection()
        result = users.insert_one(user_data)
        return str(result.inserted_id)

    def get_user_by_registration_number(self, registration_number):
        users = self.get_users_collection()
        user = users.find_one({'registration_number': registration_number})
        return user

    def get_user_by_email(self, email):
        users = self.get_users_collection()
        user = users.find_one({'email': email})
        return user

    def get_user_by_id(self, user_id):
        users = self.get_users_collection()
        user = users.find_one({'_id': ObjectId(user_id)})
        return user

    def update_user(self, user_id, update_data):
        users = self.get_users_collection()
        users.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})

    def import_users_from_csv(self, csv_file_path):
        import csv
        users = self.get_users_collection()

        with open(csv_file_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Check if user already exists
                existing_user = self.get_user_by_registration_number(row['registration_number'])
                if not existing_user:
                    user_data = {
                        'registration_number': row['registration_number'],
                        'email': row['email'],
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'password': 'default_password',
                        'is_active': True,
                        'is_staff': False,
                        'date_joined': datetime.now()
                    }
                    self.create_user(user_data)