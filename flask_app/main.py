from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
import hashlib
import urllib.parse
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

print(os.getenv('MONGO_USER'))  # Should print 'user-xxx'
print(os.getenv('MONGO_PASSWORD')) 
app = Flask(__name__)
CORS(app)
jwt = JWTManager(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

# Properly encode MongoDB credentials
username = urllib.parse.quote_plus(os.getenv('MONGO_USER'))
password = urllib.parse.quote_plus(os.getenv('MONGO_PASSWORD'))
host = os.getenv('MONGO_HOST')
db_name = os.getenv('MONGO_DB_NAME')

MONGO_URI = f"mongodb://{username}:{password}@{host}/{db_name}?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client[db_name]
users_collection = db["users"]
admins_collection = db["admins"]

def generate_username(email):
    hash_object = hashlib.sha256(email.encode())
    hash_hex = hash_object.hexdigest()
    numeric_filter = filter(str.isdigit, hash_hex)
    numeric_string = ''.join(numeric_filter)
    first_10_digits = numeric_string[:10]
    first_4_characters = hash_hex[:4]
    return f"anon{first_10_digits}{first_4_characters}"

def is_admin(email):
    return admins_collection.find_one({"email": email}) is not None

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match.', 'success': False}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({'message': 'Email already exists.', 'success': False}), 400

    username = generate_username(email)
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    users_collection.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_password,
        "username": username
    })

    access_token = create_access_token(identity=email)
    return jsonify({'message': 'User signed up successfully!', 'success': True, 'access_token': access_token, 'username': username}), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = users_collection.find_one({"email": email})

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid email or password.', 'success': False}), 401

    access_token = create_access_token(identity=email)
    return jsonify({'message': 'Logged in successfully!', 'success': True, 'access_token': access_token}), 200

@app.route('/api/check-admin', methods=['GET'])
@jwt_required()
def check_admin():
    user_email = get_jwt_identity()
    return jsonify({'is_admin': is_admin(user_email)}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
