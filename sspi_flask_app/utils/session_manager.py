"""
Session Manager for Customizable SSPI Editing Sessions

Provides utilities for tracking active editing sessions in Flask session storage.
Sessions persist for 30 days of inactivity and track unsaved changes.
"""

from flask import session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


# Session keys
SESSION_KEY = 'sspi_editing_session'
LAST_ACTIVITY_KEY = 'sspi_session_last_activity'
SESSION_TIMEOUT_DAYS = 30


def get_active_session() -> Optional[Dict[str, Any]]:
    """
    Get the current active editing session if it exists and is not expired.

    Returns:
        Dictionary with session data or None if no active session
        Session structure: {
            'config_id': str,
            'name': str,
            'has_unsaved': bool,
            'started_at': str (ISO format),
            'last_activity': str (ISO format),
            'metadata_preview': dict (first few items for display)
        }
    """
    if SESSION_KEY not in session:
        return None

    # Check if session has expired
    last_activity = session.get(LAST_ACTIVITY_KEY)
    if last_activity:
        last_activity_dt = datetime.fromisoformat(last_activity)
        if datetime.utcnow() - last_activity_dt > timedelta(days=SESSION_TIMEOUT_DAYS):
            # Session expired, clear it
            clear_active_session()
            return None

    return session[SESSION_KEY]


def set_active_session(
    config_id: str,
    config_name: str,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create or update the active editing session.

    Args:
        config_id: Unique identifier for the configuration
        config_name: Human-readable name
        metadata: Full metadata structure (optional, for preview)

    Returns:
        The created/updated session dictionary
    """
    now = datetime.utcnow().isoformat()

    # Create metadata preview (first 3 pillars with counts)
    metadata_preview = None
    if metadata:
        metadata_preview = {
            'pillar_count': len(metadata) if isinstance(metadata, list) else 0,
            'category_count': sum(len(p.get('categories', [])) for p in metadata) if isinstance(metadata, list) else 0,
            'indicator_count': sum(
                len(cat.get('indicators', []))
                for p in metadata
                for cat in p.get('categories', [])
            ) if isinstance(metadata, list) else 0
        }

    session_data = {
        'config_id': config_id,
        'name': config_name,
        'has_unsaved': False,
        'started_at': session.get(SESSION_KEY, {}).get('started_at', now),
        'last_activity': now,
        'metadata_preview': metadata_preview
    }

    session[SESSION_KEY] = session_data
    session[LAST_ACTIVITY_KEY] = now
    session.modified = True

    return session_data


def clear_active_session() -> None:
    """
    Clear the active editing session from Flask session.
    """
    if SESSION_KEY in session:
        del session[SESSION_KEY]
    if LAST_ACTIVITY_KEY in session:
        del session[LAST_ACTIVITY_KEY]
    session.modified = True


def mark_unsaved_changes(has_unsaved: bool = True) -> None:
    """
    Mark the current session as having unsaved changes.

    Args:
        has_unsaved: True to mark as unsaved, False to mark as saved
    """
    if SESSION_KEY in session:
        session[SESSION_KEY]['has_unsaved'] = has_unsaved
        session.modified = True


def mark_changes_saved() -> None:
    """
    Mark the current session changes as saved.
    """
    mark_unsaved_changes(False)


def update_last_activity() -> None:
    """
    Update the last activity timestamp to current time.
    Called on each request to prevent session expiry during active editing.
    """
    if SESSION_KEY in session:
        now = datetime.utcnow().isoformat()
        session[SESSION_KEY]['last_activity'] = now
        session[LAST_ACTIVITY_KEY] = now
        session.modified = True


def has_unsaved_changes() -> bool:
    """
    Check if the current session has unsaved changes.

    Returns:
        True if session exists and has unsaved changes, False otherwise
    """
    active_session = get_active_session()
    return active_session.get('has_unsaved', False) if active_session else False


def get_session_config_id() -> Optional[str]:
    """
    Get the config_id of the current active session.

    Returns:
        Config ID string or None if no active session
    """
    active_session = get_active_session()
    return active_session.get('config_id') if active_session else None
