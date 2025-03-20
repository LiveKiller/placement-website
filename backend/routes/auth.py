# routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Student, Faculty, HiringManager
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    # Create access token with user ID and role
    access_token = create_access_token(
        identity={'id': user.id, 'role': user.role},
        expires_delta=timedelta(hours=24)
    )
    
    return jsonify({
        'token': access_token,
        'role': user.role,
        'userId': user.id
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
        
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 409
    
    # Create new user
    user = User(email=data['email'], role=data['role'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()  # To get the user ID
    
    # Create role-specific profile
    if data['role'] == 'student':
        student = Student(
            user_id=user.id,
            full_name=data.get('full_name', ''),
            course=data.get('course', ''),
            department=data.get('department', '')
        )
        db.session.add(student)
    
    elif data['role'] == 'faculty':
        faculty = Faculty(
            user_id=user.id,
            full_name=data.get('full_name', ''),
            department=data.get('department', '')
        )
        db.session.add(faculty)
    
    elif data['role'] == 'hiring':
        hiring_manager = HiringManager(
            user_id=user.id,
            company_name=data.get('company_name', ''),
            contact_number=data.get('contact_number', '')
        )
        db.session.add(hiring_manager)
    
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'userId': user.id
    }), 201

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile information"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    profile_data = {
        'id': user.id,
        'email': user.email,
        'role': user.role
    }
    
    # Add role-specific data
    if user.role == 'student' and user.student:
        profile_data.update({
            'full_name': user.student.full_name,
            'course': user.student.course,
            'department': user.student.department,
            'cgpa': user.student.cgpa,
            'skills': user.student.skills.split(',') if user.student.skills else []
        })
    
    elif user.role == 'faculty' and user.faculty:
        profile_data.update({
            'full_name': user.faculty.full_name,
            'department': user.faculty.department
        })
    
    elif user.role == 'hiring' and user.hiring_manager:
        profile_data.update({
            'company_name': user.hiring_manager.company_name,
            'contact_number': user.hiring_manager.contact_number,
            'company_website': user.hiring_manager.company_website,
            'company_description': user.hiring_manager.company_description
        })
    
    return jsonify(profile_data), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile information"""
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update email if provided
    if data.get('email') and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 409
        user.email = data['email']
    
    # Update password if provided
    if data.get('password'):
        user.set_password(data['password'])
    
    # Update role-specific data
    if user.role == 'student' and user.student:
        if data.get('full_name'):
            user.student.full_name = data['full_name']
        if data.get('course'):
            user.student.course = data['course']
        if data.get('department'):
            user.student.department = data['department']
        if data.get('cgpa'):
            user.student.cgpa = data['cgpa']
        if data.get('skills'):
            user.student.skills = ','.join(data['skills'])
        if data.get('resume_url'):
            user.student.resume_url = data['resume_url']
    
    elif user.role == 'faculty' and user.faculty:
        if data.get('full_name'):
            user.faculty.full_name = data['full_name']
        if data.get('department'):
            user.faculty.department = data['department']
    
    elif user.role == 'hiring' and user.hiring_manager:
        if data.get('company_name'):
            user.hiring_manager.company_name = data['company_name']
        if data.get('contact_number'):
            user.hiring_manager.contact_number = data['contact_number']
        if data.get('company_website'):
            user.hiring_manager.company_website = data['company_website']
        if data.get('company_description'):
            user.hiring_manager.company_description = data['company_description']
    
    db.session.commit()
    
    return jsonify({'message': 'Profile updated successfully'}), 200
