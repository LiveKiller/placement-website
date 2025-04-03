from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
from datetime import datetime, timedelta
import traceback
import json
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import time
from dotenv import load_dotenv
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# App configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

jwt = JWTManager(app)

# MongoDB connection with retry logic
MONGO_URI = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_CLUSTER')}/{os.getenv('MONGO_DB_NAME')}?retryWrites=true&w=majority"

MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds


def connect_to_mongo():
    """Establish connection to MongoDB with retry logic"""
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            client = MongoClient(MONGO_URI)
            # Test connection
            client.admin.command('ping')
            logger.info("Connected successfully to MongoDB!")
            return client
        except ConnectionFailure as e:
            retry_count += 1
            logger.warning(f"MongoDB connection attempt {retry_count} failed: {e}")
            if retry_count >= MAX_RETRIES:
                logger.error("All connection attempts failed. Please check your MongoDB configuration.")
                raise
            time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise


# Initialize MongoDB connections
try:
    client = connect_to_mongo()
    db = client[os.getenv('MONGO_DB_NAME', 'student_profile_system')]
    users_collection = db["users"]
    admins_collection = db["admins"]
    profiles_collection = db["profiles"]
    error_logs_collection = db["error_logs"]
except Exception as e:
    logger.critical(f"Failed to initialize MongoDB: {e}")
    # Continue execution but services requiring DB will fail

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


