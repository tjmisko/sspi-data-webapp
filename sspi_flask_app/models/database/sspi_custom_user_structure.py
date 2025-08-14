from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from datetime import datetime, timezone
import secrets
import re


class SSPICustomUserStructure(MongoWrapper):
    """
    MongoDB wrapper for custom user-defined SSPI structure data.
    
    Handles validation, CRUD operations, and business logic for user-defined
    SSPI structures created through the customization interface.
    """
    
    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Validates custom config document format.
        
        Expected document format:
        {
            "config_id": "unique_string_identifier",
            "name": "My Custom SSPI Configuration", 
            "user_id": "optional_for_future_multiuser",
            "structure": [
                {
                    "Category": "Environmental Performance",
                    "CategoryCode": "ECO", 
                    "Indicator": "Biodiversity Protection",
                    "IndicatorCode": "BIODIV",
                    "Pillar": "Sustainability",
                    "PillarCode": "SUS", 
                    "LowerGoalpost": 0.0,
                    "UpperGoalpost": 100.0,
                    "ItemOrder": 1,
                    "Inverted": false,
                    "datasets": [
                        {
                            "dataset_code": "EPI_CO2GRW",
                            "weight": 1.0
                        },
                        {
                            "dataset_code": "UNSDG_EPI001",
                            "weight": 2.0
                        }
                    ],
                    "scoring_function": "weighted_average"
                }
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "version": 1
        }
        """
        self.validate_config_id(document, document_number)
        self.validate_config_name(document, document_number)
        self.validate_user_id(document, document_number)
        self.validate_structure(document, document_number)
        self.validate_timestamps(document, document_number)
        self.validate_version(document, document_number)
    
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
        """Validates user_id format (optional field)."""
        if "user_id" in document.keys() and document["user_id"] is not None:
            user_id = document["user_id"]
            if not isinstance(user_id, str):
                raise InvalidDocumentFormatError(
                    f"'user_id' must be a string or None (document {document_number})"
                )
            
            if len(user_id) == 0:
                raise InvalidDocumentFormatError(
                    f"'user_id' cannot be empty string (document {document_number})"
                )
    
    def validate_structure(self, document: dict, document_number: int = 0):
        """Validates the structure array and its contents."""
        if "structure" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'structure' is a required field (document {document_number})"
            )
        
        structure = document["structure"]
        if not isinstance(structure, list):
            raise InvalidDocumentFormatError(
                f"'structure' must be an array (document {document_number})"
            )
        
        if len(structure) == 0:
            raise InvalidDocumentFormatError(
                f"'structure' cannot be empty (document {document_number})"
            )
        
        # Validate each indicator configuration
        indicator_codes = set()
        for i, indicator_config in enumerate(structure):
            self.validate_indicator_config(indicator_config, document_number, i)
            
            # Check for duplicate indicator codes
            indicator_code = indicator_config.get("IndicatorCode", "")
            if indicator_code and indicator_code in indicator_codes:
                raise InvalidDocumentFormatError(
                    f"Duplicate IndicatorCode '{indicator_code}' found in structure (document {document_number})"
                )
            if indicator_code:
                indicator_codes.add(indicator_code)
    
    def validate_indicator_config(self, indicator_config: dict, document_number: int = 0, indicator_index: int = 0):
        """Validates individual indicator configuration object."""
        if not isinstance(indicator_config, dict):
            raise InvalidDocumentFormatError(
                f"Indicator config {indicator_index} must be an object (document {document_number})"
            )
        
        # Required fields
        required_fields = ["Category", "Indicator", "Pillar", "CategoryCode", "IndicatorCode", "PillarCode"]
        for field in required_fields:
            if field not in indicator_config:
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} missing required field '{field}' (document {document_number})"
                )
            
            if not isinstance(indicator_config[field], str):
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} field '{field}' must be a string (document {document_number})"
                )
            
            if len(indicator_config[field].strip()) == 0:
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} field '{field}' cannot be empty (document {document_number})"
                )
        
        # Validate code formats
        self.validate_codes(indicator_config, document_number, indicator_index)
        
        # Validate datasets and scoring function
        self.validate_datasets_and_scoring(indicator_config, document_number, indicator_index)
        
        # Validate goalposts
        self.validate_goalposts(indicator_config, document_number, indicator_index)
        
        # Validate ItemOrder if present
        if "ItemOrder" in indicator_config:
            item_order = indicator_config["ItemOrder"]
            if not isinstance(item_order, int) or item_order < 1:
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'ItemOrder' must be a positive integer (document {document_number})"
                )
        
        # Validate Inverted if present
        if "Inverted" in indicator_config:
            inverted = indicator_config["Inverted"]
            if not isinstance(inverted, bool):
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'Inverted' must be a boolean (document {document_number})"
                )
    
    def validate_codes(self, indicator_config: dict, document_number: int = 0, indicator_index: int = 0):
        """Validates pillar, category, and indicator code formats."""
        # Validate PillarCode format (2-3 uppercase letters)
        pillar_code = indicator_config.get("PillarCode", "")
        if not re.match(r'^[A-Z]{2,3}$', pillar_code):
            raise InvalidDocumentFormatError(
                f"Indicator config {indicator_index} 'PillarCode' must be 2-3 uppercase letters (document {document_number})"
            )
        
        # Validate CategoryCode format (3 uppercase letters)
        category_code = indicator_config.get("CategoryCode", "")
        if not re.match(r'^[A-Z]{3}$', category_code):
            raise InvalidDocumentFormatError(
                f"Indicator config {indicator_index} 'CategoryCode' must be exactly 3 uppercase letters (document {document_number})"
            )
        
        # Validate IndicatorCode format (6 uppercase letters/numbers)
        indicator_code = indicator_config.get("IndicatorCode", "")
        if not re.match(r'^[A-Z0-9]{6}$', indicator_code):
            raise InvalidDocumentFormatError(
                f"Indicator config {indicator_index} 'IndicatorCode' must be exactly 6 uppercase letters/numbers (document {document_number})"
            )
    
    def validate_datasets_and_scoring(self, indicator_config: dict, document_number: int = 0, indicator_index: int = 0):
        """Validates datasets and scoring function configuration."""
        # Validate datasets array
        if "datasets" in indicator_config:
            datasets = indicator_config["datasets"]
            if not isinstance(datasets, list):
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'datasets' must be an array (document {document_number})"
                )
            
            if len(datasets) > 5:
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'datasets' cannot contain more than 5 datasets (document {document_number})"
                )
            
            # Validate each dataset object
            for j, dataset in enumerate(datasets):
                if not isinstance(dataset, dict):
                    raise InvalidDocumentFormatError(
                        f"Indicator config {indicator_index} dataset {j} must be an object (document {document_number})"
                    )
                
                # Required dataset fields
                if "dataset_code" not in dataset:
                    raise InvalidDocumentFormatError(
                        f"Indicator config {indicator_index} dataset {j} missing 'dataset_code' (document {document_number})"
                    )
                
                if not isinstance(dataset["dataset_code"], str) or len(dataset["dataset_code"]) == 0:
                    raise InvalidDocumentFormatError(
                        f"Indicator config {indicator_index} dataset {j} 'dataset_code' must be a non-empty string (document {document_number})"
                    )
                
                # Validate weight if present
                if "weight" in dataset:
                    weight = dataset["weight"]
                    if not isinstance(weight, (int, float)) or weight <= 0:
                        raise InvalidDocumentFormatError(
                            f"Indicator config {indicator_index} dataset {j} 'weight' must be a positive number (document {document_number})"
                        )
        
        # Validate scoring function
        if "scoring_function" in indicator_config:
            scoring_function = indicator_config["scoring_function"]
            if not isinstance(scoring_function, str):
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'scoring_function' must be a string (document {document_number})"
                )
            
            valid_functions = ["average", "weighted_average", "sum", "min", "max"]
            if scoring_function not in valid_functions:
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'scoring_function' must be one of {valid_functions} (document {document_number})"
                )
    
    def validate_goalposts(self, indicator_config: dict, document_number: int = 0, indicator_index: int = 0):
        """Validates goalpost values."""
        lower = indicator_config.get("LowerGoalpost")
        upper = indicator_config.get("UpperGoalpost")
        
        if lower is not None:
            if not isinstance(lower, (int, float)):
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'LowerGoalpost' must be a number (document {document_number})"
                )
        
        if upper is not None:
            if not isinstance(upper, (int, float)):
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'UpperGoalpost' must be a number (document {document_number})"
                )
        
        if lower is not None and upper is not None:
            if lower > upper:
                raise InvalidDocumentFormatError(
                    f"Indicator config {indicator_index} 'LowerGoalpost' cannot be greater than 'UpperGoalpost' (document {document_number})"
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
    
    def validate_version(self, document: dict, document_number: int = 0):
        """Validates version number."""
        if "version" not in document:
            raise InvalidDocumentFormatError(
                f"'version' is a required field (document {document_number})"
            )
        
        version = document["version"]
        if not isinstance(version, int) or version < 1:
            raise InvalidDocumentFormatError(
                f"'version' must be a positive integer (document {document_number})"
            )
    
    def generate_config_id(self) -> str:
        """Generate a unique config identifier."""
        return secrets.token_hex(8)  # 16 characters, hex (alphanumeric only)
    
    def config_exists(self, config_id: str) -> bool:
        """Check if a configuration exists."""
        return self.count_documents({"config_id": config_id}) > 0
    
    def create_config(self, name: str, structure: list, user_id: str = None) -> str:
        """
        Create a new custom configuration.
        
        Args:
            name: Human-readable name for the configuration
            structure: Array of indicator configuration objects
            user_id: Optional user identifier
            
        Returns:
            The generated config_id
            
        Raises:
            InvalidDocumentFormatError: If validation fails
        """
        config_id = self.generate_config_id()
        
        # Ensure unique config_id
        while self.config_exists(config_id):
            config_id = self.generate_config_id()
        
        now = datetime.now(timezone.utc).isoformat()
        
        config_doc = {
            "config_id": config_id,
            "name": name,
            "user_id": user_id,
            "structure": structure,
            "created_at": now,
            "updated_at": now,
            "version": 1
        }
        
        # Validate the document
        self.validate_document_format(config_doc)
        
        # Insert the document
        self.insert_one(config_doc)
        
        return config_id
    
    def find_by_config_id(self, config_id: str) -> dict:
        """Find configuration by config_id."""
        return self.find_one({"config_id": config_id})
    
    def find_by_user_id(self, user_id: str) -> list:
        """Find all configurations for a user."""
        return self.find({"user_id": user_id})
    
    def update_config(self, config_id: str, updates: dict) -> bool:
        """
        Update an existing configuration.
        
        Args:
            config_id: Configuration identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        # Get existing config
        existing_config = self.find_by_config_id(config_id)
        if not existing_config:
            return False
        
        # Prepare update document
        update_doc = existing_config.copy()
        update_doc.update(updates)
        update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_doc["version"] = update_doc.get("version", 1) + 1
        
        # Validate the updated document
        self.validate_document_format(update_doc)
        
        # Update in database
        result = self._mongo_database.update_one(
            {"config_id": config_id},
            {"$set": update_doc}
        )
        
        return result.modified_count > 0
    
    def duplicate_config(self, config_id: str, new_name: str) -> str:
        """
        Create a copy of an existing configuration.
        
        Args:
            config_id: Source configuration identifier
            new_name: Name for the new configuration
            
        Returns:
            The new config_id, or None if source not found
        """
        source_config = self.find_by_config_id(config_id)
        if not source_config:
            return None
        
        return self.create_config(
            name=new_name,
            structure=source_config["structure"],
            user_id=source_config.get("user_id")
        )
    
    def list_config_names(self, user_id: str = None) -> list:
        """
        Get list of configuration names for dropdown/selection.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of dicts with config_id and name
        """
        query = {"user_id": user_id} if user_id else {}
        configs = self.find(query, {"_id": 0, "config_id": 1, "name": 1})
        return configs
    
    def delete_config(self, config_id: str) -> bool:
        """Delete a configuration."""
        result = self.delete_one({"config_id": config_id})
        return result > 0
    
    def create_indexes(self):
        """Create database indexes for performance."""
        # Unique index on config_id
        self._mongo_database.create_index("config_id", unique=True)
        # Index on user_id for user-specific queries
        self._mongo_database.create_index("user_id")
        # Index on name for search functionality
        self._mongo_database.create_index("name")