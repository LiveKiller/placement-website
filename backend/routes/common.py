# routes/common.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Student, Internship, Application, Faculty, HiringManager

common_bp = Blueprint('common', __name__)

@common_bp.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "message": "Internship Placement System API",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth",
            "student": "/api/student",
            "faculty": "/api/faculty",
            "hiring": "/api/hiring"
        }
    }), 200

@common_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "API is running"
    }), 200

@common_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get general statistics about the platform"""
    # Count users by role
    student_count = Student.query.count()
    faculty_count = Faculty.query.count()
    hiring_count = HiringManager.query.count()
    
    # Count internships
    active_internships = Internship.query.filter_by(is_active=True).count()
    total_internships = Internship.query.count()
    
    # Count applications
    pending_applications = Application.query.filter_by(status='pending').count()
    approved_applications = Application.query.filter_by(status='approved').count()
    rejected_applications = Application.query.filter_by(status='rejected').count()
    
    stats = {
        "users": {
            "students": student_count,
            "faculty": faculty_count,
            "hiring_managers": hiring_count,
            "total": student_count + faculty_count + hiring_count
        },
        "internships": {
            "active": active_internships,
            "total": total_internships
        },
        "applications": {
            "pending": pending_applications,
            "approved": approved_applications,
            "rejected": rejected_applications,
            "total": pending_applications + approved_applications + rejected_applications
        }
    }
    
    return jsonify(stats), 200

@common_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    """Search internships"""
    # Get query parameters
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    # Search in internships
    if category == 'all' or category == 'internships':
        internships = Internship.query.filter(
            (Internship.title.ilike(f'%{query}%')) |
            (Internship.description.ilike(f'%{query}%')) |
            (Internship.company.ilike(f'%{query}%')) |
            (Internship.requirements.ilike(f'%{query}%'))
        ).all()
        
        internships_result = [
            {
                'id': i.id,
                'title': i.title,
                'company': i.company,
                'location': i.location,
                'description': i.description,
                'is_active': i.is_active
            } for i in internships
        ]
    else:
        internships_result = []
    
    # Search in students
    if category == 'all' or category == 'students':
        students = Student.query.filter(
            (Student.full_name.ilike(f'%{query}%')) |
            (Student.course.ilike(f'%{query}%')) |
            (Student.department.ilike(f'%{query}%')) |
            (Student.skills.ilike(f'%{query}%'))
        ).all()
        
        students_result = [
            {
                'id': s.id,
                'name': s.full_name,
                'course': s.course,
                'department': s.department,
                'skills': s.skills.split(',') if s.skills else []
            } for s in students
        ]
    else:
        students_result = []
    
    # Return results
    return jsonify({
        'internships': internships_result,
        'students': students_result
    }), 200