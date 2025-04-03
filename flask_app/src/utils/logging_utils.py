"""Logging utilities"""
import os
import logging
from datetime import datetime
import traceback
import json
from flask import request


def setup_logging():
    """Set up logging configuration"""
    # Ensure logs directory exists
    log_dir = os.path.dirname('logs/app.log')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )


def log_api_call(collection, endpoint, user_id, status_code, details=None):
    """Log API calls for auditing"""
    try:
        collection.insert_one({
            "endpoint": endpoint,
            "user_id": user_id,
            "timestamp": datetime.now(),
            "status_code": status_code,
            "details": details or {}
        })
    except Exception as e:
        logging.error(f"Failed to log API call: {e}")


def log_error(collection, e, request_obj=None):
    """Log errors to database"""
    try:
        # Get the stack trace
        tb = traceback.format_exc()

        # Log the error
        logging.error(f"Unhandled exception: {str(e)}\n{tb}")

        # Save error to database
        error_data = {
            "error": str(e),
            "traceback": tb,
            "timestamp": datetime.now(),
        }

        if request_obj:
            error_data.update({
                "endpoint": request_obj.path,
                "method": request_obj.method,
                "request_data": request_obj.get_json(silent=True),
                "headers": dict(request_obj.headers)
            })

        collection.insert_one(error_data)
        return str(datetime.now().timestamp())  # Return error ID

    except Exception as db_error:
        logging.error(f"Failed to log error to database: {db_error}")
        return None