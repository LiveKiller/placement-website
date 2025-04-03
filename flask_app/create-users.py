import datetime

import pandas as pd
from werkzeug.security import generate_password_hash
from database import db


def create_users_from_file(file_path):
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            return False, "Unsupported file format"

        users = []
        for _, row in df.iterrows():
            users.append({
                "registration_number": str(row['registration_number']),
                "email": row['email'],
                "password": generate_password_hash(str(row['registration_number'])),
                "department": row['department'],
                "course": row['course'],
                "created_at": datetime.now(),
                "profile_completed": False,
                "default_password": True
            })

        result = db.users.insert_many(users)
        return True, f"Successfully created {len(result.inserted_ids)} users"

    except Exception as e:
        return False, str(e)
