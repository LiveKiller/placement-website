from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from datetime import timedelta
import logging

from config import Config
from utils.db_utils import init_db
from utils.logging_utils import setup_logging
from routes import register_routes

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    jwt = JWTManager(app)

    # Initialize database
    try:
        init_db(app)
    except Exception as e:
        logger.critical(f"Failed to initialize MongoDB: {e}")
        # Continue execution but services requiring DB will fail

    # Register routes
    register_routes(app)

    return app


app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'False').lower() == 'true'
    )