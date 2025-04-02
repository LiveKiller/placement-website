# Create a test script (test_api.py)
import requests
import json

BASE_URL = "http://localhost:5000/api"
admin_token = None
user_token = None


# Test function
def test_endpoint(method, endpoint, data=None, token=None, expected_status=200):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE_URL}/{endpoint}"

    if method.lower() == "get":
        response = requests.get(url, headers=headers)
    elif method.lower() == "post":
        response = requests.post(url, json=data, headers=headers)

    print(f"\nTesting {method.upper()} {endpoint}")
    print(f"Status: {response.status_code} (Expected: {expected_status})")

    if response.status_code != expected_status:
        print(f"❌ Test failed! Expected {expected_status}, got {response.status_code}")
        print(f"Response: {response.text}")
        return False, None

    print("✅ Test passed!")
    try:
        return True, response.json()
    except:
        return True, response.text


# 1. Admin Login (You need to create an admin user first)
print("\n=== TESTING ADMIN LOGIN ===")
admin_reg = input("Enter admin registration number: ")
admin_pass = input("Enter admin password: ")
success, result = test_endpoint("post", "login", {"registration_number": admin_reg, "password": admin_pass})
if success:
    admin_token = result.get("access_token")
    print(f"Admin token: {admin_token[:10]}...")

# 2. Test adding a user
print("\n=== TESTING ADD USER ===")
new_user = {
    "registration_number": "TEST002",
    "email": "test2@example.com",
    "password": "TEST0_xamp",
    "department": "Computer Science",
    "course": "B.Tech"
}
test_endpoint("post", "admin/add-user", new_user, admin_token)

# 3. Test user login
print("\n=== TESTING USER LOGIN ===")
# The default password should be TEST0_xamp
success, result = test_endpoint("post", "login", {"registration_number": "TEST002", "password": "TEST0_xamp"})
if success:
    user_token = result.get("access_token")
    print(f"User token: {user_token[:10]}...")

# 4. Test profile completion
print("\n=== TESTING PROFILE COMPLETION ===")
profile_data = {
    "personal_details": {
        "full_name": "Test User",
        "date_of_birth": "2000-01-01",
        "email": "test2@example.com",
        "phone_number": "1234567890",
        "address": "123 Test St"
    },
    "academic_details": {
        "registration_number": "TEST002",
        "department": "Computer Science",
        "course": "B.Tech",
        "year_of_study": "3",
        "cgpa": "8.5",
        "skills": ["Python", "JavaScript"],
        "certifications": ["AWS Certified"],
        "resume_link": "https://example.com/resume"
    },
    "internship_experience": {
        "preferred_internship_domain": "Web Development",
        "preferred_companies": ["Google", "Microsoft"],
        "previous_internships": [
            {"company": "TechCorp", "duration": "3 months", "role": "Intern", "description": "Developed web apps"}],
        "projects": [{"title": "Project 1", "description": "Test project", "technologies": ["React", "Node.js"],
                      "link": "https://github.com/test"}]
    },
    "additional_information": {
        "linkedin_profile": "https://linkedin.com/in/test",
        "github_profile": "https://github.com/test"
    }
}
test_endpoint("post", "complete-profile", profile_data, user_token)

# 5. Test profile retrieval
print("\n=== TESTING PROFILE RETRIEVAL ===")
test_endpoint("get", "profile", token=user_token)

# 6. Test password change
print("\n=== TESTING PASSWORD CHANGE ===")
password_data = {
    "current_password": "TEST0_xamp",
    "new_password": "NewPassword123",
    "confirm_password": "NewPassword123"
}
test_endpoint("post", "change-password", password_data, user_token)

# 7. Test login with new password
print("\n=== TESTING LOGIN WITH NEW PASSWORD ===")
test_endpoint("post", "login", {"registration_number": "TEST001", "password": "NewPassword123"})

print("\n=== TESTING COMPLETE ===")