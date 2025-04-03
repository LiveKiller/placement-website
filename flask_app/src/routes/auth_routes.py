"""Authentication related routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from models.models import users_collection, api_logs_collection
from services.auth_service import is_admin
from utils.logging_utils import log_api_call

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/api/login', methods=['POST'])
def user_login():
    """User login endpoint"""
    data = request.json

    # Validate input
    if not all(key in data for key in ['registration_number', 'password']):
        return jsonify({'message': 'Missing registration number or password', 'success': False}), 400

    reg_number = str(data.get('registration_number')).strip()
    password = str(data.get('password')).strip()

    # Find user in the database
    user = users_collection.find_one({"registration_number": reg_number})

    if not user:
        return jsonify({'message': 'Invalid registration number or password', 'success': False}), 401

    # Check if the account is locked
    if user.get("locked", False):
        return jsonify({'message': 'Account is locked. Please reset your password or contact support.', 'success': False}), 403

    # Verify password
    if not check_password_hash(user['password'], password):
        # Try direct comparison for compatibility with simple version
        if password != user.get('password', ''):
            return jsonify({'message': 'Invalid registration number or password', 'success': False}), 401

    # Generate access token
    access_token = create_access_token(identity=user['registration_number'])

    # Log successful login
    log_api_call(api_logs_collection, '/api/login', reg_number, 200)

    return jsonify({
        'message': 'Logged in successfully!',
        'success': True,
        'access_token': access_token,
        'registration_number': user['registration_number'],
        'email': user.get('email', ''),
        'department': user.get('department', ''),
        'course': user.get('course', ''),
        'profile_completed': user.get('profile_completed', False),
        'default_password': user.get('default_password', False),
        'is_admin': is_admin(user.get('email', ''))
    }), 200

@auth_routes.route('/api/change-password', methods=['POST'])
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

    # Try both hashed and direct comparison for compatibility
    if not check_password_hash(user.get('password', ''), data['current_password']) and user.get('password') != data['current_password']:
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

    log_api_call(api_logs_collection, '/api/change-password', reg_number, 200)

    return jsonify({'message': 'Password changed successfully', 'success': True}), 200

@auth_routes.route('/api/check-admin', methods=['GET'])
@jwt_required()
def check_admin():
    """Check if user is an admin"""
    reg_number = get_jwt_identity()
    user = users_collection.find_one({"registration_number": reg_number})
    if not user:
        return jsonify({'is_admin': False}), 200

    return jsonify({'is_admin': is_admin(user.get('email', ''))}), 200