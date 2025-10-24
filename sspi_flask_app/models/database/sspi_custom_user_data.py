from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from datetime import datetime, timezone
import re


class SSPICustomUserData(MongoWrapper):
    """
    MongoDB wrapper for custom SSPI scoring results data.
    
    Stores cached scoring results from custom user-defined SSPI structures 
    to avoid recalculating scores every time a chart is loaded.
    """
    
    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Validates custom scoring data document format.
        
        Expected document format:
        {
            "config_id": "unique_string_identifier",
            "country_code": "USA", 
            "year": 2023,
            "item_code": "SSPI|SUS|ECO|BIODIV",
            "item_name": "Biodiversity Protection",
            "item_type": "SSPI|Pillar|Category|Indicator",
            "score": 75.5,
            "rank": 12,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        """
        self.validate_config_id(document, document_number)
        self.validate_country_code(document, document_number)
        self.validate_year(document, document_number)
        self.validate_item_code(document, document_number)
        self.validate_item_name(document, document_number)
        self.validate_item_type(document, document_number)
        self.validate_score(document, document_number)
        self.validate_rank(document, document_number)
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
    
    def validate_country_code(self, document: dict, document_number: int = 0):
        """Validates country_code format."""
        if "country_code" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'country_code' is a required field (document {document_number})"
            )
        
        country_code = document["country_code"]
        if not isinstance(country_code, str):
            raise InvalidDocumentFormatError(
                f"'country_code' must be a string (document {document_number})"
            )
        
        # Validate ISO 3166-1 alpha-3 country code format
        if not re.match(r'^[A-Z]{3}$', country_code):
            raise InvalidDocumentFormatError(
                f"'country_code' must be a 3-letter uppercase country code (document {document_number})"
            )
    
    def validate_year(self, document: dict, document_number: int = 0):
        """Validates year field."""
        if "year" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'year' is a required field (document {document_number})"
            )
        
        year = document["year"]
        if not isinstance(year, int):
            raise InvalidDocumentFormatError(
                f"'year' must be an integer (document {document_number})"
            )
        
        # Reasonable year range for SSPI data
        if not (1990 <= year <= 2030):
            raise InvalidDocumentFormatError(
                f"'year' must be between 1990 and 2030 (document {document_number})"
            )
    
    def validate_item_code(self, document: dict, document_number: int = 0):
        """Validates item_code format."""
        if "item_code" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'item_code' is a required field (document {document_number})"
            )
        
        item_code = document["item_code"]
        if not isinstance(item_code, str):
            raise InvalidDocumentFormatError(
                f"'item_code' must be a string (document {document_number})"
            )
        
        if len(item_code) == 0:
            raise InvalidDocumentFormatError(
                f"'item_code' cannot be empty (document {document_number})"
            )
        
        # Validate based on expected SSPI item code patterns
        valid_patterns = [
            r'^SSPI$',  # Root SSPI
            r'^[A-Z]{2,3}$',  # Pillar codes (2-3 letters)
            r'^[A-Z]{3}$',  # Category codes (3 letters) 
            r'^[A-Z0-9]{6}$'  # Indicator codes (6 alphanumeric)
        ]
        
        if not any(re.match(pattern, item_code) for pattern in valid_patterns):
            raise InvalidDocumentFormatError(
                f"'item_code' format not recognized for SSPI hierarchy (document {document_number})"
            )
    
    def validate_item_name(self, document: dict, document_number: int = 0):
        """Validates item_name field."""
        if "item_name" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'item_name' is a required field (document {document_number})"
            )
        
        item_name = document["item_name"]
        if not isinstance(item_name, str):
            raise InvalidDocumentFormatError(
                f"'item_name' must be a string (document {document_number})"
            )
        
        if len(item_name.strip()) == 0:
            raise InvalidDocumentFormatError(
                f"'item_name' cannot be empty (document {document_number})"
            )
        
        if len(item_name) > 200:
            raise InvalidDocumentFormatError(
                f"'item_name' cannot exceed 200 characters (document {document_number})"
            )
    
    def validate_item_type(self, document: dict, document_number: int = 0):
        """Validates item_type field."""
        if "item_type" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'item_type' is a required field (document {document_number})"
            )
        
        item_type = document["item_type"]
        if not isinstance(item_type, str):
            raise InvalidDocumentFormatError(
                f"'item_type' must be a string (document {document_number})"
            )
        
        valid_types = ["SSPI", "Pillar", "Category", "Indicator"]
        if item_type not in valid_types:
            raise InvalidDocumentFormatError(
                f"'item_type' must be one of {valid_types} (document {document_number})"
            )
    
    def validate_score(self, document: dict, document_number: int = 0):
        """Validates score field."""
        if "score" not in document.keys():
            raise InvalidDocumentFormatError(
                f"'score' is a required field (document {document_number})"
            )
        
        score = document["score"]
        if score is not None and not isinstance(score, (int, float)):
            raise InvalidDocumentFormatError(
                f"'score' must be a number or null (document {document_number})"
            )
        
        # SSPI scores are typically 0-100 range but allow broader range for flexibility
        if score is not None and not (0 <= score <= 150):
            raise InvalidDocumentFormatError(
                f"'score' must be between 0 and 150 (document {document_number})"
            )
    
    def validate_rank(self, document: dict, document_number: int = 0):
        """Validates rank field."""
        # Rank is optional - some items may not have meaningful ranking
        if "rank" in document.keys():
            rank = document["rank"]
            if rank is not None and not isinstance(rank, int):
                raise InvalidDocumentFormatError(
                    f"'rank' must be an integer or null (document {document_number})"
                )
            
            if rank is not None and rank < 1:
                raise InvalidDocumentFormatError(
                    f"'rank' must be a positive integer (document {document_number})"
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
    
    def store_scoring_results(self, config_id: str, scoring_results: list) -> int:
        """
        Store scoring results for a custom configuration.
        
        Args:
            config_id: Configuration identifier
            scoring_results: List of score documents to store
            
        Returns:
            Number of documents inserted
            
        Raises:
            InvalidDocumentFormatError: If validation fails
        """
        now = datetime.now(timezone.utc).isoformat()
        
        # Clear existing results for this config
        self.clear_config_results(config_id)
        
        # Prepare documents for insertion
        documents = []
        for i, result in enumerate(scoring_results):
            doc = result.copy()
            doc["config_id"] = config_id
            doc["created_at"] = now
            doc["updated_at"] = now
            
            # Validate each document
            self.validate_document_format(doc, i)
            documents.append(doc)
        
        # Insert all documents
        if documents:
            result = self.insert_many(documents)
            return len(result)
        
        return 0
    
    def get_config_results(self, config_id: str, country_codes: list = None, years: list = None) -> list:
        """
        Retrieve scoring results for a configuration.
        
        Args:
            config_id: Configuration identifier
            country_codes: Optional filter by country codes
            years: Optional filter by years
            
        Returns:
            List of scoring result documents
        """
        query = {"config_id": config_id}
        
        if country_codes:
            query["country_code"] = {"$in": country_codes}
        
        if years:
            query["year"] = {"$in": years}
        
        return self.find(query, {"_id": 0})  # Exclude MongoDB _id field
    
    def clear_config_results(self, config_id: str) -> int:
        """
        Clear all scoring results for a configuration.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            Number of documents deleted
        """
        return self.delete_many({"config_id": config_id})
    
    def get_latest_scoring_timestamp(self, config_id: str) -> str:
        """
        Get the timestamp of the most recent scoring for a configuration.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            ISO timestamp string, or None if no results found
        """
        result = self._mongo_database.find_one(
            {"config_id": config_id},
            {"created_at": 1},
            sort=[("created_at", -1)]
        )
        
        return result.get("created_at") if result else None
    
    def config_has_results(self, config_id: str) -> bool:
        """Check if a configuration has cached scoring results."""
        return self.count_documents({"config_id": config_id}) > 0
    
    def get_config_stats(self, config_id: str) -> dict:
        """
        Get statistics about cached results for a configuration.
        
        Args:
            config_id: Configuration identifier
            
        Returns:
            Dictionary with result statistics
        """
        pipeline = [
            {"$match": {"config_id": config_id}},
            {"$group": {
                "_id": None,
                "total_results": {"$sum": 1},
                "unique_countries": {"$addToSet": "$country_code"},
                "unique_years": {"$addToSet": "$year"},
                "item_types": {"$addToSet": "$item_type"},
                "latest_update": {"$max": "$updated_at"}
            }}
        ]
        
        result = list(self._mongo_database.aggregate(pipeline))
        if not result:
            return {
                "total_results": 0,
                "countries_count": 0,
                "years_count": 0,
                "item_types": [],
                "latest_update": None
            }
        
        stats = result[0]
        return {
            "total_results": stats["total_results"],
            "countries_count": len(stats["unique_countries"]),
            "years_count": len(stats["unique_years"]),
            "item_types": stats["item_types"],
            "latest_update": stats["latest_update"]
        }
    
    def create_indexes(self):
        """Create database indexes for performance."""
        # Compound index for efficient queries by config, country, year
        self._mongo_database.create_index([
            ("config_id", 1),
            ("country_code", 1), 
            ("year", 1)
        ])
        
        # Index on config_id for config-specific queries
        self._mongo_database.create_index("config_id")
        
        # Index on item_code for item-specific queries
        self._mongo_database.create_index([("config_id", 1), ("item_code", 1)])
        
        # Index on timestamps for cache management
        self._mongo_database.create_index("created_at")
        self._mongo_database.create_index("updated_at")