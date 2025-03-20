import os

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql://root:root@localhost/internship_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-key-here'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    
    # App configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('FLASK_DEBUG') or True
    
    # Admin configuration
    FLASK_ADMIN_SWATCH = 'cerulean'