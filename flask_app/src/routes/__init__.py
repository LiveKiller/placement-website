from flask import jsonify, request
import logging
import traceback
from datetime import datetime

from models.models import error_logs_collection
from routes.auth_routes import auth_routes
from .admin_routes import admin_routes
from .profile_routes import profile_routes
from routes.utility_routes import utility_routes
from utils.logging_utils import log_error

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all application routes"""
    # Register blueprint routes
    app.register_blueprint(auth_routes)
    app.register_blueprint(admin_routes)
    app.register_blueprint(profile_routes)
    app.register_blueprint(utility_routes)

    # Global error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global exception handler to log errors and return appropriate responses"""
        error_id = log_error(error_logs_collection, e, request)

        # Return appropriate response
        return jsonify({
            'message': 'An unexpected error occurred. Please try again later.',
            'error_id': error_id,
            'success': False
        }), 500

    return app