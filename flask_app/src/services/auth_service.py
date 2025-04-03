"""Authentication related services"""
from models.models import admins_collection, users_collection


def is_admin(email):
    """Check if a user is an admin"""
    if not email:
        return False
    return admins_collection.find_one({"email": email}) is not None


def get_user_by_registration(reg_number):
    """Get user by registration number"""
    if not reg_number:
        return None
    return users_collection.find_one({"registration_number": reg_number})


def verify_user_credentials(reg_number, password, password_hash_func):
    """Verify user credentials"""
    user = get_user_by_registration(reg_number)
    if not user:
        return None, "User not found"

    # Check if account is locked
    if user.get("locked", False):
        return None, "Account is locked"

    # Check password - for compatibility we try both hashed and direct comparison
    if not password_hash_func(user.get('password', ''), password) and user.get('password') != password:
        return None, "Invalid password"

    return user, None