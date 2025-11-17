from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from bson import ObjectId
import secrets
import re


class SSPIUserData(MongoWrapper):
    """
    MongoDB wrapper for user authentication data.
    
    Handles user document validation, CRUD operations, and authentication queries
    following the established SSPI wrapper pattern.
    """
    
    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Validates user document format with authentication-specific requirements.

        Expected document format:
        {
            "username": "admin",          # str, 4-20 chars, alphanumeric + underscore
            "password": "hashed_password", # str, bcrypt hash
            "apikey": "api_key_string",   # str, 128 chars hex
            "secretkey": "secret_string",  # str, 64 chars hex
            "roles": ["user"]             # list of str, valid roles: "user", "admin"
        }
        """
        self.validate_username(document, document_number)
        self.validate_password_hash(document, document_number)
        self.validate_api_key(document, document_number)
        self.validate_secret_key(document, document_number)
        self.validate_roles(document, document_number)
    
    def validate_username(self, document: dict, document_number: int = 0):
        """Validates username format and requirements."""
        if "username" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'username' is a required field (document {document_number})"
            )
        
        username = document["username"]
        if not isinstance(username, str):
            raise InvalidDocumentFormatError(
                f"'username' must be a string (document {document_number})"
            )
        
        if not (4 <= len(username) <= 20):
            raise InvalidDocumentFormatError(
                f"'username' must be 4-20 characters long (document {document_number})"
            )
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise InvalidDocumentFormatError(
                f"'username' can only contain letters, numbers, and underscores (document {document_number})"
            )
    
    def validate_password_hash(self, document: dict, document_number: int = 0):
        """Validates password hash format."""
        if "password" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'password' is a required field (document {document_number})"
            )
        
        password = document["password"]
        if not isinstance(password, str):
            raise InvalidDocumentFormatError(
                f"'password' must be a string (document {document_number})"
            )
        
        # Bcrypt hashes should be 60 characters and start with $2b$
        if not password.startswith('$2b$') or len(password) != 60:
            raise InvalidDocumentFormatError(
                f"'password' must be a valid bcrypt hash (document {document_number})"
            )
    
    def validate_api_key(self, document: dict, document_number: int = 0):
        """Validates API key format."""
        if "apikey" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'apikey' is a required field (document {document_number})"
            )
        
        apikey = document["apikey"]
        if not isinstance(apikey, str):
            raise InvalidDocumentFormatError(
                f"'apikey' must be a string (document {document_number})"
            )
        
        if len(apikey) != 128:  # 64 bytes as hex = 128 chars
            raise InvalidDocumentFormatError(
                f"'apikey' must be 128 characters long (document {document_number})"
            )
        
        if not re.match(r'^[a-f0-9]+$', apikey):
            raise InvalidDocumentFormatError(
                f"'apikey' must be a valid hexadecimal string (document {document_number})"
            )
    
    def validate_secret_key(self, document: dict, document_number: int = 0):
        """Validates secret key format."""
        if "secretkey" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'secretkey' is a required field (document {document_number})"
            )

        secretkey = document["secretkey"]
        if not isinstance(secretkey, str):
            raise InvalidDocumentFormatError(
                f"'secretkey' must be a string (document {document_number})"
            )

        if len(secretkey) != 64:  # 32 bytes as hex = 64 chars
            raise InvalidDocumentFormatError(
                f"'secretkey' must be 64 characters long (document {document_number})"
            )

        if not re.match(r'^[a-f0-9]+$', secretkey):
            raise InvalidDocumentFormatError(
                f"'secretkey' must be a valid hexadecimal string (document {document_number})"
            )

    def validate_roles(self, document: dict, document_number: int = 0):
        """Validates roles format and requirements."""
        if "roles" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'roles' is a required field (document {document_number})"
            )

        roles = document["roles"]
        if not isinstance(roles, list):
            raise InvalidDocumentFormatError(
                f"'roles' must be a list (document {document_number})"
            )

        if len(roles) == 0:
            raise InvalidDocumentFormatError(
                f"'roles' cannot be empty (document {document_number})"
            )

        valid_roles = ["user", "admin"]
        for role in roles:
            if not isinstance(role, str):
                raise InvalidDocumentFormatError(
                    f"Each role must be a string (document {document_number})"
                )
            if role not in valid_roles:
                raise InvalidDocumentFormatError(
                    f"Invalid role '{role}'. Valid roles are: {', '.join(valid_roles)} (document {document_number})"
                )

    def find_by_username(self, username: str) -> dict:
        return self.find_one({"username": username}, options={})  # Include _id
    
    def find_by_api_key(self, api_key: str) -> dict:
        return self.find_one({"apikey": api_key}, options={})  # Include _id
    
    def find_by_id(self, user_id: str) -> dict:
        try:
            return self.find_one({"_id": ObjectId(user_id)}, options={})  # Include _id
        except Exception:
            return {}
    
    def create_user(self, username: str, password_hash: str, api_key: str|None = None, secret_key: str|None = None, roles: list|None = None) -> str:
        """
        Create a new user with validation.

        Args:
            username: Unique username
            password_hash: Bcrypt hashed password
            api_key: Optional API key (generates if not provided)
            secret_key: Optional secret key (generates if not provided)
            roles: Optional roles list (defaults to ["user"])

        Returns:
            String representation of created user's ObjectId

        Raises:
            InvalidDocumentFormatError: If validation fails
            DuplicateKeyError: If username already exists
        """
        # Generate keys if not provided
        if api_key is None:
            api_key = secrets.token_hex(64)
        if secret_key is None:
            secret_key = secrets.token_hex(32)
        if roles is None:
            roles = ["user"]
        user_doc = {
            "username": username,
            "password": password_hash,
            "apikey": api_key,
            "secretkey": secret_key,
            "roles": roles
        }
        self.validate_document_format(user_doc)
        existing_user = self.find_by_username(username)
        if existing_user:
            raise InvalidDocumentFormatError(f"Username '{username}' already exists")
        result = self._mongo_database.insert_one(user_doc)
        return str(result.inserted_id)
    
    def update_password(self, user_id: str, new_password_hash: str) -> bool:
        try:
            # Validate password hash format
            temp_doc = {"password": new_password_hash, "username": "temp", "apikey": "a"*128, "secretkey": "b"*64, "roles": ["user"]}
            self.validate_password_hash(temp_doc)
            
            result = self._mongo_database.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password": new_password_hash}}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def regenerate_api_key(self, user_id: str) -> str:
        try:
            new_api_key = secrets.token_hex(64)
            result = self._mongo_database.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"apikey": new_api_key}}
            )
            return new_api_key if result.modified_count > 0 else ""
        except Exception:
            return ""
    
    def username_exists(self, username: str) -> bool:
        return self.count_documents({"username": username}) > 0
    
    def get_all_users(self) -> list:
        return self.find({}, options={})  # Include _id
    
    def delete_user(self, user_id: str) -> bool:
        try:
            result = self._mongo_database.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    def get_user_roles(self, user_id: str) -> list:
        """
        Get the roles for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of role strings (e.g., ["user"] or ["admin", "user"])
            Returns empty list if user not found
        """
        try:
            user = self.find_by_id(user_id)
            return user.get("roles", []) if user else []
        except Exception:
            return []

    def add_role(self, user_id: str, role: str) -> bool:
        """
        Add a role to a user (if they don't already have it).

        Args:
            user_id: User identifier
            role: Role to add (must be "user" or "admin")

        Returns:
            True if role was added, False otherwise
        """
        valid_roles = ["user", "admin"]
        if role not in valid_roles:
            return False

        try:
            result = self._mongo_database.update_one(
                {"_id": ObjectId(user_id)},
                {"$addToSet": {"roles": role}}  # $addToSet prevents duplicates
            )
            return result.modified_count > 0
        except Exception:
            return False

    def remove_role(self, user_id: str, role: str) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: User identifier
            role: Role to remove

        Returns:
            True if role was removed, False otherwise
        """
        try:
            result = self._mongo_database.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"roles": role}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def set_roles(self, user_id: str, roles: list) -> bool:
        """
        Replace a user's roles entirely.

        Args:
            user_id: User identifier
            roles: List of roles to set (e.g., ["admin", "user"])

        Returns:
            True if roles were updated, False otherwise
        """
        # Validate roles format
        temp_doc = {"username": "temp", "password": "$2b$" + "0" * 57, "apikey": "a"*128, "secretkey": "b"*64, "roles": roles}
        try:
            self.validate_roles(temp_doc)
        except InvalidDocumentFormatError:
            return False

        try:
            result = self._mongo_database.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"roles": roles}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def create_indexes(self):
        # Unique index on username
        self._mongo_database.create_index("username", unique=True)
