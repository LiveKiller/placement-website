from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime)

    # Define relationships without conflicting backrefs
    student = db.relationship('Student', backref='user', uselist=False)
    faculty = db.relationship('Faculty', backref='user', uselist=False)
    hiring_manager = db.relationship('HiringManager', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        print(len(self.password_hash))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __tablename__ = 'student'  # Changed to singular to match foreign key reference
    
    id = db.Column(db.Integer, primary_key=True)  # Add a proper id primary key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(100))
    course = db.Column(db.String(100))
    department = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    skills = db.Column(db.Text)
    
    # Remove the conflicting relationship definition - the backref from User is enough
    # user = db.relationship('User', backref='student')  # Remove this line
    
    # Relationships
    applications = db.relationship('Application', backref='student', lazy='dynamic')

class Faculty(db.Model):
    __tablename__ = 'faculty'
    
    id = db.Column(db.Integer, primary_key=True)  # Add a proper id primary key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(100))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))

class HiringManager(db.Model):
    __tablename__ = 'hiring_manager'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    company_website = db.Column(db.String(200))
    company_description = db.Column(db.Text)
    contact_number = db.Column(db.String(20))
    
    # Relationships
    internships = db.relationship('Internship', backref='hiring_manager', lazy='dynamic')

class Internship(db.Model):
    __tablename__ = 'internship'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    requirements = db.Column(db.Text)
    stipend = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    posted_by = db.Column(db.Integer, db.ForeignKey('hiring_manager.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    applications = db.relationship('Application', backref='internship', lazy='dynamic')

class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    faculty_approval = db.Column(db.Boolean, default=False)
    hiring_approval = db.Column(db.Boolean, default=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    cover_letter = db.Column(db.Text)
    feedback = db.Column(db.Text)