"""
Startup-safe unique indexes for the recomputable custom-scoring caches.

The custom-score caches (sspi_custom_item_data, sspi_custom_panel_data) get a
UNIQUE index at app startup. A database written by older code can hold
duplicate rows, or a same-named index with different options, either of which
makes create_index raise and would abort startup. These collections are pure
caches: every row is rebuilt the next time a configuration is scored, and a
config whose rows are gone simply shows as unscored. So instead of failing
startup we repair the cache and build the index.

Use this only for recomputable caches, never for collections holding user data.
"""
import logging

from pymongo.errors import DuplicateKeyError, OperationFailure

logger = logging.getLogger(__name__)

# Server codes for "an index with this name/keys already exists with different
# options or a different key spec".
INDEX_CONFLICT_CODES = frozenset({85, 86})


def create_unique_cache_index(collection, keys, name: str) -> None:
    """
    Create a unique index on a recomputable cache collection, repairing it if
    existing contents or an old index definition block the build.
    """
    try:
        collection.create_index(keys, unique=True, name=name)
        return
    except DuplicateKeyError:
        logger.warning(
            "Duplicate rows block unique index %s on cache %s; clearing the "
            "cache (it rebuilds on the next score) and retrying",
            name, collection.name,
        )
        cleared = collection.delete_many({})
        logger.warning(
            "Cleared %s rows from cache %s",
            getattr(cleared, "deleted_count", "?"), collection.name,
        )
    except OperationFailure as error:
        if error.code not in INDEX_CONFLICT_CODES:
            raise
        logger.warning(
            "Existing index conflicts with unique index %s on cache %s "
            "(code %s); dropping it and retrying",
            name, collection.name, error.code,
        )
        collection.drop_index(name)
    collection.create_index(keys, unique=True, name=name)
