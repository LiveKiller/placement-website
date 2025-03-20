# utils/helpers.py
import os
import re
from datetime import datetime
from functools import wraps
from flask import flash, redirect, url_for, session, current_app
from werkzeug.utils import secure_filename

def login_required(role=None):
    """
    Decorator to check if user is logged in and has the right role.
    If role is None, it checks only for login status.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'error')
                return redirect(url_for('auth.login'))
            
            if role and session.get('role') != role:
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('common.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def allowed_file(filename, allowed_extensions=None):
    """
    Check if the uploaded file has an allowed extension
    """
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'doc', 'docx'})
        
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, upload_folder=None):
    """
    Save an uploaded file to the specified folder
    """
    if upload_folder is None:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    return unique_filename

def format_date(date_obj, format_string='%B %d, %Y'):
    """
    Format a date object to a string
    """
    if not date_obj:
        return ''
    return date_obj.strftime(format_string)

def validate_email(email):
    """
    Validate email format
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def get_pagination_data(query, page, per_page):
    """
    Get pagination data for a query
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    data = {
        'items': pagination.items,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
        'next_page': pagination.next_num,
        'prev_page': pagination.prev_num,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': pagination.page
    }
    
    return data

def calculate_days_remaining(deadline):
    """
    Calculate the number of days remaining until a deadline
    """
    if not deadline:
        return 0
        
    delta = deadline - datetime.now()
    return max(0, delta.days)

def get_application_status_label(status):
    """
    Get a human-readable label for application status
    """
    status_labels = {
        'pending': 'Pending Review',
        'under_review': 'Under Review',
        'shortlisted': 'Shortlisted',
        'selected': 'Selected',
        'rejected': 'Not Selected'
    }
    
    return status_labels.get(status, 'Unknown')

def truncate_text(text, max_length=100):
    """
    Truncate text to a maximum length
    """
    if not text or len(text) <= max_length:
        return text
        
    return text[:max_length] + '...'

def generate_password_reset_token():
    """
    Generate a secure token for password reset
    """
    import secrets
    return secrets.token_urlsafe(32)

def parse_skills(skills_string):
    """
    Parse a comma-separated skills string into a list
    """
    if not skills_string:
        return []
        
    return [skill.strip() for skill in skills_string.split(',') if skill.strip()]

def match_skills(student_skills, internship_requirements):
    """
    Calculate a match score between student skills and internship requirements
    """
    if not student_skills or not internship_requirements:
        return 0
        
    student_skills_list = parse_skills(student_skills.lower())
    internship_req_list = parse_skills(internship_requirements.lower())
    
    if not student_skills_list or not internship_req_list:
        return 0
    
    matches = sum(1 for skill in student_skills_list if any(req in skill or skill in req for req in internship_req_list))
    match_percentage = (matches / len(internship_req_list)) * 100 if internship_req_list else 0
    
    return min(100, match_percentage)
