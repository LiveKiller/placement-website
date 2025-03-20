# routes/hiring.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, HiringManager, Internship, Application, Student
from datetime import datetime
from sqlalchemy import desc

hiring_bp = Blueprint('hiring', __name__)

@hiring_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def hiring_dashboard():
    """Get hiring manager dashboard data"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get internships posted by this hiring manager
    internships = Internship.query.filter_by(posted_by=hiring_manager.id).all()
    
    # Get pending applications for these internships
    pending_applications = 0
    for internship in internships:
        pending_count = Application.query.filter_by(
            internship_id=internship.id,
            status='pending',
            faculty_approval=True
        ).count()
        pending_applications += pending_count
    
    dashboard_data = {
        'hiring_manager': {
            'name': hiring_manager.company_name,
            'contact': hiring_manager.contact_number
        },
        'internships': {
            'total': len(internships),
            'active': sum(1 for i in internships if i.is_active)
        },
        'pending_applications': pending_applications,
        'recent_internships': [
            {
                'id': i.id,
                'title': i.title,
                'applications': Application.query.filter_by(internship_id=i.id).count(),
                'deadline': i.deadline.isoformat() if i.deadline else None,
                'is_active': i.is_active
            } for i in Internship.query.filter_by(posted_by=hiring_manager.id).order_by(desc(Internship.created_at)).limit(5).all()
        ]
    }
    
    return jsonify(dashboard_data), 200

@hiring_bp.route('/internships', methods=['GET'])
@jwt_required()
def get_internships():
    """Get internships posted by this hiring manager"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get query parameters
    status = request.args.get('status', 'all')
    
    # Build query
    query = Internship.query.filter_by(posted_by=hiring_manager.id)
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    internships = query.all()
    
    result = []
    for internship in internships:
        # Count applications
        applications = Application.query.filter_by(internship_id=internship.id).all()
        
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
            'is_active': internship.is_active,
            'created_at': internship.created_at.isoformat(),
            'applications_count': len(applications)
        })
    
    return jsonify(result), 200

@hiring_bp.route('/internship', methods=['POST'])
@jwt_required()
def create_internship():
    """Create a new internship"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get data from request
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'description', 'company', 'location', 'requirements']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    # Create internship
    internship = Internship(
        title=data['title'],
        description=data['description'],
        company=data['company'],
        location=data['location'],
        requirements=data['requirements'],
        stipend=data.get('stipend', ''),
        duration=data.get('duration', ''),
        posted_by=hiring_manager.id
    )
    
    # Set deadline if provided
    if data.get('deadline'):
        try:
            internship.deadline = datetime.fromisoformat(data['deadline'])
        except ValueError:
            return jsonify({'message': 'Invalid date format for deadline'}), 400
    
    db.session.add(internship)
    db.session.commit()
    
    return jsonify({
        'message': 'Internship created successfully',
        'internship_id': internship.id
    }), 201

@hiring_bp.route('/internship/<int:internship_id>', methods=['GET'])
@jwt_required()
def get_internship_details(internship_id):
    """Get details of a specific internship"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get internship
    internship = Internship.query.filter_by(id=internship_id, posted_by=hiring_manager.id).first()
    if not internship:
        return jsonify({'message': 'Internship not found'}), 404
    
    # Count applications
    applications = Application.query.filter_by(internship_id=internship.id).all()
    
    result = {
        'id': internship.id,
        'title': internship.title,
        'company': internship.company,
        'location': internship.location,
        'description': internship.description,
        'requirements': internship.requirements,
        'stipend': internship.stipend,
        'duration': internship.duration,
        'deadline': internship.deadline.isoformat() if internship.deadline else None,
        'is_active': internship.is_active,
        'created_at': internship.created_at.isoformat(),
        'applications_count': len(applications)
    }
    
    return jsonify(result), 200

@hiring_bp.route('/internship/<int:internship_id>', methods=['PUT'])
@jwt_required()
def update_internship(internship_id):
    """Update an internship"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get internship
    internship = Internship.query.filter_by(id=internship_id, posted_by=hiring_manager.id).first()
    if not internship:
        return jsonify({'message': 'Internship not found'}), 404
    
    # Get data from request
    data = request.get_json()
    
    # Update internship
    if data.get('title'):
        internship.title = data['title']
    if data.get('description'):
        internship.description = data['description']
    if data.get('company'):
        internship.company = data['company']
    if data.get('location'):
        internship.location = data['location']
    if data.get('requirements'):
        internship.requirements = data['requirements']
    if data.get('stipend'):
        internship.stipend = data['stipend']
    if data.get('duration'):
        internship.duration = data['duration']
    if data.get('deadline'):
        try:
            internship.deadline = datetime.fromisoformat(data['deadline'])
        except ValueError:
            return jsonify({'message': 'Invalid date format for deadline'}), 400
    if 'is_active' in data:
        internship.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({'message': 'Internship updated successfully'}), 200

@hiring_bp.route('/internship/<int:internship_id>', methods=['DELETE'])
@jwt_required()
def delete_internship(internship_id):
    """Delete an internship"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get internship
    internship = Internship.query.filter_by(id=internship_id, posted_by=hiring_manager.id).first()
    if not internship:
        return jsonify({'message': 'Internship not found'}), 404
    
    # Check if there are any applications
    applications = Application.query.filter_by(internship_id=internship.id).all()
    if applications:
        return jsonify({'message': 'Cannot delete internship with existing applications'}), 400
    
    # Delete internship
    db.session.delete(internship)
    db.session.commit()
    
    return jsonify({'message': 'Internship deleted successfully'}), 200

