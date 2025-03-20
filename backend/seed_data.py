# seed_data.py
import os
import sys
from datetime import datetime, timedelta
from random import choice, randint, sample
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import create_app
from models import db, User, Student, Faculty, HiringManager, Internship, Application

def create_sample_data():
    """Create sample data for the database"""
    print("Creating sample data...")
    
    # Create an application context
    app = create_app()
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create users
        create_users()
        
        # Create internships
        create_internships()
        
        # Create applications
        create_applications()
        
        print("Sample data created successfully!")

def create_users():
    """Create sample users"""
    print("Creating users...")
    
    # Create students
    student_data = [
        {
            'email': 'student1@example.com',
            'password': 'password123',
            'full_name': 'John Doe',
            'course': 'Computer Science',
            'department': 'Computer Engineering',
            'cgpa': 8.5,
            'skills': 'Python,Java,Web Development'
        },
        {
            'email': 'student2@example.com',
            'password': 'password123',
            'full_name': 'Jane Smith',
            'course': 'Electronics Engineering',
            'department': 'Electronics and Communication',
            'cgpa': 9.0,
            'skills': 'Circuit Design,Embedded Systems,IoT'
        },
        {
            'email': 'student3@example.com',
            'password': 'password123',
            'full_name': 'Michael Johnson',
            'course': 'Information Technology',
            'department': 'Computer Engineering',
            'cgpa': 7.8,
            'skills': 'JavaScript,React,Node.js'
        },
        {
            'email': 'student4@example.com',
            'password': 'password123',
            'full_name': 'Emily Brown',
            'course': 'Mechanical Engineering',
            'department': 'Mechanical Engineering',
            'cgpa': 8.2,
            'skills': 'CAD,3D Modeling,Product Design'
        },
        {
            'email': 'student5@example.com',
            'password': 'password123',
            'full_name': 'David Wilson',
            'course': 'Data Science',
            'department': 'Computer Engineering',
            'cgpa': 9.2,
            'skills': 'Machine Learning,Data Analysis,SQL,Python'
        }
    ]
    
    for data in student_data:
        # Create User instance first
        user = User(email=data['email'], role='student', created_at=datetime.now())
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # Create Student instance using correct fields from your model
        student = Student(
            user_id=user.id,
            full_name=data['full_name'],
            course=data['course'],
            department=data['department'],
            cgpa=data['cgpa'],
            skills=data['skills']
        )
        db.session.add(student)
        print(f"Created student with ID: {student.id}")
    
    # Create faculty
    faculty_data = [
        {
            'email': 'faculty1@example.com',
            'password': 'faculty123',
            'full_name': 'Dr. Robert Chen',
            'department': 'Computer Engineering',
            'position': 'Professor'
        },
        {
            'email': 'faculty2@example.com',
            'password': 'faculty123',
            'full_name': 'Dr. Sarah Williams',
            'department': 'Electronics and Communication',
            'position': 'Associate Professor'
        },
        {
            'email': 'faculty3@example.com',
            'password': 'faculty123',
            'full_name': 'Dr. James Miller',
            'department': 'Mechanical Engineering',
            'position': 'Assistant Professor'
        }
    ]
    
    for data in faculty_data:
        # Create User instance using set_password method as we did with students
        user = User(email=data['email'], role='faculty', created_at=datetime.now())
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # Create Faculty instance with only the fields that exist in your model
        faculty = Faculty(
            user_id=user.id,
            full_name=data['full_name'],
            department=data['department'],
            position=data['position']  # Include position since it's in your model
        )
        db.session.add(faculty)
    
    # Create hiring managers
    hiring_manager_data = [
        {
            'email': 'recruiter1@techcorp.com',
            'password': 'manager123',
            'company_name': 'TechCorp',
            'company_website': 'https://techcorp.com',
            'company_description': 'Leading technology solutions provider',
            'contact_number': '555-1234'
        },
        {
            'email': 'recruiter2@innovatesys.com',
            'password': 'manager123',
            'company_name': 'InnovateSys',
            'company_website': 'https://innovatesys.com',
            'company_description': 'Innovation-driven tech company',
            'contact_number': '555-2345'
        },
        {
            'email': 'recruiter3@futuretech.com',
            'password': 'manager123',
            'company_name': 'FutureTech',
            'company_website': 'https://futuretech.com',
            'company_description': 'Building the future of technology',
            'contact_number': '555-3456'
        },
        {
            'email': 'recruiter4@datawave.com',
            'password': 'manager123',
            'company_name': 'DataWave',
            'company_website': 'https://datawave.com',
            'company_description': 'Data analytics and solutions',
            'contact_number': '555-4567'
        }
    ]
    
    for data in hiring_manager_data:
        # Create User instance using set_password method
        user = User(email=data['email'], role='hiring_manager', created_at=datetime.now())
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # Create HiringManager instance with correct field names
        manager = HiringManager(
            user_id=user.id,
            company_name=data['company_name'],
            company_website=data['company_website'],
            company_description=data['company_description'],
            contact_number=data['contact_number']
        )
        db.session.add(manager)
    
    db.session.commit()

