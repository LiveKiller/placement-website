from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
import hashlib
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Print environment variables for debugging (remove in production)
print(f"MONGO_USER: {os.getenv('MONGO_USER')}")
print(f"MONGO_PASSWORD: {os.getenv('MONGO_PASSWORD')}")
print(f"MONGO_CLUSTER: {os.getenv('MONGO_CLUSTER')}")
print(f"MONGO_DB_NAME: {os.getenv('MONGO_DB_NAME')}")

app = Flask(__name__)
CORS(app)
jwt = JWTManager(app)

# App configurations
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# MongoDB connection - using direct string construction without additional encoding
# The password is already encoded in the .env file
MONGO_URI = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_CLUSTER')}/{os.getenv('MONGO_DB_NAME')}?retryWrites=true&w=majority"

# Print connection string for debugging (remove in production)
print(f"Connection URI: {MONGO_URI}")

try:
    client = MongoClient(MONGO_URI)
    # Force a command to check if the connection is valid
    client.admin.command('ping')
    print("Connected successfully to MongoDB!")
    db = client[os.getenv('MONGO_DB_NAME')]
    users_collection = db["users"]
    admins_collection = db["admins"]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    # You might want to raise the exception here to prevent the app from starting
    # with a broken database connection

# Utility functions
def generate_username(email):
    hash_hex = hashlib.sha256(email.encode()).hexdigest()
    numeric_string = ''.join(filter(str.isdigit, hash_hex))[:10]
    return f"anon{numeric_string}{hash_hex[:4]}"

def is_admin(email):
    return admins_collection.find_one({"email": email}) is not None

# Routes
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    if not all(key in data for key in ['email', 'password', 'confirm_password']):
        return jsonify({'message': 'Missing required fields.', 'success': False}), 400
        
    if data.get('password') != data.get('confirm_password'):
        return jsonify({'message': 'Passwords do not match.', 'success': False}), 400
        
    if users_collection.find_one({"email": data.get('email')}):
        return jsonify({'message': 'Email already exists.', 'success': False}), 400
        
    username = generate_username(data['email'])
    users_collection.insert_one({
        "first_name": data.get('first_name', ''),
        "last_name": data.get('last_name', ''),
        "email": data['email'],
        "password": generate_password_hash(data['password'], method='pbkdf2:sha256'),
        "username": username
    })
    
    access_token = create_access_token(identity=data['email'])
    return jsonify({
        'message': 'User signed up successfully!', 
        'success': True, 
        'access_token': access_token, 
        'username': username
    }), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not all(key in data for key in ['email', 'password']):
        return jsonify({'message': 'Missing email or password.', 'success': False}), 400
        
    user = users_collection.find_one({"email": data.get('email')})
    if not user or not check_password_hash(user['password'], data.get('password')):
        return jsonify({'message': 'Invalid email or password.', 'success': False}), 401
        
    access_token = create_access_token(identity=data['email'])
    return jsonify({
        'message': 'Logged in successfully!', 
        'success': True, 
        'access_token': access_token,
        'username': user.get('username')
    }), 200

@app.route('/api/check-admin', methods=['GET'])
@jwt_required()
def check_admin():
    user_email = get_jwt_identity()
    return jsonify({'is_admin': is_admin(user_email)}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)