@hiring_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    """Get applications for internships posted by this hiring manager"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get internships posted by this hiring manager
    internships = Internship.query.filter_by(posted_by=hiring_manager.id).all()
    internship_ids = [i.id for i in internships]
    
    # Get query parameters
    status = request.args.get('status', 'all')
    internship_id = request.args.get('internship_id', None)
    
    # Build query
    query = Application.query.filter(Application.internship_id.in_(internship_ids))
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    if internship_id:
        query = query.filter_by(internship_id=internship_id)
    
    # Only show applications that have faculty approval
    query = query.filter_by(faculty_approval=True)
    
    applications = query.all()
    
    result = []
    for app in applications:
        student = Student.query.get(app.student_id)
        internship = Internship.query.get(app.internship_id)
        
        result.append({
            'id': app.id,
            'student': {
                'id': student.id,
                'name': student.full_name,
                'course': student.course,
                'cgpa': student.cgpa
            },
            'internship': {
                'id': internship.id,
                'title': internship.title,
                'company': internship.company
            },
            'status': app.status,
            'faculty_approval': app.faculty_approval,
            'hiring_approval': app.hiring_approval,
            'applied_at': app.applied_at.isoformat()
        })
    
    return jsonify(result), 200

@hiring_bp.route('/application/<int:app_id>', methods=['GET'])
@jwt_required()
def get_application_details(app_id):
    """Get details of a specific application"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get application
    application = Application.query.get(app_id)
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Verify that the application is for an internship posted by this hiring manager
    internship = Internship.query.get(application.internship_id)
    if not internship or internship.posted_by != hiring_manager.id:
        return jsonify({'message': 'Access denied'}), 403
    
    # Get student details
    student = Student.query.get(application.student_id)
    
    result = {
        'id': application.id,
        'student': {
            'id': student.id,
            'name': student.full_name,
            'course': student.course,
            'department': student.department,
            'cgpa': student.cgpa,
            'skills': student.skills.split(',') if student.skills else [],
            'resume_url': student.resume_url
        },
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
        'faculty_approval': application.faculty_approval,
        'hiring_approval': application.hiring_approval,
        'applied_at': application.applied_at.isoformat(),
        'cover_letter': application.cover_letter,
        'feedback': application.feedback
    }
    
    return jsonify(result), 200

@hiring_bp.route('/application/<int:app_id>/approve', methods=['POST'])
@jwt_required()
def approve_application(app_id):
    """Approve an application"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get application
    application = Application.query.get(app_id)
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Verify that the application is for an internship posted by this hiring manager
    internship = Internship.query.get(application.internship_id)
    if not internship or internship.posted_by != hiring_manager.id:
        return jsonify({'message': 'Access denied'}), 403
    
    # Verify that the application has faculty approval
    if not application.faculty_approval:
        return jsonify({'message': 'Application does not have faculty approval'}), 400
    
    # Update application
    application.status = 'approved'
    application.hiring_approval = True
    
    # Add feedback if provided
    data = request.get_json()
    if data and data.get('feedback'):
        application.feedback = data['feedback']
    
    db.session.commit()
    
    return jsonify({'message': 'Application approved successfully'}), 200

@hiring_bp.route('/application/<int:app_id>/reject', methods=['POST'])
@jwt_required()
def reject_application(app_id):
    """Reject an application"""
    current_user = get_jwt_identity()
    
    # Verify user is a hiring manager
    if current_user['role'] != 'hiring':
        return jsonify({'message': 'Access denied'}), 403
    
    hiring_manager = HiringManager.query.filter_by(user_id=current_user['id']).first()
    if not hiring_manager:
        return jsonify({'message': 'Hiring manager profile not found'}), 404
    
    # Get application
    application = Application.query.get(app_id)
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Verify that the application is for an internship posted by this hiring manager
    internship = Internship.query.get(application.internship_id)
    if not internship or internship.posted_by != hiring_manager.id:
        return jsonify({'message': 'Access denied'}), 403
    
    # Update application
    application.status = 'rejected'
    
    # Add feedback (required for rejection)
    data = request.get_json()
    if not data or not data.get('feedback'):
        return jsonify({'message': 'Feedback is required when rejecting an application'}), 400
    
    application.feedback = data['feedback']
    db.session.commit()
    
    return jsonify({'message': 'Application rejected successfully'}), 200
