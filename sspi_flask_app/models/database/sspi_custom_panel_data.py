"""
SSPICustomPanelData - Database model for custom SSPI line chart data.

This collection stores ONLY line chart format data for SSPIPanelChart.
One document per (config_hash, item_code, country_code) with year-aligned arrays.

Many-to-one relationship: Multiple config_ids can reference the same config_hash.
Caching strategy: Line data cached by config_hash only, no config_id stored.
No eager deletion on config delete - cached results remain available for other
configs with the same hash.

Document format:
{
    "config_hash": "abc123def456...",     # 32-char SHA-256 prefix (primary cache key)
    "ICode": "SSPI",                      # Item code
    "IName": "Custom SSPI",               # Item name
    "CCode": "USA",                       # Country code (ISO 3166-1 alpha-3)
    "CName": "United States",             # Country name
    "CFlag": "🇺🇸",                        # Country flag emoji
    "CGroup": ["SSPI67", "OECD"],         # Country groups
    "years": [2000, 2001, ..., 2023],     # Year array (always 2000-2023)
    "score": [72.1, 73.5, ..., 76.2],     # Score array (aligned with years)
    "data": [72.1, 73.5, ..., 76.2],      # Same as score (for chart compatibility)
    "label": "USA - United States",       # Display label
    "pinned": false,                      # UI state
    "hidden": false,                      # UI state
    "yAxisMinValue": 0,                   # Chart axis config
    "yAxisMaxValue": 100,                 # Chart axis config
    "created_at": "2024-01-15T10:30:00Z"
}

Indexes:
- (config_hash, ICode, CCode) - unique compound
- config_hash - for full config lookups
- (config_hash, ICode) - for item-specific queries
"""

from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)


