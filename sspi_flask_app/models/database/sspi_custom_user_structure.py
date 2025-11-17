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
        "config_id": "unique_hex_string",
        "name": "My Custom SSPI",
        "user_id": "user@email.com",  # REQUIRED - enforces ownership
        "metadata": [...],  # Array of SSPI metadata items (same format as item_details())
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    """

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Validates configuration document format.

        All validation delegates to simpler validators or reuses existing metadata validation.
        """
        self.validate_config_id(document, document_number)
        self.validate_config_name(document, document_number)
        self.validate_user_id(document, document_number)
        self.validate_metadata(document, document_number)
        self.validate_timestamps(document, document_number)

    def validate_config_id(self, document: dict, document_number: int = 0):
        """Validates config_id format and requirements."""
        if "config_id" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'config_id' is a required field (document {document_number})"
            )

        config_id = document["config_id"]
        if not isinstance(config_id, str):
            raise InvalidDocumentFormatError(
                f"'config_id' must be a string (document {document_number})"
            )

        if not (6 <= len(config_id) <= 64):
            raise InvalidDocumentFormatError(
                f"'config_id' must be 6-64 characters long (document {document_number})"
            )

        if not re.match(r'^[a-zA-Z0-9_]+$', config_id):
            raise InvalidDocumentFormatError(
                f"'config_id' can only contain letters, numbers, and underscores (document {document_number})"
            )

    def validate_config_name(self, document: dict, document_number: int = 0):
        """Validates config name format."""
        if "name" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'name' is a required field (document {document_number})"
            )

        name = document["name"]
        if not isinstance(name, str):
            raise InvalidDocumentFormatError(
                f"'name' must be a string (document {document_number})"
            )

        if not (1 <= len(name) <= 100):
            raise InvalidDocumentFormatError(
                f"'name' must be 1-100 characters long (document {document_number})"
            )

        if name.strip() != name:
            raise InvalidDocumentFormatError(
                f"'name' cannot have leading or trailing whitespace (document {document_number})"
            )

    def validate_user_id(self, document: dict, document_number: int = 0):
        """
        Validates user_id format - REQUIRED for user isolation.

        User ID must be present and non-empty to ensure ownership tracking.
        """
        if "user_id" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'user_id' is a required field (document {document_number})"
            )

        user_id = document["user_id"]

        if user_id is None or user_id == "":
            raise InvalidDocumentFormatError(
                f"'user_id' cannot be None or empty (document {document_number})"
            )

        if not isinstance(user_id, str):
            raise InvalidDocumentFormatError(
                f"'user_id' must be a string (document {document_number})"
            )

        if len(user_id.strip()) == 0:
            raise InvalidDocumentFormatError(
                f"'user_id' cannot be empty or whitespace (document {document_number})"
            )

    def validate_metadata(self, document: dict, document_number: int = 0):
        """
        Validates metadata array using existing metadata validation.

        Delegates to validate_custom_metadata() to avoid duplication.
        """
        if "metadata" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'metadata' is a required field (document {document_number})"
            )

        metadata = document["metadata"]

        if not isinstance(metadata, list):
            raise InvalidDocumentFormatError(
                f"'metadata' must be an array (document {document_number})"
            )

        # Import and use existing validation from customize.py
        from sspi_flask_app.api.core.customize import validate_custom_metadata

        validation = validate_custom_metadata(metadata)
        if not validation["valid"]:
            errors_str = "; ".join(validation["errors"])
            raise InvalidDocumentFormatError(
                f"Invalid metadata format (document {document_number}): {errors_str}"
            )

    def validate_timestamps(self, document: dict, document_number: int = 0):
        """Validates timestamp format."""
        timestamp_fields = ["created_at", "updated_at"]

        for field in timestamp_fields:
            if field not in document:
                raise InvalidDocumentFormatError(
                    f"'{field}' is a required field (document {document_number})"
                )

            timestamp = document[field]
            if not isinstance(timestamp, str):
                raise InvalidDocumentFormatError(
                    f"'{field}' must be an ISO datetime string (document {document_number})"
                )

            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                raise InvalidDocumentFormatError(
                    f"'{field}' must be a valid ISO datetime string (document {document_number})"
                )

    # Helper methods

    def generate_config_id(self) -> str:
        """Generate a unique configuration identifier."""
        return secrets.token_hex(8)  # 16 characters, hex (alphanumeric only)

    def config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists."""
        return self.count_documents({"config_id": config_id}) > 0

    def verify_ownership(self, config_id: str, user_id: str) -> bool:
        """
        Verify that a user owns a specific configuration.

        Args:
            config_id: Configuration identifier
            user_id: User identifier

        Returns:
            True if user owns the configuration, False otherwise
        """
        if not user_id:
            return False
        return self.count_documents({"config_id": config_id, "user_id": user_id}) > 0

    # CRUD operations with user isolation

    def create_config(self, name: str, metadata: list, user_id: str) -> str:
        """
        Create a new custom configuration.

        Args:
            name: Human-readable name for the configuration
            metadata: Array of SSPI metadata items (SSPI, Pillars, Categories, Indicators)
            user_id: User identifier (REQUIRED)

        Returns:
            The generated config_id

        Raises:
            ValueError: If user_id is not provided
            InvalidDocumentFormatError: If validation fails
        """
        if not user_id:
            raise ValueError("user_id is required to create a configuration")

        config_id = self.generate_config_id()

        # Ensure unique config_id
        while self.config_exists(config_id):
            config_id = self.generate_config_id()

        now = datetime.now(timezone.utc).isoformat()

        config_doc = {
            "config_id": config_id,
            "name": name,
            "user_id": user_id,
            "metadata": metadata,
            "created_at": now,
            "updated_at": now
        }

        # Validate the document
        self.validate_document_format(config_doc)

        # Insert the document
        self.insert_one(config_doc)

        return config_id

    def find_by_config_id(self, config_id: str, user_id: str = None, is_admin: bool = False) -> dict:
        """
        Find configuration by config_id.

        Args:
            config_id: Configuration identifier
            user_id: User identifier (optional, but recommended for ownership verification)
            is_admin: If True, bypass ownership check (admin can access any config)

        Returns:
            Configuration document or None if not found

        Note: If user_id is provided and is_admin is False, only returns config if user owns it.
              If is_admin is True, returns config regardless of ownership.
        """
        query = {"config_id": config_id}
        # Only enforce ownership if not admin
        if user_id and not is_admin:
            query["user_id"] = user_id
        return self.find_one(query)

    def find_by_user_id(self, user_id: str) -> list:
        """
        Find all configurations for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of configuration documents owned by the user
        """
        if not user_id:
            return []
        return self.find({"user_id": user_id})

    def list_config_names(self, user_id: str = None, is_admin: bool = False) -> list:
        """
        Get list of configuration names for a specific user.

        Args:
            user_id: User identifier (optional if is_admin is True)
            is_admin: If True, return all configurations across all users

        Returns:
            List of dicts with config_id, name, and user_id (user_id included if admin)

        Raises:
            ValueError: If user_id is not provided and is_admin is False
        """
        if is_admin:
            # Admin can see all configs across all users
            configs = self.find({}, {"_id": 0, "config_id": 1, "name": 1, "user_id": 1})
            return configs
        else:
            # Regular user can only see their own configs
            if not user_id:
                raise ValueError("user_id is required to list configurations")
            configs = self.find({"user_id": user_id}, {"_id": 0, "config_id": 1, "name": 1})
            return configs

    def update_config(self, config_id: str, user_id: str, updates: dict, is_admin: bool = False) -> bool:
        """
        Update an existing configuration.

        Args:
            config_id: Configuration identifier
            user_id: User identifier (REQUIRED for ownership verification)
            updates: Dictionary of fields to update
            is_admin: If True, bypass ownership check (admin can update any config)

        Returns:
            True if update successful, False otherwise

        Raises:
            ValueError: If user_id is not provided
            PermissionError: If user doesn't own the configuration (unless admin)
        """
        if not user_id:
            raise ValueError("user_id is required to update a configuration")

        # Verify ownership (skip if admin)
        if not is_admin and not self.verify_ownership(config_id, user_id):
            raise PermissionError(
                f"User {user_id} does not have permission to modify configuration {config_id}"
            )

        # Get existing config (admin can get any config)
        existing_config = self.find_by_config_id(config_id, user_id, is_admin=is_admin)
        if not existing_config:
            return False

        # Prepare update document
        update_doc = existing_config.copy()
        update_doc.update(updates)
        update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Ensure user_id cannot be changed via updates (keep original owner)
        update_doc["user_id"] = existing_config["user_id"]

        # Validate the updated document
        self.validate_document_format(update_doc)

        # Update in database (use original user_id for the query, not the requesting user)
        result = self._mongo_database.update_one(
            {"config_id": config_id},
            {"$set": update_doc}
        )

        return result.modified_count > 0

    def delete_config(self, config_id: str, user_id: str, is_admin: bool = False) -> bool:
        """
        Delete a configuration.

        Args:
            config_id: Configuration identifier
            user_id: User identifier (REQUIRED for ownership verification)
            is_admin: If True, bypass ownership check (admin can delete any config)

        Returns:
            True if deletion successful, False otherwise

        Raises:
            ValueError: If user_id is not provided
            PermissionError: If user doesn't own the configuration (unless admin)
        """
        if not user_id:
            raise ValueError("user_id is required to delete a configuration")

        # Verify ownership (skip if admin)
        if not is_admin and not self.verify_ownership(config_id, user_id):
            raise PermissionError(
                f"User {user_id} does not have permission to delete configuration {config_id}"
            )

        # Admin can delete any config, regular user can only delete their own
        if is_admin:
            result = self.delete_one({"config_id": config_id})
        else:
            result = self.delete_one({"config_id": config_id, "user_id": user_id})
        return result > 0

    def duplicate_config(self, config_id: str, user_id: str, new_name: str, is_admin: bool = False) -> str:
        """
        Create a copy of an existing configuration.

        Args:
            config_id: Source configuration identifier
            user_id: User identifier (REQUIRED - the user who will own the duplicate)
            new_name: Name for the new configuration
            is_admin: If True, can duplicate any config (admin bypass)

        Returns:
            The new config_id

        Raises:
            ValueError: If user_id is not provided
            PermissionError: If user doesn't own the source configuration (unless admin)
        """
        if not user_id:
            raise ValueError("user_id is required to duplicate a configuration")

        # Get source config (admin can duplicate any config)
        source_config = self.find_by_config_id(config_id, user_id, is_admin=is_admin)

        if not source_config:
            raise PermissionError(
                f"User {user_id} does not have permission to access configuration {config_id}"
            )

        # Create new config with same metadata, owned by the requesting user
        return self.create_config(
            name=new_name,
            metadata=source_config["metadata"],
            user_id=user_id
        )

    def create_indexes(self):
        """Create database indexes for performance and uniqueness."""
        # Unique index on config_id
        self._mongo_database.create_index("config_id", unique=True)

        # Compound index on user_id + config_id for ownership checks
        self._mongo_database.create_index([("user_id", 1), ("config_id", 1)])

        # Index on user_id for listing user's configs
        self._mongo_database.create_index("user_id")
