import requests
import json
import pandas as pd
import os
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000/api"
ADMIN_REG = "231302050"  # Admin registration number
ADMIN_PASSWORD = "admin@admin"  # Admin password
TEST_USER_REG = f"TEST{int(time.time())}"  # Generate unique test user
TEST_USER_EMAIL = f"test{int(time.time())}@example.com"

# For storing tokens
tokens = {}


def pretty_print_response(response):
    """Print response data in a readable format"""
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("-" * 50)


def run_test(name, method, endpoint, data=None, token=None, files=None, expected_status=200):
    """Run a test against the API"""
    print(f"\n[TEST] {name}")
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE_URL}{endpoint}"
    print(f"Request: {method} {url}")

    if data:
        print(f"Data: {json.dumps(data, indent=2)}")

    start_time = time.time()

    if method.upper() == "GET":
        response = requests.get(url, headers=headers)
    elif method.upper() == "POST":
        if files:
            response = requests.post(url, headers=headers, data=data, files=files)
        else:
            response = requests.post(url, headers=headers, json=data)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        print(f"Invalid method: {method}")
        return False

    end_time = time.time()
    duration = round((end_time - start_time) * 1000, 2)  # in ms

    print(f"Response time: {duration}ms")
    pretty_print_response(response)

    if response.status_code != expected_status:
        print(f"❌ Test failed! Expected status {expected_status}, got {response.status_code}")
        return False

    print(f"✅ Test passed!")
    return response.json() if response.text else {}


def create_test_excel():
    """Create a test Excel file for importing users"""
    df = pd.DataFrame({
        'registration_number': [f"TEST{int(time.time()) + i}" for i in range(1, 4)],
        'email': [f"test{int(time.time()) + i}@example.com" for i in range(1, 4)],
        'department': ['Computer Science', 'Electrical Engineering', 'Mechanical Engineering'],
        'course': ['B.Tech', 'M.Tech', 'PhD']
    })

    filename = 'test_users.xlsx'
    df.to_excel(filename, index=False)
    return filename


def create_sample_profile_data(reg_number):
    """Create sample profile data for testing"""
    return {
        "personal_details": {
            "full_name": "Test User",
            "date_of_birth": "1995-01-01",
            "email": f"test_{reg_number}@example.com",
            "phone_number": "1234567890",
            "address": "123 Test Street, Test City"
        },
        "academic_details": {
            "registration_number": reg_number,
            "department": "Computer Science",
            "course": "B.Tech",
            "year_of_study": "3",
            "cgpa": "8.5",
            "skills": "Python, JavaScript, MongoDB",
            "certifications": "AWS Certified Developer",
            "resume_link": "https://example.com/resume",
            "research_papers": "None"
        },
        "internship_experience": {
            "preferred_internship_domain": "Web Development",
            "preferred_companies": "Google, Microsoft, Amazon",
            "previous_internships": "None",
            "projects": "Student Profile Management System",
            "work_experience": "None"
        },
        "additional_information": {
            "linkedin_profile": "https://linkedin.com/in/testuser",
            "github_profile": "https://github.com/testuser",
            "portfolio_website": "https://testuser.com"
        }
    }


def run_tests():
    """Run a series of tests against the API"""
    test_results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "start_time": datetime.now().isoformat()
    }

    try:
        # Test health endpoint
        test_results["total"] += 1
        if run_test("Health Check", "GET", "/health"):
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1

        # Test admin login
        test_results["total"] += 1
        admin_login = run_test("Admin Login", "POST", "/login", {
            "registration_number": ADMIN_REG,
            "password": ADMIN_PASSWORD
        })

        if admin_login and admin_login.get("success"):
            test_results["passed"] += 1
            tokens["admin"] = admin_login.get("access_token")
        else:
            test_results["failed"] += 1
            print("⚠️ Admin login failed, subsequent admin tests will be skipped")

        # Test admin routes if we have an admin token
        if "admin" in tokens:
            # Test adding a single user
            test_results["total"] += 1
            add_user = run_test("Add User", "POST", "/admin/add-user", {
                "registration_number": TEST_USER_REG,
                "email": TEST_USER_EMAIL,
                "department": "Computer Science",
                "course": "B.Tech"
            }, tokens["admin"])

            if add_user and add_user.get("success"):
                test_results["passed"] += 1
                print(f"Created test user: {TEST_USER_REG}")
            else:
                test_results["failed"] += 1

            # Test importing users via Excel
            test_results["total"] += 1
            excel_file = create_test_excel()

            with open(excel_file, 'rb') as f:
                import_users = run_test(
                    "Import Users",
                    "POST",
                    "/admin/import-users",
                    {},
                    tokens["admin"],
                    {"file": (excel_file, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                )

            # Clean up Excel file
            try:
                os.remove(excel_file)
            except:
                pass

            if import_users and import_users.get("success"):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

            # Test list users
            test_results["total"] += 1
            if run_test("List Users", "GET", "/admin/list-users", None, tokens["admin"]):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

        # Test user login with newly created user
        test_results["total"] += 1
        user_login = run_test("User Login", "POST", "/login", {
            "registration_number": TEST_USER_REG,
            "password": TEST_USER_REG  # Default password is registration number
        })

        if user_login and user_login.get("success"):
            test_results["passed"] += 1
            tokens["user"] = user_login.get("access_token")
        else:
            test_results["failed"] += 1
            print("⚠️ User login failed, subsequent user tests will be skipped")

        # Test user routes if we have a user token
        if "user" in tokens:
            # Test check profile status
            test_results["total"] += 1
            if run_test("Check Profile Status", "GET", "/check-profile-status", None, tokens["user"]):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

            # Test change password
            test_results["total"] += 1
            change_password = run_test("Change Password", "POST", "/change-password", {
                "current_password": TEST_USER_REG,
                "new_password": f"{TEST_USER_REG}_new",
                "confirm_password": f"{TEST_USER_REG}_new"
            }, tokens["user"])

            if change_password and change_password.get("success"):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

            # Test complete profile
            test_results["total"] += 1
            complete_profile = run_test(
                "Complete Profile",
                "POST",
                "/complete-profile",
                create_sample_profile_data(TEST_USER_REG),
                tokens["user"]
            )

            if complete_profile and complete_profile.get("success"):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

            # Test get profile
            test_results["total"] += 1
            if run_test("Get Profile", "GET", "/profile", None, tokens["user"]):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

        # If we have both admin and user tokens, test admin viewing a user profile
        if "admin" in tokens and "user" in tokens:
            test_results["total"] += 1
            if run_test("Admin View User Profile", "GET", f"/profile/{TEST_USER_REG}", None, tokens["admin"]):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

            # Test password reset by admin
            test_results["total"] += 1
            reset_password = run_test("Reset User Password", "POST", "/reset-password", {
                "registration_number": TEST_USER_REG
            }, tokens["admin"])

            if reset_password and reset_password.get("success"):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1

    except Exception as e:
        print(f"❌ Test runner error: {str(e)}")

    # Update test results
    test_results["end_time"] = datetime.now().isoformat()
    test_results["duration_seconds"] = (datetime.fromisoformat(test_results["end_time"]) -
                                        datetime.fromisoformat(test_results["start_time"])).total_seconds()

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Success rate: {(test_results['passed'] / test_results['total']) * 100:.2f}%")
    print(f"Duration: {test_results['duration_seconds']:.2f} seconds")

    # Save results to file
    with open(f"test_results_{int(time.time())}.json", "w") as f:
        json.dump(test_results, f, indent=2)

    return test_results


if __name__ == "__main__":
    run_tests()