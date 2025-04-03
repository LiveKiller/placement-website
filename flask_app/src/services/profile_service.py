"""Profile management services"""
from datetime import datetime
from models.models import REQUIRED_PROFILE_FIELDS


def validate_profile_fields(profile_data):
    """Validate profile data against required fields"""
    missing_fields = {}

    for section, fields in REQUIRED_PROFILE_FIELDS.items():
        if section not in profile_data:
            missing_fields[section] = fields
            continue

        section_data = profile_data[section]
        missing_section_fields = [field for field in fields if field not in section_data or not section_data[field]]
        if missing_section_fields:
            missing_fields[section] = missing_section_fields

    return missing_fields or None


def get_user_profile(profile_collection, reg_number):
    """Get user profile and format it for API response"""
    profile = profile_collection.find_one({"registration_number": reg_number})
    if not profile:
        return None

    # Remove MongoDB _id field
    profile.pop('_id', None)

    # Convert datetime objects to strings
    for key in ['created_at', 'updated_at']:
        if key in profile and isinstance(profile[key], datetime):
            profile[key] = profile[key].isoformat()

    return profile


def create_or_update_profile(profile_collection, user, profile_data):
    """Create or update a user profile"""
    # Check if profile already exists
    reg_number = user["registration_number"]
    existing_profile = profile_collection.find_one({"registration_number": reg_number})

    # Prepare profile data
    updated_profile = {
        "registration_number": reg_number,
        "email": user.get('email'),
        "updated_at": datetime.now(),
        **profile_data
    }

    if existing_profile:
        # Update existing profile
        updated_profile["created_at"] = existing_profile.get("created_at")
        profile_collection.update_one(
            {"registration_number": reg_number},
            {"$set": updated_profile}
        )
    else:
        # Create new profile
        updated_profile["created_at"] = datetime.now()
        profile_collection.insert_one(updated_profile)

    return True