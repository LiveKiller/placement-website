from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
jwt = JWTManager(app)

# App configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# MongoDB connection with retry logic
MONGO_URI = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_CLUSTER')}/{os.getenv('MONGO_DB_NAME')}?retryWrites=true&w=majority"

MAX_RETRIES = 3
retry_count = 0

while retry_count < MAX_RETRIES:
    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        print("Connected successfully to MongoDB!")
        db = client[os.getenv('MONGO_DB_NAME')]
        users_collection = db["users"]
        admins_collection = db["admins"]
        profiles_collection = db["profiles"]
        break  # Success, exit retry loop
    except ConnectionFailure as e:
        retry_count += 1
        print(f"MongoDB connection attempt {retry_count} failed: {e}")
        if retry_count >= MAX_RETRIES:
            print("All connection attempts failed. Please check your MongoDB configuration.")
            # You may want to exit if connection is critical
            # import sys
            # sys.exit(1)
        time.sleep(3)  # Wait before retrying
    except Exception as e:
        print(f"Unexpected error connecting to MongoDB: {e}")
        break

# Required profile fields
REQUIRED_PROFILE_FIELDS = {
    "personal_details": [
        "full_name",
        "date_of_birth",
        "email",
        "phone_number",
        "address"
    ],
    "academic_details": [
        "registration_number",  # Primary Key
        "department",
        "course",
        "year_of_study",
        "cgpa",
        "skills",
        "certifications",
        "resume_link"
        # research_papers is optional
    ],
    "internship_experience": [
        "preferred_internship_domain",
        "preferred_companies",
        "previous_internships",
        "projects"
        # work_experience is optional
    ],
    "additional_information": [
        "linkedin_profile",
        "github_profile"
        # portfolio_website is optional
    ]
}


# Utility function to check if a user is admin
def is_admin(email):
    return admins_collection.find_one({"email": email}) is not None


# Admin Routes
@app.route('/api/admin/import-users', methods=['POST'])
@jwt_required()
def import_users():
    # Check if the user is an admin
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user or not is_admin(user.get('email')):
        return jsonify({'message': 'Unauthorized access.', 'success': False}), 403

    # Check if file is uploaded
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded.', 'success': False}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected.', 'success': False}), 400

    if not file.filename.endswith('.xlsx'):
        return jsonify({'message': 'Only Excel (.xlsx) files are supported.', 'success': False}), 400

    try:
        # Read Excel file
        df = pd.read_excel(file)

        # Validate required columns
        required_columns = ['registration_number', 'email', 'department', 'course']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'message': f'Missing required columns: {", ".join(missing_columns)}',
                'success': False
            }), 400

        # Process each row
        success_count = 0
        failed_count = 0
        errors = []

        for _, row in df.iterrows():
            try:
                reg_number = str(row['registration_number'])
                email = row['email']

                # Check if user already exists
                if users_collection.find_one({"registration_number": reg_number}):
                    errors.append(f"User with registration number {reg_number} already exists.")
                    failed_count += 1
                    continue

                # Generate a default password (e.g., first 5 chars of reg number + last 4 chars of email)
                default_password = f"{reg_number[:5]}_{email.split('@')[0][-4:]}"

                # Create user
                users_collection.insert_one({
                    "registration_number": reg_number,
                    "email": email,
                    "password": generate_password_hash(default_password, method='pbkdf2:sha256'),
                    "department": row.get('department', ''),
                    "course": row.get('course', ''),
                    "created_at": datetime.now(),
                    "profile_completed": False,
                    "default_password": True
                })

                success_count += 1
            except Exception as e:
                errors.append(f"Error processing row for {row.get('registration_number', 'unknown')}: {str(e)}")
                failed_count += 1

        return jsonify({
            'message': f'Processed {success_count + failed_count} users: {success_count} added successfully, {failed_count} failed.',
            'success': True,
            'errors': errors
        }), 200

    except Exception as e:
        return jsonify({'message': f'Error processing file: {str(e)}', 'success': False}), 500


@app.route('/api/admin/add-user', methods=['POST'])
@jwt_required()
def add_user():
    # Check if the user is an admin
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user or not is_admin(user.get('email')):
        return jsonify({'message': 'Unauthorized access.', 'success': False}), 403

    data = request.json
    required_fields = ['registration_number', 'email', 'department', 'course']

    # Validate required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            'message': f'Missing required fields: {", ".join(missing_fields)}',
            'success': False
        }), 400

    # Check if user already exists
    if users_collection.find_one({"registration_number": data['registration_number']}):
        return jsonify({'message': 'User with this registration number already exists.', 'success': False}), 400

    if users_collection.find_one({"email": data['email']}):
        return jsonify({'message': 'User with this email already exists.', 'success': False}), 400

    # Generate a default password
    default_password = f"{data['registration_number']}"

    # Create user
    users_collection.insert_one({
        "registration_number": data['registration_number'],
        "email": data['email'],
        "password": default_password,
        "department": data.get('department', ''),
        "course": data.get('course', ''),
        "created_at": datetime.now(),
        "profile_completed": False,
        "default_password": True
    })

    return jsonify({
        'message': 'User added successfully.',
        'success': True,
        'registration_number': data['registration_number'],
        'default_password': default_password
    }), 200


