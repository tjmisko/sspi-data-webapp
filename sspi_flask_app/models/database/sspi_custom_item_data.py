"""
SSPICustomItemData - Database model for cached custom SSPI flat score results.

This collection stores computed flat score documents for custom SSPI configurations,
keyed by config_hash for efficient cache lookups. Same configurations
(regardless of user) produce the same hash and can share cached results.

Many-to-one relationship: Multiple config_ids can reference the same config_hash.
Caching strategy: Score results cached by config_hash only, no config_id stored.
No eager deletion on config delete - cached results remain available for other
configs with the same hash.

Document format:
{
    "config_hash": "abc123def456...",     # 32-char SHA-256 prefix (primary cache key)
    "item_code": "BIODIV",                # SSPI/Pillar/Category/Indicator code
    "item_name": "Biodiversity Protection",
    "item_type": "Indicator",             # Type: SSPI, Pillar, Category, Indicator
    "country_code": "USA",
    "year": 2023,
    "score": 0.75,
    "rank": 12,
    "imputed": false,
    "imputation_method": null,            # "interpolate", "extrapolate_forward", etc.
    "imputation_distance": null,          # Years from nearest actual data
    "created_at": "2024-01-15T10:30:00Z"
}

Indexes:
- (config_hash, item_code, country_code, year) - unique compound
- config_hash - for full config lookups
- created_at - for cache management
"""

from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)


