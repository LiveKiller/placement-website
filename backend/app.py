from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db, User, Student, Faculty, HiringManager, Internship, Application

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Setup Admin
    admin = Admin(app, name="Internship Portal Admin", template_mode="bootstrap3")
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Student, db.session))
    admin.add_view(ModelView(Faculty, db.session))
    admin.add_view(ModelView(HiringManager, db.session))
    admin.add_view(ModelView(Internship, db.session))
    admin.add_view(ModelView(Application, db.session))
    
    # Register blueprints
# In app.py
    from routes.student import student_bp
    from routes.faculty import faculty_bp
    from routes.hiring import hiring_bp
    from routes.auth import auth_bp
    from routes.common import common_bp

    # When registering blueprints, add unique names
    app.register_blueprint(student_bp, url_prefix='/api/student', name='student_api')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty', name='faculty_api')
    app.register_blueprint(hiring_bp, url_prefix='/api/hiring', name='hiring_api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth', name='auth_api')
    app.register_blueprint(common_bp, url_prefix='/', name='common_routes')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)