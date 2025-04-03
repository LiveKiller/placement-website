# Student Profile System API

A Flask-based REST API for managing student profiles, built with MongoDB for data storage.

## Project Structure

```
student_profile_system/
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Dependencies
├── .env.example            # Example environment variables
├── logs/                   # Log directory
├── models/                 # Database models
│   ├── __init__.py
│   └── models.py           # MongoDB collections and schema definitions
├── routes/                 # API routes
│   ├── __init__.py
│   ├── admin_routes.py     # Admin-specific routes
│   ├── auth_routes.py      # Authentication routes
│   ├── profile_routes.py   # Profile management routes
│   └── utility_routes.py   # Utility endpoints
├── services/               # Business logic
│   ├── __init__.py
│   ├── admin_service.py    # Admin-related operations
│   ├── auth_service.py     # Authentication operations
│   └── profile_service.py  # Profile management operations
└── utils/                  # Utility functions
    ├── __init__.py
    ├── db_utils.py         # Database utilities
    ├── logging_utils.py    # Logging utilities
    └── validation_utils.py # Validation functions
```

## Features

- User authentication with JWT
- Profile management for students
- Admin features for user management
- File import for batch user creation
- Password management
- Comprehensive logging and error handling

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd student_profile_system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. Run the application:
```bash
python app.py
```

## Environment Variables

- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT secret key for token generation
- `DEBUG`: Enable debug mode (True/False)
- `PORT`: Port to run the application
- `MONGO_USER`: MongoDB username
- `MONGO_PASSWORD`: MongoDB password
- `MONGO_CLUSTER`: MongoDB cluster URL
- `MONGO_DB_NAME`: MongoDB database name
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `LOG_FILE`: Path to log file

## API Endpoints

### Authentication

- `POST /api/login`: User login
- `POST /api/change-password`: Change user password
- `GET /api/check-admin`: Check if user is an admin

### Profile Management

- `POST /api/complete-profile`: Complete or update user profile
- `GET /api/profile`: Get user's own profile
- `GET /api/profile/<registration_number>`: Get another user's profile (admin only)
- `GET /api/check-profile-status`: Check if user has completed profile

### Admin Operations

- `POST /api/admin/create-admin`: Create a new admin user
- `POST /api/admin/import-users`: Import multiple users from Excel/CSV
- `POST /api/admin/add-user`: Add a single user
- `GET /api/admin/list-users`: List all users with pagination
- `POST /api/reset-password`: Reset a user's password to default

### Utility

- `GET /api/health`: Health check endpoint

## User Model

- `registration_number`: Unique identifier
- `email`: User email
- `password`: Hashed password
- `department`: Department name
- `course`: Course name
- `created_at`: Creation timestamp
- `profile_completed`: Profile completion status
- `default_password`: Whether user has default password
- `created_by`: Admin who created the user

## Profile Model

The profile contains several sections:

### Personal Details
- `full_name`
- `date_of_birth`
- `email`
- `phone_number`
- `address`

### Academic Details
- `registration_number` (Primary Key)
- `department`
- `course`
- `year_of_study`
- `cgpa`
- `skills`
- `certifications`
- `resume_link`
- `research_papers` (optional)

### Internship Experience
- `preferred_internship_domain`
- `preferred_companies`
- `previous_internships`
- `projects`
- `work_experience` (optional)

### Additional Information
- `linkedin_profile`
- `github_profile`
- `portfolio_website` (optional)

## Security Features

- Password hashing using Werkzeug's PBKDF2
- JWT authentication
- Admin privilege checking
- Request logging for audit purposes
- Error logging with tracebacks

## Error Handling

The application includes a global error handler that logs errors to both file and database, providing error IDs for debugging.