# Error handling middleware
@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler to log errors and return appropriate responses"""
    # Get the stack trace
    tb = traceback.format_exc()

    # Log the error
    logger.error(f"Unhandled exception: {str(e)}\n{tb}")

    # Save error to database
    try:
        error_logs_collection.insert_one({
            "error": str(e),
            "traceback": tb,
            "timestamp": datetime.now(),
            "endpoint": request.path,
            "method": request.method,
            "request_data": request.get_json(silent=True),
            "headers": dict(request.headers)
        })
    except Exception as db_error:
        logger.error(f"Failed to log error to database: {db_error}")

    # Return appropriate response
    return jsonify({
        'message': 'An unexpected error occurred. Please try again later.',
        'error_id': str(datetime.now().timestamp()),
        'success': False
    }), 500


# Utility functions
def is_admin(email):
    """Check if a user is an admin"""
    return admins_collection.find_one({"email": email}) is not None


def log_api_call(endpoint, user_id, status_code, details=None):
    """Log API calls for auditing"""
    try:
        db.api_logs.insert_one({
            "endpoint": endpoint,
            "user_id": user_id,
            "timestamp": datetime.now(),
            "status_code": status_code,
            "details": details or {}
        })
    except Exception as e:
        logger.error(f"Failed to log API call: {e}")


# Admin management route
@app.route('/api/admin/create-admin', methods=['POST'])
@jwt_required()
def create_admin():
    """Create a new admin user"""
    # Verify request is from an existing admin
    current_user_reg = get_jwt_identity()
    current_user = users_collection.find_one({"registration_number": current_user_reg})

    if not current_user or not is_admin(current_user.get('email')):
        return jsonify({'message': 'Unauthorized access', 'success': False}), 403

    data = request.json
    if not all(key in data for key in ['email']):
        return jsonify({'message': 'Missing required fields', 'success': False}), 400

    # Check if the email is associated with a user
    user = users_collection.find_one({"email": data['email']})
    if not user:
        return jsonify({'message': 'User with this email does not exist', 'success': False}), 404

    # Check if already an admin
    if is_admin(data['email']):
        return jsonify({'message': 'User is already an admin', 'success': False}), 400

    # Add as admin
    admins_collection.insert_one({
        "email": data['email'],
        "created_at": datetime.now(),
        "created_by": current_user.get('email')
    })

    return jsonify({
        'message': 'Admin created successfully',
        'success': True
    }), 201


# Admin Routes
@app.route('/api/admin/import-users', methods=['POST'])
@jwt_required()
def import_users():
    """Import multiple users from Excel or CSV file"""
    # Check if the user is an admin
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user or not is_admin(user.get('email')):
        log_api_call('/api/admin/import-users', reg_number, 403, {'error': 'Unauthorized access'})
        return jsonify({'message': 'Unauthorized access', 'success': False}), 403

    # Check if file is uploaded
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded', 'success': False}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected', 'success': False}), 400

    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        return jsonify({'message': 'Only Excel (.xlsx) or CSV (.csv) files are supported', 'success': False}), 400

    try:
        # Read file based on extension
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

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
        new_users = []

        for _, row in df.iterrows():
            try:
                reg_number = str(row['registration_number']).strip()
                email = str(row['email']).strip()

                # Skip empty rows
                if not reg_number or not email:
                    errors.append("Skipped row with empty registration number or email")
                    failed_count += 1
                    continue

                # Check if user already exists
                if users_collection.find_one({"registration_number": reg_number}):
                    errors.append(f"User with registration number {reg_number} already exists")
                    failed_count += 1
                    continue

                if users_collection.find_one({"email": email}):
                    errors.append(f"User with email {email} already exists")
                    failed_count += 1
                    continue

                # Generate a default password
                default_password = reg_number  # Using reg number as default password

                # Create user
                new_user = {
                    "registration_number": reg_number,
                    "email": email,
                    "password": generate_password_hash(default_password, method='pbkdf2:sha256'),
                    "department": str(row.get('department', '')).strip(),
                    "course": str(row.get('course', '')).strip(),
                    "created_at": datetime.now(),
                    "profile_completed": False,
                    "default_password": True,
                    "created_by": user.get('email')
                }

                users_collection.insert_one(new_user)
                new_users.append({
                    "registration_number": reg_number,
                    "email": email,
                    "default_password": default_password
                })
                success_count += 1

            except Exception as e:
                error_detail = f"Error processing row for {row.get('registration_number', 'unknown')}: {str(e)}"
                errors.append(error_detail)
                logger.error(error_detail)
                failed_count += 1

        log_api_call('/api/admin/import-users', reg_number, 200, {
            'success_count': success_count,
            'failed_count': failed_count
        })

        return jsonify({
            'message': f'Processed {success_count + failed_count} users: {success_count} added successfully, {failed_count} failed',
            'success': True,
            'new_users': new_users,
            'errors': errors
        }), 200

    except Exception as e:
        tb = traceback.format_exc()
        error_id = datetime.now().timestamp()

        error_logs_collection.insert_one({
            "error_id": str(error_id),
            "error": str(e),
            "traceback": tb,
            "timestamp": datetime.now(),
            "endpoint": "/api/admin/import-users",
            "user": reg_number
        })

        logger.error(f"Error processing file: {str(e)}\n{tb}")
        return jsonify({
            'message': f'Error processing file: {str(e)}',
            'error_id': str(error_id),
            'success': False
        }), 500


@app.route('/api/admin/add-user', methods=['POST'])
@jwt_required()
def add_user():
    """Add a single user"""
    # Check if the user is an admin
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user or not is_admin(user.get('email')):
        return jsonify({'message': 'Unauthorized access', 'success': False}), 403

    data = request.json
    required_fields = ['registration_number', 'email', 'department', 'course']

    # Validate required fields
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        return jsonify({
            'message': f'Missing required fields: {", ".join(missing_fields)}',
            'success': False
        }), 400

    # Clean and validate input
    reg_number = str(data['registration_number']).strip()
    email = str(data['email']).strip()

    # Check if user already exists
    if users_collection.find_one({"registration_number": reg_number}):
        return jsonify({'message': 'User with this registration number already exists', 'success': False}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({'message': 'User with this email already exists', 'success': False}), 400

    # Generate a default password (using registration number as password)
    default_password = reg_number

    # Create user
    users_collection.insert_one({
        "registration_number": reg_number,
        "email": email,
        "password": generate_password_hash(default_password, method='pbkdf2:sha256'),
        "department": data.get('department', '').strip(),
        "course": data.get('course', '').strip(),
        "created_at": datetime.now(),
        "profile_completed": False,
        "default_password": True,
        "created_by": user.get('email')
    })

    log_api_call('/api/admin/add-user', reg_number, 200, {
        'added_user': reg_number
    })

    return jsonify({
        'message': 'User added successfully',
        'success': True,
        'registration_number': reg_number,
        'default_password': default_password
    }), 201


@app.route('/api/admin/list-users', methods=['GET'])
@jwt_required()
def list_users():
    """List all users with pagination"""
    # Check if the user is an admin
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user or not is_admin(user.get('email')):
        return jsonify({'message': 'Unauthorized access', 'success': False}), 403

    # Pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    skip = (page - 1) * per_page

    # Optional filters
    filters = {}
    if 'department' in request.args and request.args['department']:
        filters['department'] = request.args['department']
    if 'course' in request.args and request.args['course']:
        filters['course'] = request.args['course']
    if 'profile_completed' in request.args:
        filters['profile_completed'] = request.args['profile_completed'].lower() == 'true'

    # Get users with pagination
    users_cursor = users_collection.find(
        filters,
        {'password': 0}  # Exclude password
    ).sort('created_at', -1).skip(skip).limit(per_page)

    users_list = list(users_cursor)
    total_users = users_collection.count_documents(filters)

    # Convert ObjectId to string
    for user in users_list:
        user['_id'] = str(user['_id'])
        user['created_at'] = user['created_at'].isoformat()

    return jsonify({
        'success': True,
        'users': users_list,
        'total': total_users,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_users + per_page - 1) // per_page
    }), 200


# User Routes
@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.json
    if not all(key in data for key in ['registration_number', 'password']):
        return jsonify({'message': 'Missing registration number or password', 'success': False}), 400

    reg_number = str(data.get('registration_number')).strip()
    password = str(data.get('password'))

    user = users_collection.find_one({"registration_number": reg_number})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid registration number or password', 'success': False}), 401

    # Generate token with registration number
    access_token = create_access_token(identity=user['registration_number'])

    log_api_call('/api/login', reg_number, 200)

    return jsonify({
        'message': 'Logged in successfully!',
        'success': True,
        'access_token': access_token,
        'registration_number': user['registration_number'],
        'email': user['email'],
        'department': user.get('department', ''),
        'course': user.get('course', ''),
        'profile_completed': user.get('profile_completed', False),
        'default_password': user.get('default_password', False),
        'is_admin': is_admin(user.get('email', ''))
    }), 200


@app.route('/api/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password endpoint"""
    reg_number = get_jwt_identity()
    data = request.json

    if not all(key in data for key in ['current_password', 'new_password', 'confirm_password']):
        return jsonify({'message': 'Missing required fields', 'success': False}), 400

    if data['new_password'] != data['confirm_password']:
        return jsonify({'message': 'New password and confirm password do not match', 'success': False}), 400

    if len(data['new_password']) < 8:
        return jsonify({'message': 'Password must be at least 8 characters long', 'success': False}), 400

    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found', 'success': False}), 404

    if not check_password_hash(user['password'], data['current_password']):
        return jsonify({'message': 'Current password is incorrect', 'success': False}), 401

    # Update password
    users_collection.update_one(
        {"registration_number": reg_number},
        {"$set": {
            "password": generate_password_hash(data['new_password'], method='pbkdf2:sha256'),
            "default_password": False,
            "password_updated_at": datetime.now()
        }}
    )

    log_api_call('/api/change-password', reg_number, 200)

    return jsonify({'message': 'Password changed successfully', 'success': True}), 200


