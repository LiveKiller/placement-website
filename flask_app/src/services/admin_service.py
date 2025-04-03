"""Admin-related services"""
from services.auth_service import is_admin


def check_admin_privileges(user):
    """Check if a user has admin privileges"""
    if not user:
        return False

    return is_admin(user.get('email', ''))


def get_filtered_users(collection, filters=None, page=1, per_page=20, sort_by='created_at', sort_order=-1):
    """Get users with filters and pagination"""
    filters = filters or {}
    skip = (page - 1) * per_page

    users_cursor = collection.find(
        filters,
        {'password': 0}  # Exclude password
    ).sort(sort_by, sort_order).skip(skip).limit(per_page)

    total_users = collection.count_documents(filters)

    return list(users_cursor), total_users
