"""Utility endpoints"""
from flask import Blueprint, jsonify
from datetime import datetime

utility_routes = Blueprint('utility', __name__)


@utility_routes.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # We don't have direct access to client here, so we'll just return status
    # The actual MongoDB check will be done in a service layer in a real implementation

    return jsonify({
        'status': 'UP',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200