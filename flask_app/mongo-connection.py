# Create a test script (test_mongodb.py)
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_CLUSTER')}/{os.getenv('MONGO_DB_NAME')}?retryWrites=true&w=majority"

print(f"Attempting to connect to MongoDB...")
try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")

    # List collections to verify database access
    db = client[os.getenv('MONGO_DB_NAME')]
    collections = db.list_collection_names()
    print(f"Collections in database: {collections}")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")