import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # MongoDB configuration
    MONGO_URI = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_CLUSTER')}/{os.getenv('MONGO_DB_NAME')}?retryWrites=true&w=majority"
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'student_profile_system')

    # MongoDB retry configuration
    MONGO_MAX_RETRIES = 3
    MONGO_RETRY_DELAY = 3  # seconds

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    # Application version
    APP_VERSION = '1.0.0'

    # Debug mode
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'