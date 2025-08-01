from flask_login import UserMixin
from sspi_flask_app.models.database import sspi_user_data


class User(UserMixin):
    """
    MongoDB-based User model for Flask-Login authentication.
    
    Replaces the previous SQLAlchemy-based User model with MongoDB backend
    using the SSPIUserData wrapper.
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
        self.password = user_doc['password']
        self.secretkey = user_doc['secretkey']
        self.apikey = user_doc['apikey']
    
    def get_id(self):
        """
        Return user ID for Flask-Login session management.
        
        Returns:
            String representation of MongoDB ObjectId
        """
        return self.id
    
    @staticmethod
    def find_by_username(username):
        """
        Find user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User object or None if not found
        """
        user_doc = sspi_user_data.find_by_username(username)
        return User(user_doc) if user_doc else None
    
    @staticmethod
    def find_by_api_key(api_key):
        """
        Find user by API key.
        
        Args:
            api_key: API key to search for
            
        Returns:
            User object or None if not found
        """
        user_doc = sspi_user_data.find_by_api_key(api_key)
        return User(user_doc) if user_doc else None
    
    @staticmethod
    def find_by_id(user_id):
        """
        Find user by MongoDB ObjectId.
        
        Args:
            user_id: String representation of ObjectId
            
        Returns:
            User object or None if not found
        """
        user_doc = sspi_user_data.find_by_id(user_id)
        return User(user_doc) if user_doc else None
    
    @staticmethod
    def create_user(username, password_hash, api_key=None, secret_key=None):
        """
        Create a new user.
        
        Args:
            username: Unique username
            password_hash: Bcrypt hashed password
            api_key: Optional API key (generates if not provided)
            secret_key: Optional secret key (generates if not provided)
            
        Returns:
            User object of created user
            
        Raises:
            InvalidDocumentFormatError: If validation fails or username exists
        """
        user_id = sspi_user_data.create_user(username, password_hash, api_key, secret_key)
        user_doc = sspi_user_data.find_by_id(user_id)
        return User(user_doc)
    
    @staticmethod
    def username_exists(username):
        """
        Check if username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if username exists, False otherwise
        """
        return sspi_user_data.username_exists(username)
    
    def update_password(self, new_password_hash):
        """
        Update user's password.
        
        Args:
            new_password_hash: New bcrypt hashed password
            
        Returns:
            True if update successful, False otherwise
        """
        success = sspi_user_data.update_password(self.id, new_password_hash)
        if success:
            self.password = new_password_hash
        return success
    
    def regenerate_api_key(self):
        """
        Generate new API key for user.
        
        Returns:
            New API key string or None if failed
        """
        new_api_key = sspi_user_data.regenerate_api_key(self.id)
        if new_api_key:
            self.apikey = new_api_key
        return new_api_key
    
    @staticmethod
    def get_all_users():
        """
        Get all users (for admin purposes).
        
        Returns:
            List of User objects
        """
        user_docs = sspi_user_data.get_all_users()
        return [User(doc) for doc in user_docs]
    
    def delete(self):
        """
        Delete this user.
        
        Returns:
            True if deletion successful, False otherwise
        """
        return sspi_user_data.delete_user(self.id)
    
    def __repr__(self):
        """String representation of User object."""
        return f'<User {self.username}>'
