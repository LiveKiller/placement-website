# routes/student.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Student, Internship, Application
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def student_dashboard():
    """Get student dashboard data"""
    current_user = get_jwt_identity()
    
    # Verify user is a student
    if current_user['role'] != 'student':
        return jsonify({'message': 'Access denied'}), 403
    
    student = Student.query.filter_by(user_id=current_user['id']).first()
    if not student:
        return jsonify({'message': 'Student profile not found'}), 404
    
    # Get student's applications
    applications = Application.query.filter_by(student_id=student.id).all()
    
    # Get active internships
    active_internships = Internship.query.filter_by(is_active=True).all()
    
    dashboard_data = {
        'student': {
            'name': student.full_name,
            'course': student.course,
            'cgpa': student.cgpa
        },
        'applications': [
            {
                'id': app.id,
                'internship': app.internship.title,
                'company': app.internship.company,
                'status': app.status,
                'applied_at': app.applied_at.isoformat()
            } for app in applications
        ],
        'active_internships': len(active_internships),
        'pending_applications': sum(1 for app in applications if app.status == 'pending')
    }
    
    return jsonify(dashboard_data), 200

@student_bp.route('/internships', methods=['GET'])
@jwt_required()
def get_internships():
    """Get available internships for student"""
    current_user = get_jwt_identity()
    
    # Verify user is a student
    if current_user['role'] != 'student':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get student object
    student = Student.query.filter_by(user_id=current_user['id']).first()
    if not student:
        return jsonify({'message': 'Student profile not found'}), 404
    
    # Get all active internships
    internships = Internship.query.filter_by(is_active=True).all()
    
    # Check which internships student has already applied to
    applied_internships = {app.internship_id for app in Application.query.filter_by(student_id=student.id).all()}
    
    result = []
    for internship in internships:
        # Check if deadline has passed
        deadline_passed = False
        if internship.deadline and internship.deadline < datetime.utcnow():
            deadline_passed = True
        
        result.append({
            'id': internship.id,
            'title': internship.title,
            'company': internship.company,
            'location': internship.location,
            'description': internship.description,
            'requirements': internship.requirements,
            'stipend': internship.stipend,
            'duration': internship.duration,
            'deadline': internship.deadline.isoformat() if internship.deadline else None,
            'already_applied': internship.id in applied_internships,
            'deadline_passed': deadline_passed,
            'created_at': internship.created_at.isoformat()
        })
    
    return jsonify(result), 200

@student_bp.route('/apply/<int:internship_id>', methods=['POST'])
@jwt_required()
def apply_for_internship(internship_id):
    """Apply for an internship"""
    current_user = get_jwt_identity()
    
    # Verify user is a student
    if current_user['role'] != 'student':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get student object
    student = Student.query.filter_by(user_id=current_user['id']).first()
    if not student:
        return jsonify({'message': 'Student profile not found'}), 404
    
    # Check if internship exists and is active
    internship = Internship.query.filter_by(id=internship_id, is_active=True).first()
    if not internship:
        return jsonify({'message': 'Internship not found or not active'}), 404
    
    # Check if deadline has passed
    if internship.deadline and internship.deadline < datetime.utcnow():
        return jsonify({'message': 'Application deadline has passed'}), 400
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        student_id=student.id,
        internship_id=internship_id
    ).first()
    
    if existing_application:
        return jsonify({'message': 'You have already applied for this internship'}), 400
    
    # Get data from request
    data = request.get_json()
    
    # Create application
    application = Application(
        student_id=student.id,
        internship_id=internship_id,
        cover_letter=data.get('cover_letter', '')
    )
    
    db.session.add(application)
    db.session.commit()
    
    return jsonify({
        'message': 'Application submitted successfully',
        'application_id': application.id
    }), 201

@student_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_student_applications():
    """Get student's applications"""
    current_user = get_jwt_identity()
    
    # Verify user is a student
    if current_user['role'] != 'student':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get student object
    student = Student.query.filter_by(user_id=current_user['id']).first()
    if not student:
        return jsonify({'message': 'Student profile not found'}), 404
    
    # Get all applications
    applications = Application.query.filter_by(student_id=student.id).all()
    
    result = []
    for app in applications:
        result.append({
            'id': app.id,
            'internship': {
                'id': app.internship.id,
                'title': app.internship.title,
                'company': app.internship.company,
                'location': app.internship.location
            },
            'status': app.status,
            'applied_at': app.applied_at.isoformat(),
            'faculty_approval': app.faculty_approval,
            'hiring_approval': app.hiring_approval,
            'feedback': app.feedback
        })
    
    return jsonify(result), 200

@student_bp.route('/application/<int:app_id>', methods=['GET'])
@jwt_required()
def get_application_details(app_id):
    """Get details of a specific application"""
    current_user = get_jwt_identity()
    
    # Verify user is a student
    if current_user['role'] != 'student':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get student object
    student = Student.query.filter_by(user_id=current_user['id']).first()
    if not student:
        return jsonify({'message': 'Student profile not found'}), 404
    
    # Get application
    application = Application.query.filter_by(id=app_id, student_id=student.id).first()
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Get internship details
    internship = application.internship
    
    result = {
        'id': application.id,
        'internship': {
            'id': internship.id,
            'title': internship.title,
            'company': internship.company,
            'location': internship.location,
            'description': internship.description,
            'requirements': internship.requirements,
            'stipend': internship.stipend,
            'duration': internship.duration
        },
        'status': application.status,
        'applied_at': application.applied_at.isoformat(),
        'faculty_approval': application.faculty_approval,
        'hiring_approval': application.hiring_approval,
        'cover_letter': application.cover_letter,
        'feedback': application.feedback
    }
    
    return jsonify(result), 200

@student_bp.route('/application/<int:app_id>', methods=['PUT'])
@jwt_required()
def update_application(app_id):
    """Update an application"""
    current_user = get_jwt_identity()
    
    # Verify user is a student
    if current_user['role'] != 'student':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get student object
    student = Student.query.filter_by(user_id=current_user['id']).first()
    if not student:
        return jsonify({'message': 'Student profile not found'}), 404
    
    # Get application
    application = Application.query.filter_by(id=app_id, student_id=student.id).first()
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Only allow updates if application is pending
    if application.status != 'pending':
        return jsonify({'message': 'Cannot update application that is not pending'}), 400
    
    # Get data from request
    data = request.get_json()
    
    # Update application
    if data.get('cover_letter'):
        application.cover_letter = data['cover_letter']
    
    db.session.commit()
    
    return jsonify({'message': 'Application updated successfully'}), 200

@student_bp.route('/application/<int:app_id>', methods=['DELETE'])
@jwt_required()
def withdraw_application(app_id):
    """Withdraw an application"""
    current_user = get_jwt_identity()
    
    # Verify user is a student
    if current_user['role'] != 'student':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get student object
    student = Student.query.filter_by(user_id=current_user['id']).first()
    if not student:
        return jsonify({'message': 'Student profile not found'}), 404
    
    # Get application
    application = Application.query.filter_by(id=app_id, student_id=student.id).first()
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Only allow withdrawal if application is pending
    if application.status != 'pending':
        return jsonify({'message': 'Cannot withdraw application that is not pending'}), 400
    
    # Delete application
    db.session.delete(application)
    db.session.commit()
    
    return jsonify({'message': 'Application withdrawn successfully'}), 200
