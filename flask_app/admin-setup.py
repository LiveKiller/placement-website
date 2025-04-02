# admin_setup.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

load_dotenv()

MONGO_URI = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_CLUSTER')}/{os.getenv('MONGO_DB_NAME')}?retryWrites=true&w=majority"

try:
    client = MongoClient(MONGO_URI)
    db = client[os.getenv('MONGO_DB_NAME')]

    # Create admin user
    reg_number = input("Enter admin registration number: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")

    # Check if user already exists
    if db.users.find_one({"registration_number": reg_number}):
        print(f"User with registration number {reg_number} already exists.")
    else:
        # Create user
        db.users.insert_one({
            "registration_number": reg_number,
            "email": email,
            "password": generate_password_hash(password, method='pbkdf2:sha256'),
            "department": "Administration",
            "course": "N/A",
            "created_at": datetime.now(),
            "profile_completed": True,
            "default_password": False
        })

        # Add to admins collection
        if not db.admins.find_one({"email": email}):
            db.admins.insert_one({
                "email": email,
                "registration_number": reg_number,
                "created_at": datetime.now()
            })

        print(f"Admin user {reg_number} created successfully!")

except Exception as e:
    print(f"Error setting up admin: {e}")