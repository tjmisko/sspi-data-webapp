"""
Secure file reading utilities for the SSPI Flask application.

Provides path traversal protection and graceful error handling
for reading documentation and methodology files from disk.
"""
import os
import logging

log = logging.getLogger(__name__)


class SecurePathError(Exception):
    """Raised when path validation fails due to security concerns."""
    pass


def secure_read_file(
    base_dir: str,
    relative_path: str,
    allowed_extensions: list = None
) -> str:
    """
    Safely read a file within an allowed base directory.

    Prevents path traversal attacks by ensuring the resolved path
    stays within the base directory. Returns file contents on success,
    raises SecurePathError on security violations or file not found.

    Args:
        base_dir: The base directory that the file must be within
        relative_path: The relative path from base_dir to the file
        allowed_extensions: Optional list of allowed file extensions (e.g., ['.md'])

    Returns:
        The contents of the file as a string

    Raises:
        SecurePathError: If path traversal is detected, extension is invalid,
                        or file doesn't exist
    """
    # Resolve both paths to absolute, normalized paths
    base_resolved = os.path.realpath(base_dir)
    full_path = os.path.realpath(os.path.join(base_dir, relative_path))

    # Verify path is within allowed directory (prevent path traversal)
    if not full_path.startswith(base_resolved + os.sep) and full_path != base_resolved:
        log.warning(f"Path traversal attempt blocked: {relative_path}")
        raise SecurePathError("Invalid file path")

    # Validate extension if specified
    if allowed_extensions:
        if not any(full_path.endswith(ext) for ext in allowed_extensions):
            log.warning(f"Invalid file extension for path: {relative_path}")
            raise SecurePathError("Invalid file type")

    # Check file exists
    if not os.path.isfile(full_path):
        log.debug(f"File not found: {full_path}")
        raise SecurePathError("File not found")

    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()
