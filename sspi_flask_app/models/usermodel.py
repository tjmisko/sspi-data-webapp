from flask_login import UserMixin
from sspi_flask_app.models.database import sspi_user_data


class User(UserMixin):
    """
    MongoDB-based User model for Flask-Login authentication.
    """
    
    def __init__(self, user_doc):
        """
        Initialize User from MongoDB document.

        Args:
            user_doc: Dictionary containing user data from MongoDB
        """
        if user_doc is None:
            raise ValueError("User document cannot be None")

        # Handle ObjectId format from json_util.dumps
        if isinstance(user_doc['_id'], dict) and '$oid' in user_doc['_id']:
            self.id = user_doc['_id']['$oid']
        else:
            self.id = str(user_doc['_id'])
        self.username = user_doc['username']
        self.email = user_doc.get('email', None)  # Optional field for backwards compatibility
        self.password = user_doc['password']
        self.secretkey = user_doc['secretkey']
        # self.roles = user_doc['roles']
        if 'roles' in user_doc:
            self.roles = user_doc['roles']
        elif 'role' in user_doc:
            self.roles = [user_doc['role']]
        else:
            self.roles = []
        self.apikey = user_doc['apikey']
    
    def get_id(self):
        return self.id
    
    @staticmethod
    def find_by_username(username):
        user_doc = sspi_user_data.find_by_username(username)
        return User(user_doc) if user_doc else None
    
    @staticmethod
    def find_by_api_key(api_key):
        user_doc = sspi_user_data.find_by_api_key(api_key)
        return User(user_doc) if user_doc else None
    
    @staticmethod
    def find_by_id(user_id):
        user_doc = sspi_user_data.find_by_id(user_id)
        return User(user_doc) if user_doc else None
    
    @staticmethod
    def create_user(username, password_hash, email=None, api_key=None, secret_key=None, roles=None):
        user_id = sspi_user_data.create_user(username, password_hash, email, api_key, secret_key, roles)
        user_doc = sspi_user_data.find_by_id(user_id)
        return User(user_doc)
    
    @staticmethod
    def username_exists(username):
        return sspi_user_data.username_exists(username)

    @staticmethod
    def email_exists(email):
        return sspi_user_data.email_exists(email)
    
    def update_password(self, new_password_hash):
        success = sspi_user_data.update_password(self.id, new_password_hash)
        if success:
            self.password = new_password_hash
        return success
    
    def regenerate_api_key(self):
        new_api_key = sspi_user_data.regenerate_api_key(self.id)
        if new_api_key:
            self.apikey = new_api_key
        return new_api_key
    
    @staticmethod
    def get_all_users():
        user_docs = sspi_user_data.get_all_users()
        return [User(doc) for doc in user_docs]
    
    def delete(self):
        return sspi_user_data.delete_user(self.id)

    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            role: Role to check (e.g., "admin", "user")

        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles

    def is_admin(self) -> bool:
        """
        Check if user has admin role.

        Returns:
            True if user is an admin, False otherwise
        """
        return "admin" in self.roles

    def add_role(self, role: str) -> bool:
        """
        Add a role to this user.

        Args:
            role: Role to add (must be "user" or "admin")

        Returns:
            True if role was added, False otherwise
        """
        success = sspi_user_data.add_role(self.id, role)
        if success and role not in self.roles:
            self.roles.append(role)
        return success

    def remove_role(self, role: str) -> bool:
        """
        Remove a role from this user.

        Args:
            role: Role to remove

        Returns:
            True if role was removed, False otherwise
        """
        success = sspi_user_data.remove_role(self.id, role)
        if success and role in self.roles:
            self.roles.remove(role)
        return success

    def __repr__(self):
        """String representation of User object."""
        return f'<User {self.username}>'
