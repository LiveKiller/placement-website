# routes/faculty.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Faculty, Student, Internship, Application
from sqlalchemy import desc

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def faculty_dashboard():
    """Get faculty dashboard data"""
    current_user = get_jwt_identity()
    
    # Verify user is a faculty
    if current_user['role'] != 'faculty':
        return jsonify({'message': 'Access denied'}), 403
    
    faculty = Faculty.query.filter_by(user_id=current_user['id']).first()
    if not faculty:
        return jsonify({'message': 'Faculty profile not found'}), 404
    
    # Get pending applications
    pending_applications = Application.query.filter_by(faculty_approval=False).all()
    
    # Get approved applications
    approved_applications = Application.query.filter_by(faculty_approval=True).all()
    
    dashboard_data = {
        'faculty': {
            'name': faculty.full_name,
            'department': faculty.department
        },
        'pending_applications': len(pending_applications),
        'approved_applications': len(approved_applications),
        'recent_applications': [
            {
                'id': app.id,
                'student': Student.query.get(app.student_id).full_name,
                'internship': Internship.query.get(app.internship_id).title,
                'status': app.status,
                'applied_at': app.applied_at.isoformat()
            } for app in Application.query.order_by(desc(Application.applied_at)).limit(5).all()
        ]
    }
    
    return jsonify(dashboard_data), 200

@faculty_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    """Get all applications for faculty review"""
    current_user = get_jwt_identity()
    
    # Verify user is a faculty
    if current_user['role'] != 'faculty':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get query parameters
    status = request.args.get('status', 'all')
    approval = request.args.get('approval', 'all')
    
    # Build query
    query = Application.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    if approval == 'pending':
        query = query.filter_by(faculty_approval=False)
    elif approval == 'approved':
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
            'applied_at': app.applied_at.isoformat()
        })
    
    return jsonify(result), 200

@faculty_bp.route('/application/<int:app_id>', methods=['GET'])
@jwt_required()
def get_application_details(app_id):
    """Get details of a specific application"""
    current_user = get_jwt_identity()
    
    # Verify user is a faculty
    if current_user['role'] != 'faculty':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get application
    application = Application.query.get(app_id)
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    student = Student.query.get(application.student_id)
    internship = Internship.query.get(application.internship_id)
    
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

@faculty_bp.route('/application/<int:app_id>/approve', methods=['POST'])
@jwt_required()
def approve_application(app_id):
    """Approve an application"""
    current_user = get_jwt_identity()
    
    # Verify user is a faculty
    if current_user['role'] != 'faculty':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get application
    application = Application.query.get(app_id)
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Update application
    application.faculty_approval = True
    
    # Add feedback if provided
    data = request.get_json()
    if data and data.get('feedback'):
        application.feedback = data['feedback']
    
    db.session.commit()
    
    return jsonify({'message': 'Application approved successfully'}), 200

@faculty_bp.route('/application/<int:app_id>/reject', methods=['POST'])
@jwt_required()
def reject_application(app_id):
    """Reject an application"""
    current_user = get_jwt_identity()
    
    # Verify user is a faculty
    if current_user['role'] != 'faculty':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get application
    application = Application.query.get(app_id)
    if not application:
        return jsonify({'message': 'Application not found'}), 404
    
    # Update application
    application.status = 'rejected'
    
    # Add feedback (required for rejection)
    data = request.get_json()
    if not data or not data.get('feedback'):
        return jsonify({'message': 'Feedback is required when rejecting an application'}), 400
    
    application.feedback = data['feedback']
    db.session.commit()
    
    return jsonify({'message': 'Application rejected successfully'}), 200

@faculty_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    """Get all students"""
    current_user = get_jwt_identity()
    
    # Verify user is a faculty
    if current_user['role'] != 'faculty':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get query parameters
    department = request.args.get('department', None)
    course = request.args.get('course', None)
    
    # Build query
    query = Student.query
    
    if department:
        query = query.filter_by(department=department)
    
    if course:
        query = query.filter_by(course=course)
    
    students = query.all()
    
    result = []
    for student in students:
        # Count applications
        applications = Application.query.filter_by(student_id=student.id).all()
        
        result.append({
            'id': student.id,
            'name': student.full_name,
            'course': student.course,
            'department': student.department,
            'cgpa': student.cgpa,
            'skills': student.skills.split(',') if student.skills else [],
            'application_count': len(applications)
        })
    
    return jsonify(result), 200

@faculty_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_reports():
    """Get faculty reports"""
    current_user = get_jwt_identity()
    
    # Verify user is a faculty
    if current_user['role'] != 'faculty':
        return jsonify({'message': 'Access denied'}), 403
    
    # Get all applications
    applications = Application.query.all()
    
    # Count applications by status
    status_counts = {
        'pending': 0,
        'approved': 0,
        'rejected': 0
    }
    
    for app in applications:
        status_counts[app.status] += 1
    
    # Count applications by departments
    department_counts = {}
    for app in applications:
        student = Student.query.get(app.student_id)
        department = student.department
        
        if department not in department_counts:
            department_counts[department] = 0
        
        department_counts[department] += 1
    
    # Count applications by companies
    company_counts = {}
    for app in applications:
        internship = Internship.query.get(app.internship_id)
        company = internship.company
        
        if company not in company_counts:
            company_counts[company] = 0
        
        company_counts[company] += 1
    
    return jsonify({
        'status_counts': status_counts,
        'department_counts': department_counts,
        'company_counts': company_counts
    }), 200