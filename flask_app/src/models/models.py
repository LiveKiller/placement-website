"""MongoDB collections and schema definitions"""

# Collections are initialized in utils/db_utils.py
users_collection = None
admins_collection = None
profiles_collection = None
error_logs_collection = None
api_logs_collection = None

# Profile field requirements
REQUIRED_PROFILE_FIELDS = {
    "personal_details": [
        "full_name",
        "date_of_birth",
        "email",
        "phone_number",
        "address"
    ],
    "academic_details": [
        "registration_number",  # Primary Key
        "department",
        "course",
        "year_of_study",
        "cgpa",
        "skills",
        "certifications",
        "resume_link"
        # research_papers is optional
    ],
    "internship_experience": [
        "preferred_internship_domain",
        "preferred_companies",
        "previous_internships",
        "projects"
        # work_experience is optional
    ],
    "additional_information": [
        "linkedin_profile",
        "github_profile"
        # portfolio_website is optional
    ]
}