@app.route('/api/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password():
    """Admin endpoint to reset a user's password"""
    admin_reg = get_jwt_identity()
    admin = users_collection.find_one({"registration_number": admin_reg})

    if not admin or not is_admin(admin.get('email')):
        return jsonify({'message': 'Unauthorized access', 'success': False}), 403

    data = request.json
    if 'registration_number' not in data:
        return jsonify({'message': 'Missing registration number', 'success': False}), 400

    user_reg = data['registration_number']
    user = users_collection.find_one({"registration_number": user_reg})

    if not user:
        return jsonify({'message': 'User not found', 'success': False}), 404

    # Reset password to registration number
    new_password = user_reg

    users_collection.update_one(
        {"registration_number": user_reg},
        {"$set": {
            "password": generate_password_hash(new_password, method='pbkdf2:sha256'),
            "default_password": True,
            "password_reset_at": datetime.now(),
            "password_reset_by": admin.get('email')
        }}
    )

    log_api_call('/api/reset-password', admin_reg, 200, {
        'target_user': user_reg
    })

    return jsonify({
        'message': 'Password reset successfully',
        'success': True,
        'registration_number': user_reg,
        'new_password': new_password
    }), 200


@app.route('/api/complete-profile', methods=['POST'])
@jwt_required()
def complete_profile():
    """Complete or update user profile"""
    reg_number = get_jwt_identity()
    data = request.json

    # Check if user exists
    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found', 'success': False}), 404

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
            'message': 'Missing required fields',
            'missing_fields': missing_fields,
            'success': False
        }), 400

    # Validate that the registration number in the profile matches the authenticated user
    if data.get("academic_details", {}).get("registration_number") != reg_number:
        return jsonify({
            'message': 'Registration number in profile does not match authenticated user',
            'success': False
        }), 400

    # Create profile
    profile_data = {
        "registration_number": reg_number,
        "email": user.get('email'),
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
        profile_data["created_at"] = existing_profile.get("created_at")
        profiles_collection.update_one(
            {"registration_number": reg_number},
            {"$set": profile_data}
        )
    else:
        # Create new profile
        profile_data["created_at"] = datetime.now()
        profiles_collection.insert_one(profile_data)

    # Update user profile status
    users_collection.update_one(
        {"registration_number": reg_number},
        {"$set": {"profile_completed": True}}
    )

    log_api_call('/api/complete-profile', reg_number, 200)

    return jsonify({
        'message': 'Profile completed successfully!',
        'success': True,
        'registration_number': reg_number
    }), 200


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    reg_number = get_jwt_identity()

    # Find user and profile
    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found', 'success': False}), 404

    profile = profiles_collection.find_one({"registration_number": reg_number})
    if not profile:
        return jsonify({
            'message': 'Profile not completed yet',
            'success': False,
            'profile_completed': False
        }), 404

    # Remove MongoDB _id field
    profile.pop('_id', None)

    # Convert datetime objects to strings
    for key in ['created_at', 'updated_at']:
        if key in profile and isinstance(profile[key], datetime):
            profile[key] = profile[key].isoformat()

    return jsonify({
        'success': True,
        'profile': profile
    }), 200


@app.route('/api/profile/<registration_number>', methods=['GET'])
@jwt_required()
def get_user_profile(registration_number):
    """Get another user's profile (admin only)"""
    admin_reg = get_jwt_identity()
    admin = users_collection.find_one({"registration_number": admin_reg})

    if not admin or not is_admin(admin.get('email')):
        return jsonify({'message': 'Unauthorized access', 'success': False}), 403

    # Find profile
    profile = profiles_collection.find_one({"registration_number": registration_number})
    if not profile:
        return jsonify({
            'message': 'Profile not found',
            'success': False
        }), 404

    # Remove MongoDB _id field
    profile.pop('_id', None)

    # Convert datetime objects to strings
    for key in ['created_at', 'updated_at']:
        if key in profile and isinstance(profile[key], datetime):
            profile[key] = profile[key].isoformat()

    log_api_call('/api/profile/<registration_number>', admin_reg, 200, {
        'viewed_profile': registration_number
    })

    return jsonify({
        'success': True,
        'profile': profile
    }), 200


@app.route('/api/check-profile-status', methods=['GET'])
@jwt_required()
def check_profile_status():
    """Check if user has completed profile"""
    reg_number = get_jwt_identity()

    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'message': 'User not found', 'success': False}), 404

    return jsonify({
        'success': True,
        'profile_completed': user.get('profile_completed', False),
        'default_password': user.get('default_password', False),
        'is_admin': is_admin(user.get('email', ''))
    }), 200


@app.route('/api/check-admin', methods=['GET'])
@jwt_required()
def check_admin():
    """Check if user is an admin"""
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'is_admin': False}), 200

    return jsonify({'is_admin': is_admin(user.get('email', ''))}), 200


# Utility endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check MongoDB connection
    mongo_status = "OK"
    try:
        client.admin.command('ping')
    except Exception as e:
        mongo_status = f"Failed: {str(e)}"

    return jsonify({
        'status': 'UP',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'database': mongo_status
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('DEBUG', 'False').lower() == 'true')