class SSPICustomPanelData(MongoWrapper):
    """
    MongoDB wrapper for custom SSPI line chart data.

    Stores ONLY line chart format data for SSPIPanelChart.
    One document per (config_hash, item_code, country_code) with year-aligned arrays.
    """

    # ==========================================================================
    # Document Validation
    # ==========================================================================

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Validate line chart document format.

        Args:
            document: Document to validate
            document_number: Index for error messages

        Raises:
            InvalidDocumentFormatError: If validation fails
        """
        self._validate_config_hash(document, document_number)
        self._validate_item_fields(document, document_number)
        self._validate_country_fields(document, document_number)
        self._validate_year_aligned_arrays(document, document_number)

    def _validate_config_hash(self, document: dict, document_number: int):
        """Validate config_hash field."""
        if "config_hash" not in document:
            raise InvalidDocumentFormatError(
                f"'config_hash' is required (document {document_number})"
            )

        config_hash = document["config_hash"]
        if not isinstance(config_hash, str):
            raise InvalidDocumentFormatError(
                f"'config_hash' must be a string (document {document_number})"
            )

        if not re.match(r'^[a-f0-9]{32}$', config_hash):
            raise InvalidDocumentFormatError(
                f"'config_hash' must be 32 lowercase hex characters (document {document_number})"
            )

    def _validate_item_fields(self, document: dict, document_number: int):
        """Validate item code and name fields."""
        if "ICode" not in document:
            raise InvalidDocumentFormatError(
                f"'ICode' is required (document {document_number})"
            )

        if not isinstance(document["ICode"], str) or len(document["ICode"]) == 0:
            raise InvalidDocumentFormatError(
                f"'ICode' must be a non-empty string (document {document_number})"
            )

        if "IName" not in document:
            raise InvalidDocumentFormatError(
                f"'IName' is required (document {document_number})"
            )

    def _validate_country_fields(self, document: dict, document_number: int):
        """Validate country fields."""
        if "CCode" not in document:
            raise InvalidDocumentFormatError(
                f"'CCode' is required (document {document_number})"
            )

        country_code = document["CCode"]
        if not isinstance(country_code, str):
            raise InvalidDocumentFormatError(
                f"'CCode' must be a string (document {document_number})"
            )

        if not re.match(r'^[A-Z]{3}$', country_code):
            raise InvalidDocumentFormatError(
                f"'CCode' must be 3 uppercase letters (document {document_number})"
            )

        if "CName" not in document:
            raise InvalidDocumentFormatError(
                f"'CName' is required (document {document_number})"
            )

        if "CGroup" not in document or not isinstance(document["CGroup"], list):
            raise InvalidDocumentFormatError(
                f"'CGroup' must be a list (document {document_number})"
            )

    def _validate_year_aligned_arrays(self, document: dict, document_number: int):
        """Validate year-aligned score arrays."""
        if "years" not in document:
            raise InvalidDocumentFormatError(
                f"'years' is required (document {document_number})"
            )

        years = document["years"]
        if not isinstance(years, list):
            raise InvalidDocumentFormatError(
                f"'years' must be a list (document {document_number})"
            )

        # Validate years span 2000-2023
        expected_years = list(range(2000, 2024))
        if years != expected_years:
            raise InvalidDocumentFormatError(
                f"'years' must be [2000, 2001, ..., 2023] (document {document_number})"
            )

        if "score" not in document:
            raise InvalidDocumentFormatError(
                f"'score' is required (document {document_number})"
            )

        score = document["score"]
        if not isinstance(score, list):
            raise InvalidDocumentFormatError(
                f"'score' must be a list (document {document_number})"
            )

        if len(score) != len(years):
            raise InvalidDocumentFormatError(
                f"'score' length ({len(score)}) must match 'years' length ({len(years)}) "
                f"(document {document_number})"
            )

        # Validate each score is a number or None
        for i, s in enumerate(score):
            if s is not None and not isinstance(s, (int, float)):
                raise InvalidDocumentFormatError(
                    f"'score[{i}]' must be a number or null (document {document_number})"
                )

    # ==========================================================================
    # CRUD Operations
    # ==========================================================================

    def store_line_data(
        self,
        config_hash: str,
        line_data: list[dict]
    ) -> int:
        """
        Store line chart data for a configuration.

        Args:
            config_hash: SHA-256 hash prefix (32 chars) of canonical config
            line_data: List of line chart documents to store

        Returns:
            Number of documents inserted

        Raises:
            InvalidDocumentFormatError: If validation fails
        """
        if not line_data:
            return 0

        now = datetime.now(timezone.utc).isoformat()

        # Prepare documents
        documents = []
        for i, data in enumerate(line_data):
            doc = data.copy()
            doc["config_hash"] = config_hash
            doc["created_at"] = now

            # Ensure 'data' field matches 'score' for chart compatibility
            doc["data"] = doc.get("score", [])

            # Set defaults for UI state fields
            doc.setdefault("pinned", False)
            doc.setdefault("hidden", False)
            doc.setdefault("yAxisMinValue", 0)
            doc.setdefault("yAxisMaxValue", 100)

            # Validate
            self.validate_document_format(doc, i)
            documents.append(doc)

        # Insert all documents
        try:
            inserted = self.insert_many(documents)
            logger.info(f"Stored {len(inserted)} line chart documents for config_hash {config_hash[:8]}...")
            return len(inserted)
        except Exception as e:
            logger.error(f"Failed to store line chart data: {e}")
            raise

    def get_line_data(
        self,
        config_hash: str,
        item_code: str | None = None,
        country_codes: list[str] | None = None
    ) -> list[dict]:
        """
        Get line chart data by config hash.

        Args:
            config_hash: SHA-256 hash prefix of canonical config
            item_code: Optional filter by item code
            country_codes: Optional filter by country codes

        Returns:
            List of line chart documents
        """
        query = {"config_hash": config_hash}

        if item_code:
            query["ICode"] = item_code

        if country_codes:
            query["CCode"] = {"$in": country_codes}

        return self.find(query, {"_id": 0})

    def has_line_data(self, config_hash: str) -> bool:
        """Check if line data exists for a config hash."""
        return self.count_documents({"config_hash": config_hash}) > 0

    def has_scores(self, config_hash: str) -> bool:
        """Check if scores exist for a config hash (alias for has_line_data)."""
        return self.has_line_data(config_hash)

    def clear_by_hash(self, config_hash: str) -> int:
        """
        Clear all line data for a config hash.

        Args:
            config_hash: Config hash to clear

        Returns:
            Number of documents deleted
        """
        deleted = self.delete_many({"config_hash": config_hash})
        logger.info(f"Cleared {deleted} line chart documents for config_hash {config_hash[:8]}...")
        return deleted

    def get_unique_items(self, config_hash: str) -> list[str]:
        """
        Get list of unique item codes for a config.

        Args:
            config_hash: Configuration hash

        Returns:
            List of unique item codes
        """
        pipeline = [
            {"$match": {"config_hash": config_hash}},
            {"$group": {"_id": "$ICode"}},
            {"$sort": {"_id": 1}}
        ]
        result = list(self._mongo_database.aggregate(pipeline))
        return [r["_id"] for r in result]

    def get_cache_stats(self, config_hash: str) -> dict:
        """
        Get statistics about cached line data.

        Args:
            config_hash: Configuration hash

        Returns:
            Dictionary with cache statistics
        """
        pipeline = [
            {"$match": {"config_hash": config_hash}},
            {"$group": {
                "_id": None,
                "total_documents": {"$sum": 1},
                "unique_countries": {"$addToSet": "$CCode"},
                "unique_items": {"$addToSet": "$ICode"},
                "created_at": {"$first": "$created_at"}
            }}
        ]

        result = list(self._mongo_database.aggregate(pipeline))

        if not result:
            return {
                "total_documents": 0,
                "countries_count": 0,
                "items_count": 0,
                "created_at": None
            }

        stats = result[0]
        return {
            "total_documents": stats["total_documents"],
            "countries_count": len(stats["unique_countries"]),
            "items_count": len(stats["unique_items"]),
            "created_at": stats["created_at"]
        }

    # ==========================================================================
    # Index Management
    # ==========================================================================

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        # Primary compound unique index
        self._mongo_database.create_index(
            [
                ("config_hash", 1),
                ("ICode", 1),
                ("CCode", 1)
            ],
            unique=True,
            name="unique_line_entry"
        )

        # Index for full config hash lookups
        self._mongo_database.create_index(
            "config_hash",
            name="config_hash_lookup"
        )

        # Index for item-specific queries
        self._mongo_database.create_index(
            [("config_hash", 1), ("ICode", 1)],
            name="hash_item_lookup"
        )

        logger.info("Created indexes for sspi_custom_panel_data")

    def drop_indexes(self):
        """Drop all custom indexes (keeps _id index)."""
        self._mongo_database.drop_indexes()
        logger.info("Dropped indexes for sspi_custom_panel_data")