# User Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not all(key in data for key in ['registration_number', 'password']):
        return jsonify({'message': 'Missing registration number or password.', 'success': False}), 400

    user = users_collection.find_one({"registration_number": data.get('registration_number')})
    if not user or not check_password_hash(user['password'], data.get('password')):
        return jsonify({'message': 'Invalid registration number or password.', 'success': False}), 401

    # Generate token with registration number
    access_token = create_access_token(identity=user['registration_number'])

    return jsonify({
        'message': 'Logged in successfully!',
        'success': True,
        'access_token': access_token,
        'registration_number': user['registration_number'],
        'profile_completed': user.get('profile_completed', False),
        'default_password': user.get('default_password', False)
    }), 200


@app.route('/api/change-password', methods=['POST'])
@jwt_required()
def change_password():
    reg_number = get_jwt_identity()
    data = request.json

    if not all(key in data for key in ['current_password', 'new_password', 'confirm_password']):
        return jsonify({'message': 'Missing required fields.', 'success': False}), 400

    if data['new_password'] != data['confirm_password']:
        return jsonify({'message': 'New password and confirm password do not match.', 'success': False}), 400

    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found.', 'success': False}), 404

    if not check_password_hash(user['password'], data['current_password']):
        return jsonify({'message': 'Current password is incorrect.', 'success': False}), 401

    # Update password
    users_collection.update_one(
        {"registration_number": reg_number},
        {"$set": {
            "password": generate_password_hash(data['new_password'], method='pbkdf2:sha256'),
            "default_password": False
        }}
    )

    return jsonify({'message': 'Password changed successfully.', 'success': True}), 200


@app.route('/api/complete-profile', methods=['POST'])
@jwt_required()
def complete_profile():
    reg_number = get_jwt_identity()
    data = request.json

    # Check if user exists
    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found.', 'success': False}), 404

    # Validate all required fields
    missing_fields = {}
    for section, fields in REQUIRED_PROFILE_FIELDS.items():
        if section not in data:
            missing_fields[section] = fields
            continue

        section_data = data[section]
        missing_section_fields = [field for field in fields if field not in section_data or not section_data[field]]
        if missing_section_fields:
            missing_fields[section] = missing_section_fields

    if missing_fields:
        return jsonify({
            'message': 'Missing required fields.',
            'missing_fields': missing_fields,
            'success': False
        }), 400

    # Create profile
    profile_data = {
        "registration_number": reg_number,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "personal_details": data["personal_details"],
        "academic_details": data["academic_details"],
        "internship_experience": data["internship_experience"],
        "additional_information": data["additional_information"]
    }

    # Optional fields
    if "research_papers" in data.get("academic_details", {}):
        profile_data["academic_details"]["research_papers"] = data["academic_details"]["research_papers"]

    if "work_experience" in data.get("internship_experience", {}):
        profile_data["internship_experience"]["work_experience"] = data["internship_experience"]["work_experience"]

    if "portfolio_website" in data.get("additional_information", {}):
        profile_data["additional_information"]["portfolio_website"] = data["additional_information"][
            "portfolio_website"]

    # Check if profile already exists
    existing_profile = profiles_collection.find_one({"registration_number": reg_number})
    if existing_profile:
        # Update existing profile
        profiles_collection.update_one(
            {"registration_number": reg_number},
            {"$set": profile_data}
        )
    else:
        # Create new profile
        profiles_collection.insert_one(profile_data)

    # Update user profile status
    users_collection.update_one(
        {"registration_number": reg_number},
        {"$set": {"profile_completed": True}}
    )

    return jsonify({
        'message': 'Profile completed successfully!',
        'success': True,
        'registration_number': reg_number
    }), 200


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    reg_number = get_jwt_identity()

    # Find user and profile
    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found.', 'success': False}), 404

    profile = profiles_collection.find_one({"registration_number": reg_number})
    if not profile:
        return jsonify({
            'message': 'Profile not completed yet.',
            'success': False,
            'profile_completed': False
        }), 404

    # Remove MongoDB _id field
    profile.pop('_id', None)

    return jsonify({
        'success': True,
        'profile': profile
    }), 200


@app.route('/api/check-profile-status', methods=['GET'])
@jwt_required()
def check_profile_status():
    reg_number = get_jwt_identity()

    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found.', 'success': False}), 404

    return jsonify({
        'success': True,
        'profile_completed': user.get('profile_completed', False),
        'default_password': user.get('default_password', False)
    }), 200


@app.route('/api/check-admin', methods=['GET'])
@jwt_required()
def check_admin():
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'is_admin': False}), 200

    return jsonify({'is_admin': is_admin(user.get('email'))}), 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)