class SSPICustomItemData(MongoWrapper):
    """
    MongoDB wrapper for cached custom SSPI flat score data.

    Stores computed scores from custom configurations, keyed by config_hash
    for efficient caching. Multiple users with identical configurations
    share the same cached results.

    This is the flat score storage - one document per (config_hash, item, country, year).
    Used for caching, export, and as source for line data transformation.
    """

    # ==========================================================================
    # Document Validation
    # ==========================================================================

    def validate_document_format(self, document: dict, document_number: int = 0):
        """
        Validate flat score document format.

        Args:
            document: Document to validate
            document_number: Index for error messages

        Raises:
            InvalidDocumentFormatError: If validation fails
        """
        self._validate_config_hash(document, document_number)
        self._validate_item_code(document, document_number)
        self._validate_item_type(document, document_number)
        self._validate_country_code(document, document_number)
        self._validate_year(document, document_number)
        self._validate_score(document, document_number)
        self._validate_optional_fields(document, document_number)

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

        # Should be 32 hex characters (first 32 chars of SHA-256)
        if not re.match(r'^[a-f0-9]{32}$', config_hash):
            raise InvalidDocumentFormatError(
                f"'config_hash' must be 32 lowercase hex characters (document {document_number})"
            )

    def _validate_item_code(self, document: dict, document_number: int):
        """Validate item_code field."""
        if "item_code" not in document:
            raise InvalidDocumentFormatError(
                f"'item_code' is required (document {document_number})"
            )

        item_code = document["item_code"]
        if not isinstance(item_code, str) or len(item_code) == 0:
            raise InvalidDocumentFormatError(
                f"'item_code' must be a non-empty string (document {document_number})"
            )

    def _validate_item_type(self, document: dict, document_number: int):
        """Validate item_type field."""
        if "item_type" not in document:
            raise InvalidDocumentFormatError(
                f"'item_type' is required (document {document_number})"
            )

        item_type = document["item_type"]
        valid_types = {"SSPI", "Pillar", "Category", "Indicator"}

        if item_type not in valid_types:
            raise InvalidDocumentFormatError(
                f"'item_type' must be one of {valid_types} (document {document_number})"
            )

    def _validate_country_code(self, document: dict, document_number: int):
        """Validate country_code field."""
        if "country_code" not in document:
            raise InvalidDocumentFormatError(
                f"'country_code' is required (document {document_number})"
            )

        country_code = document["country_code"]
        if not isinstance(country_code, str):
            raise InvalidDocumentFormatError(
                f"'country_code' must be a string (document {document_number})"
            )

        # ISO 3166-1 alpha-3 format
        if not re.match(r'^[A-Z]{3}$', country_code):
            raise InvalidDocumentFormatError(
                f"'country_code' must be 3 uppercase letters (document {document_number})"
            )

    def _validate_year(self, document: dict, document_number: int):
        """Validate year field."""
        if "year" not in document:
            raise InvalidDocumentFormatError(
                f"'year' is required (document {document_number})"
            )

        year = document["year"]
        if not isinstance(year, int):
            raise InvalidDocumentFormatError(
                f"'year' must be an integer (document {document_number})"
            )

        if not (1990 <= year <= 2030):
            raise InvalidDocumentFormatError(
                f"'year' must be between 1990 and 2030 (document {document_number})"
            )

    def _validate_score(self, document: dict, document_number: int):
        """Validate score field."""
        if "score" not in document:
            raise InvalidDocumentFormatError(
                f"'score' is required (document {document_number})"
            )

        score = document["score"]
        # Score can be None for missing data
        if score is not None and not isinstance(score, (int, float)):
            raise InvalidDocumentFormatError(
                f"'score' must be a number or null (document {document_number})"
            )

    def _validate_optional_fields(self, document: dict, document_number: int):
        """Validate optional fields if present."""
        # Rank validation
        rank = document.get("rank")
        if rank is not None and not isinstance(rank, int):
            raise InvalidDocumentFormatError(
                f"'rank' must be an integer or null (document {document_number})"
            )

        # Imputed flag validation
        imputed = document.get("imputed")
        if imputed is not None and not isinstance(imputed, bool):
            raise InvalidDocumentFormatError(
                f"'imputed' must be a boolean or null (document {document_number})"
            )

        # Imputation method validation
        imputation_method = document.get("imputation_method")
        valid_methods = {None, "interpolate", "extrapolate_forward", "extrapolate_backward"}
        if imputation_method not in valid_methods:
            raise InvalidDocumentFormatError(
                f"'imputation_method' must be one of {valid_methods} (document {document_number})"
            )

    # ==========================================================================
    # CRUD Operations
    # ==========================================================================

    def store_scoring_results(
        self,
        config_hash: str,
        results: list[dict]
    ) -> int:
        """
        Store complete scoring results for a configuration.

        Args:
            config_hash: SHA-256 hash prefix (32 chars) of canonical config
            results: List of score documents to store

        Returns:
            Number of documents inserted

        Raises:
            InvalidDocumentFormatError: If validation fails
        """
        if not results:
            return 0

        now = datetime.now(timezone.utc).isoformat()

        # Prepare documents
        documents = []
        for i, result in enumerate(results):
            doc = result.copy()
            doc["config_hash"] = config_hash
            doc["created_at"] = now

            # Set defaults for optional fields
            doc.setdefault("imputed", False)
            doc.setdefault("imputation_method", None)
            doc.setdefault("imputation_distance", None)
            doc.setdefault("rank", None)
            doc.setdefault("item_name", doc.get("item_code", ""))

            # Validate
            self.validate_document_format(doc, i)
            documents.append(doc)

        # Insert all documents
        try:
            inserted = self.insert_many(documents)
            logger.info(f"Stored {len(inserted)} flat score results for config_hash {config_hash[:8]}...")
            return len(inserted)
        except Exception as e:
            logger.error(f"Failed to store flat score results: {e}")
            raise

    def get_cached_results(self, config_hash: str) -> list[dict] | None:
        """
        Get cached results by config hash.

        Args:
            config_hash: SHA-256 hash prefix of canonical config

        Returns:
            List of score documents if cached, None if not cached
        """
        results = self.find({"config_hash": config_hash}, {"_id": 0})

        if not results:
            return None

        return results

    def has_cached_results(self, config_hash: str) -> bool:
        """Check if results exist for a config hash."""
        return self.count_documents({"config_hash": config_hash}) > 0

    def clear_by_hash(self, config_hash: str) -> int:
        """
        Clear all results for a config hash.

        Args:
            config_hash: Config hash to clear

        Returns:
            Number of documents deleted
        """
        deleted = self.delete_many({"config_hash": config_hash})
        logger.info(f"Cleared {deleted} cached flat scores for config_hash {config_hash[:8]}...")
        return deleted

    def get_results_by_item(
        self,
        config_hash: str,
        item_code: str,
        country_codes: list[str] | None = None,
        years: list[int] | None = None
    ) -> list[dict]:
        """
        Get cached results for a specific item.

        Args:
            config_hash: Configuration hash
            item_code: Item code to query
            country_codes: Optional filter by countries
            years: Optional filter by years

        Returns:
            List of score documents
        """
        query = {
            "config_hash": config_hash,
            "item_code": item_code
        }

        if country_codes:
            query["country_code"] = {"$in": country_codes}

        if years:
            query["year"] = {"$in": years}

        return self.find(query, {"_id": 0})

    def get_results_by_country(
        self,
        config_hash: str,
        country_code: str,
        years: list[int] | None = None
    ) -> list[dict]:
        """
        Get all cached results for a specific country.

        Args:
            config_hash: Configuration hash
            country_code: Country code to query
            years: Optional filter by years

        Returns:
            List of score documents
        """
        query = {
            "config_hash": config_hash,
            "country_code": country_code
        }

        if years:
            query["year"] = {"$in": years}

        return self.find(query, {"_id": 0})

    def get_cache_stats(self, config_hash: str) -> dict:
        """
        Get statistics about cached results.

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
                "unique_countries": {"$addToSet": "$country_code"},
                "unique_years": {"$addToSet": "$year"},
                "unique_items": {"$addToSet": "$item_code"},
                "item_types": {"$addToSet": "$item_type"},
                "created_at": {"$first": "$created_at"},
                "imputed_count": {
                    "$sum": {"$cond": [{"$eq": ["$imputed", True]}, 1, 0]}
                }
            }}
        ]

        result = list(self._mongo_database.aggregate(pipeline))

        if not result:
            return {
                "total_documents": 0,
                "countries_count": 0,
                "years_count": 0,
                "items_count": 0,
                "item_types": [],
                "created_at": None,
                "imputed_count": 0
            }

        stats = result[0]
        return {
            "total_documents": stats["total_documents"],
            "countries_count": len(stats["unique_countries"]),
            "years_count": len(stats["unique_years"]),
            "items_count": len(stats["unique_items"]),
            "item_types": stats["item_types"],
            "created_at": stats["created_at"],
            "imputed_count": stats["imputed_count"]
        }

    # ==========================================================================
    # Index Management
    # ==========================================================================

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        # Primary compound unique index for cache lookups
        self._mongo_database.create_index(
            [
                ("config_hash", 1),
                ("item_code", 1),
                ("country_code", 1),
                ("year", 1)
            ],
            unique=True,
            name="unique_score_entry"
        )

        # Index for full config hash lookups (cache hit check)
        self._mongo_database.create_index(
            "config_hash",
            name="config_hash_lookup"
        )

        # Index for item-specific queries
        self._mongo_database.create_index(
            [("config_hash", 1), ("item_code", 1)],
            name="hash_item_lookup"
        )

        # Index for country-specific queries
        self._mongo_database.create_index(
            [("config_hash", 1), ("country_code", 1)],
            name="hash_country_lookup"
        )

        # Index for cache management (TTL, cleanup)
        self._mongo_database.create_index(
            "created_at",
            name="created_at_index"
        )

        logger.info("Created indexes for sspi_custom_item_data")

    def drop_indexes(self):
        """Drop all custom indexes (keeps _id index)."""
        self._mongo_database.drop_indexes()
        logger.info("Dropped indexes for sspi_custom_item_data")
