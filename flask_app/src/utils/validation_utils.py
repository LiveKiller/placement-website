"""Validation utility functions"""
from models.models import REQUIRED_PROFILE_FIELDS


def validate_profile_data(profile_data):
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

    return missing_fields