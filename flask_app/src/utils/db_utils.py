"""Database utility functions"""
import time
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import models.models as models

logger = logging.getLogger(__name__)


def connect_to_mongo(mongo_uri, max_retries=3, retry_delay=3):
    """Establish connection to MongoDB with retry logic"""
    retry_count = 0

    while retry_count < max_retries:
        try:
            client = MongoClient(mongo_uri)
            # Test connection
            client.admin.command('ping')
            logger.info("Connected successfully to MongoDB!")
            return client
        except ConnectionFailure as e:
            retry_count += 1
            logger.warning(f"MongoDB connection attempt {retry_count} failed: {e}")
            if retry_count >= max_retries:
                logger.error("All connection attempts failed. Please check your MongoDB configuration.")
                raise
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise


def init_db(app):
    """Initialize database connection and collections"""
    client = connect_to_mongo(
        app.config['MONGO_URI'],
        app.config['MONGO_MAX_RETRIES'],
        app.config['MONGO_RETRY_DELAY']
    )

    db = client[app.config['MONGO_DB_NAME']]

    # Initialize collections
    models.users_collection = db["users"]
    models.admins_collection = db["admins"]
    models.profiles_collection = db["profiles"]
    models.error_logs_collection = db["error_logs"]
    models.api_logs_collection = db["api_logs"]

    # Set up any indexes if needed
    models.users_collection.create_index("registration_number", unique=True)
    models.users_collection.create_index("email", unique=True)
    models.profiles_collection.create_index("registration_number", unique=True)

    return db