def create_internships():
    """Create sample internships"""
    print("Creating internships...")
    
    # Get hiring manager IDs
    managers = HiringManager.query.all()
    
    # Create internships
    internship_data = [
        {
            'title': 'Software Development Intern',
            'company': 'TechCorp',
            'location': 'New York, NY',
            'description': 'Join our team to develop cutting-edge software solutions. Gain hands-on experience with our tech stack and contribute to real projects.',
            'requirements': 'Knowledge of Python, JavaScript, and database concepts. Strong problem-solving skills.',
            'duration': '3 months',
            'stipend': '$1500/month',
            'manager_id': 1
        },
        {
            'title': 'Machine Learning Intern',
            'company': 'InnovateSys',
            'location': 'San Francisco, CA',
            'description': 'Work on exciting ML projects using state-of-the-art techniques. Help build and train models that solve real-world problems.',
            'requirements': 'Experience with Python, TensorFlow or PyTorch. Understanding of basic ML concepts.',
            'duration': '6 months',
            'stipend': '$2000/month',
            'manager_id': 2
        },
        {
            'title': 'Frontend Development Intern',
            'company': 'FutureTech',
            'location': 'Boston, MA',
            'description': 'Design and implement user interfaces for our web applications. Work closely with UX designers and backend developers.',
            'requirements': 'HTML, CSS, JavaScript, React or Angular experience. Eye for design and user experience.',
            'duration': '4 months',
            'stipend': '$1800/month',
            'manager_id': 3
        },
        {
            'title': 'Data Analysis Intern',
            'company': 'DataWave',
            'location': 'Chicago, IL',
            'description': 'Extract insights from large datasets. Create visualizations and reports to help drive business decisions.',
            'requirements': 'SQL, Python, data visualization tools. Strong analytical and problem-solving skills.',
            'duration': '3 months',
            'stipend': '$1700/month',
            'manager_id': 4
        },
        {
            'title': 'Embedded Systems Intern',
            'company': 'TechCorp',
            'location': 'Austin, TX',
            'description': 'Work on firmware development for IoT devices. Gain experience with hardware integration and optimization.',
            'requirements': 'C/C++ programming, basic electronics knowledge. Interest in embedded systems and IoT.',
            'duration': '5 months',
            'stipend': '$1900/month',
            'manager_id': 1
        },
        {
            'title': 'Cloud Infrastructure Intern',
            'company': 'InnovateSys',
            'location': 'Seattle, WA',
            'description': 'Help build and maintain cloud infrastructure. Learn about scalability, security, and DevOps practices.',
            'requirements': 'Basic knowledge of cloud services (AWS, Azure, or GCP). Linux command line experience.',
            'duration': '4 months',
            'stipend': '$2100/month',
            'manager_id': 2
        },
        {
            'title': 'UX/UI Design Intern',
            'company': 'FutureTech',
            'location': 'Remote',
            'description': 'Create user-centered designs for web and mobile applications. Conduct user research and usability testing.',
            'requirements': 'Experience with design tools like Figma or Adobe XD. Understanding of UI/UX principles.',
            'duration': '3 months',
            'stipend': '$1600/month',
            'manager_id': 3
        },
        {
            'title': 'Data Engineering Intern',
            'company': 'DataWave',
            'location': 'Denver, CO',
            'description': 'Build data pipelines and ETL processes. Work with big data technologies and databases.',
            'requirements': 'SQL, Python, and knowledge of data processing frameworks like Spark. Database experience.',
            'duration': '6 months',
            'stipend': '$2200/month',
            'manager_id': 4
        }
    ]
    
    for data in internship_data:
        internship = Internship(
            title=data['title'],
            company=data['company'],
            location=data['location'],
            description=data['description'],
            requirements=data['requirements'],
            duration=data['duration'],
            stipend=data['stipend'],
            posted_by=data['manager_id'],  # Changed to use posted_by to match your model
            created_at=datetime.now() - timedelta(days=randint(1, 30)),
            deadline=datetime.now() + timedelta(days=randint(10, 60)),
            is_active=True
        )
        db.session.add(internship)
    
    db.session.commit()

def create_applications():
    """Create sample applications"""
    print("Creating applications...")
    
    # Get student IDs
    students = Student.query.all()
    
    # Get internship IDs
    internships = Internship.query.all()
    internship_ids = [internship.id for internship in internships]
    
    # Create applications
    application_data = []
    status_options = ['pending', 'approved', 'rejected']
    
    # Each student applies to 2-4 internships
    for student in students:
        num_applications = randint(2, 4)
        internship_choices = sample(internship_ids, num_applications)
        
        for internship_id in internship_choices:
            application_data.append({
                'student_id': student.id,  # Use student.id, not user_id
                'internship_id': internship_id,
                'cover_letter': f'I am excited to apply for this internship opportunity as it aligns perfectly with my skills and career goals. I believe my academic background and previous projects make me a strong candidate for this position.',
                'status': choice(status_options),
                'faculty_approval': choice([True, False]),
                'hiring_approval': choice([True, False])
            })
    
    for data in application_data:
        application = Application(
            student_id=data['student_id'],
            internship_id=data['internship_id'],
            cover_letter=data['cover_letter'],
            status=data['status'],
            faculty_approval=data['faculty_approval'],
            hiring_approval=data['hiring_approval'],
            applied_at=datetime.now() - timedelta(days=randint(1, 20))
        )
        db.session.add(application)
    
    db.session.commit()

if __name__ == '__main__':
    create_sample_data()