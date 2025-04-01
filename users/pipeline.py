from db.mongo import users_collection


def linkedin_auth(backend, user, response, *args, **kwargs):
    if backend.name == 'linkedin':
        # Extract LinkedIn data
        linkedin_data = {
            "linkedin_id": response.get('id'),
            "email": response.get('emailAddress'),
            "name": f"{response.get('firstName', {}).get('localized', {}).get('en_US')} {response.get('lastName', {}).get('localized', {}).get('en_US')}"
        }

        # Update or create user in MongoDB
        users_collection.update_one(
            {"email": linkedin_data['email']},
            {"$set": linkedin_data},
            upsert=True
        )