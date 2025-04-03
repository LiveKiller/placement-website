"""Profile management routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models.models import (
    users_collection, profiles_collection, api_logs_collection
)
from services.auth_service import is_admin
from utils.validation_utils import validate_profile_data
from utils.logging_utils import log_api_call

profile_routes = Blueprint('profile', __name__)

@profile_routes.route('/api/complete-profile', methods=['POST'])
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
    missing_fields = validate_profile_data(data)
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
        profile_data["additional_information"]["portfolio_website"] = data["additional_information"]["portfolio_website"]

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

    log_api_call(api_logs_collection, '/api/complete-profile', reg_number, 200)

    return jsonify({
        'message': 'Profile completed successfully!',
        'success': True,
        'registration_number': reg_number
    }), 200


@profile_routes.route('/api/profile', methods=['GET'])
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


@profile_routes.route('/api/profile/<registration_number>', methods=['GET'])
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

    log_api_call(api_logs_collection, f'/api/profile/{registration_number}', admin_reg, 200, {
        'viewed_profile': registration_number
    })

    return jsonify({
        'success': True,
        'profile': profile
    }), 200


@profile_routes.route('/api/check-profile-status', methods=['GET'])
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


