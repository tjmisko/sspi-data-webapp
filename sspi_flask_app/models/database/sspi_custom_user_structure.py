from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from datetime import datetime, timezone
import secrets
import re


class SSPICustomUserStructure(MongoWrapper):
    """
    MongoDB wrapper for user-defined SSPI configurations.

    Stores custom SSPI structures using the metadata format (SSPI, Pillars, Categories, Indicators).
    Enforces user isolation - users can only see and modify their own configurations.

    Document format:
    {
        "config_id": "unique_hex_string", # create if missing by hashing the metadata field
        "name": "My Custom SSPI",
        "username": "",  # REQUIRED - enforces ownership
        "public": "", # Boolean
        "metadata": [...],  # Array of SSPI metadata items (same format as item_details())
        "actions": [...], # Array of actions exported from action history
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z"
    }
    """

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Validates configuration document format.

        All validation delegates to simpler validators or reuses existing metadata validation.
        """
        self.validate_config_id(document, document_number)
        self.validate_config_name(document, document_number)
        self.validate_username(document, document_number)
        self.validate_metadata(document, document_number)
        self.validate_timestamps(document, document_number)

    def validate_config_id(self, document: dict, document_number: int = 0):
        pass

    def validate_config_name(self, document: dict, document_number: int = 0):
        pass

    def validate_username(self, document: dict, document_number: int = 0):
        pass

    def validate_metadata(self, document: dict, document_number: int = 0):
        pass # think hard about how to implement! Format provided by SSPI Metadata Item Details

    def validate_timestamps(self, document: dict, document_number: int = 0):
        pass

    def generate_config_id(self) -> str:
        pass # hash the metadata with username
        # fail if that configuration id already exists (user has already saved the exact same metadata) 
        # return a helpful message 


    def config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists."""
        return self.count_documents({"config_id": config_id}) > 0

    def verify_ownership(self, config_id: str, username: str) -> bool:
        """
        Verify that a user owns a specific configuration.

        Args:
            config_id: Configuration identifier
            username: User identifier

        Returns:
            True if user owns the configuration, False otherwise
        """
        if not username:
            return False
        return self.count_documents({"config_id": config_id, "username": username}) > 0

    # CRUD operations with user isolation
    def create_config(self, name: str, metadata: list, username: str) -> str:
        """
        Create a new custom configuration.

        Args:
            name: Human-readable name for the configuration
            metadata: Array of SSPI metadata items (SSPI, Pillars, Categories, Indicators)
            username: User identifier (REQUIRED)

        Returns:
            The generated config_id

        Raises:
            ValueError: If username is not provided
            InvalidDocumentFormatError: If validation fails
        """
        if not username:
            raise ValueError("username is required to create a configuration")

        config_id = self.generate_config_id()

        # Ensure unique config_id
        while self.config_exists(config_id):
            config_id = self.generate_config_id()

        now = datetime.now(timezone.utc).isoformat()

        config_doc = {
            "config_id": config_id,
            "name": name,
            "username": username,
            "metadata": metadata,
            "created_at": now,
            "updated_at": now
        }

        # Validate the document
        self.validate_document_format(config_doc)

        # Insert the document
        self.insert_one(config_doc)

        return config_id

    def find_by_config_id(self, config_id: str, username: str = None, is_admin: bool = False) -> dict:
        """
        Find configuration by config_id.

        Args:
            config_id: Configuration identifier
            username: User identifier (optional, but recommended for ownership verification)
            is_admin: If True, bypass ownership check (admin can access any config)

        Returns:
            Configuration document or None if not found

        Note: If username is provided and is_admin is False, only returns config if user owns it.
              If is_admin is True, returns config regardless of ownership.
        """
        query = {"config_id": config_id}
        # Only enforce ownership if not admin
        if username and not is_admin:
            query["username"] = username
        return self.find_one(query)

    def find_by_username(self, username: str) -> list:
        """
        Find all configurations for a specific user.

        Args:
            username: User identifier

        Returns:
            List of configuration documents owned by the user
        """
        if not username:
            return []
        return self.find({"username": username})

    def list_config_names(self, username: str = None, is_admin: bool = False) -> list:
        """
        Get list of configuration names for a specific user.

        Args:
            username: User identifier (optional if is_admin is True)
            is_admin: If True, return all configurations across all users

        Returns:
            List of dicts with config_id, name, and username (username included if admin)

        Raises:
            ValueError: If username is not provided and is_admin is False
        """
        if is_admin:
            # Admin can see all configs across all users
            configs = self.find({}, {"_id": 0, "config_id": 1, "name": 1, "username": 1})
            return configs
        else:
            # Regular user can only see their own configs
            if not username:
                raise ValueError("username is required to list configurations")
            configs = self.find({"username": username}, {"_id": 0, "config_id": 1, "name": 1})
            return configs

    def update_config(self, config_id: str, username: str, updates: dict, is_admin: bool = False) -> bool:
        """
        Update an existing configuration.

        Args:
            config_id: Configuration identifier
            username: User identifier (REQUIRED for ownership verification)
            updates: Dictionary of fields to update
            is_admin: If True, bypass ownership check (admin can update any config)

        Returns:
            True if update successful, False otherwise

        Raises:
            ValueError: If username is not provided
            PermissionError: If user doesn't own the configuration (unless admin)
        """
        if not username:
            raise ValueError("username is required to update a configuration")

        # Verify ownership (skip if admin)
        if not is_admin and not self.verify_ownership(config_id, username):
            raise PermissionError(
                f"User {username} does not have permission to modify configuration {config_id}"
            )

        # Get existing config (admin can get any config)
        existing_config = self.find_by_config_id(config_id, username, is_admin=is_admin)
        if not existing_config:
            return False

        # Prepare update document
        update_doc = existing_config.copy()
        update_doc.update(updates)
        update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Ensure username cannot be changed via updates (keep original owner)
        update_doc["username"] = existing_config["username"]

        # Validate the updated document
        self.validate_document_format(update_doc)

        # Update in database (use original username for the query, not the requesting user)
        result = self._mongo_database.update_one(
            {"config_id": config_id},
            {"$set": update_doc}
        )

        return result.modified_count > 0

    def delete_config(self, config_id: str, username: str, is_admin: bool = False) -> bool:
        """
        Delete a configuration.

        Args:
            config_id: Configuration identifier
            username: User identifier (REQUIRED for ownership verification)
            is_admin: If True, bypass ownership check (admin can delete any config)

        Returns:
            True if deletion successful, False otherwise

        Raises:
            ValueError: If username is not provided
            PermissionError: If user doesn't own the configuration (unless admin)
        """
        if not username:
            raise ValueError("username is required to delete a configuration")

        # Verify ownership (skip if admin)
        if not is_admin and not self.verify_ownership(config_id, username):
            raise PermissionError(
                f"User {username} does not have permission to delete configuration {config_id}"
            )

        # Admin can delete any config, regular user can only delete their own
        if is_admin:
            result = self.delete_one({"config_id": config_id})
        else:
            result = self.delete_one({"config_id": config_id, "username": username})
        return result > 0

    def duplicate_config(self, config_id: str, username: str, new_name: str, is_admin: bool = False) -> str:
        """
        Create a copy of an existing configuration.

        Args:
            config_id: Source configuration identifier
            username: User identifier (REQUIRED - the user who will own the duplicate)
            new_name: Name for the new configuration
            is_admin: If True, can duplicate any config (admin bypass)

        Returns:
            The new config_id

        Raises:
            ValueError: If username is not provided
            PermissionError: If user doesn't own the source configuration (unless admin)
        """
        if not username:
            raise ValueError("username is required to duplicate a configuration")

        # Get source config (admin can duplicate any config)
        source_config = self.find_by_config_id(config_id, username, is_admin=is_admin)

        if not source_config:
            raise PermissionError(
                f"User {username} does not have permission to access configuration {config_id}"
            )

        # Create new config with same metadata, owned by the requesting user
        return self.create_config(
            name=new_name,
            metadata=source_config["metadata"],
            username=username
        )



    def create_indexes(self):
        """Create database indexes for performance and uniqueness."""
        # Unique index on config_id
        self._mongo_database.create_index("config_id", unique=True)
        # Compound index on username + config_id for ownership checks
        self._mongo_database.create_index([("username", 1), ("config_id", 1)])
        # Index on username for listing user's configs
        self._mongo_database.create_index("username")
