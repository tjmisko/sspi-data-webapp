import csv
import os
import json
import io
import logging
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request, current_app as app
from flask_login import login_required, current_user

from sspi_flask_app.auth.decorators import owner_or_admin_required
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.models.database import (
    sspi_custom_panel_data,
    sspi_custom_item_data,
    sspi_custom_user_data,
    sspi_custom_user_structure,
    sspi_item_data,
    sspi_metadata,
)
from sspi_flask_app.api.resources.custom_scoring import build_custom_tree
from sspi_flask_app.models.errors import InvalidDocumentFormatError, LimitExceededError
from sspi_flask_app.models.rank import SSPIRankingTable
from sspi_flask_app.models.sspi import FastSSPI
from sspi_flask_app.api.resources.scoring_tasks import (
    start_scoring_job,
    get_job,
    generate_sse_events,
    JobStatus,
)
from sspi_flask_app.api.resources.metadata_validator import (
    validate_custom_metadata,
    compute_config_hash,
)

logger = logging.getLogger(__name__)


def compute_metadata_counts(metadata: list) -> dict:
    """
    Compute counts of pillars, categories, indicators, and datasets from metadata.

    Args:
        metadata: List of metadata items

    Returns:
        Dictionary with pillar_count, category_count, indicator_count, dataset_count
    """
    counts = {
        "pillar_count": 0,
        "category_count": 0,
        "indicator_count": 0,
        "dataset_count": 0
    }

    dataset_codes = set()

    for item in metadata:
        item_type = item.get("ItemType", "")
        if item_type == "Pillar":
            counts["pillar_count"] += 1
        elif item_type == "Category":
            counts["category_count"] += 1
        elif item_type == "Indicator":
            counts["indicator_count"] += 1
            # Count datasets from indicators
            for code in item.get("DatasetCodes", []):
                dataset_codes.add(code)

    counts["dataset_count"] = len(dataset_codes)
    return counts


def sanitize_text_input(text: str, max_length: int = 200, field_name: str = "input", allow_newlines: bool = False) -> str:
    """
    Sanitize user text input to prevent injection and ensure safe storage.

    Only allows ASCII alphanumeric characters, periods, commas, parentheses,
    dashes, and spaces. Optionally allows newlines for description fields.
    This prevents injection attacks via special characters like
    angle brackets, curly braces, equals signs, and other operators.

    Allowed characters: A-Z, a-z, 0-9, period (.), comma (,), parentheses (), dash (-), space
    With allow_newlines: also newline characters

    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length (default 200)
        field_name: Name of the field for error messages
        allow_newlines: Whether to allow newline characters (default False)

    Returns:
        Sanitized text string

    Raises:
        ValueError: If text is invalid, contains forbidden characters, or exceeds max length
    """
    if not isinstance(text, str):
        raise ValueError(f"{field_name} must be a string")

    # Strip leading/trailing whitespace
    text = text.strip()

    if not text:
        raise ValueError(f"{field_name} cannot be empty")

    if len(text) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters")

    # Validate allowed characters: A-Za-z0-9.,()- and space only
    # This prevents injection via <, >, {, }, =, /, \, quotes, etc.
    if allow_newlines:
        # Allow newlines (\n and \r) in addition to standard characters
        allowed_pattern = re.compile(r'^[A-Za-z0-9.,() \r\n-]+$')
        allowed_chars_desc = "letters, numbers, periods, commas, parentheses, dashes, spaces, and newlines"
        char_pattern = r'[A-Za-z0-9.,() \r\n-]'
    else:
        allowed_pattern = re.compile(r'^[A-Za-z0-9.,() -]+$')
        allowed_chars_desc = "letters, numbers, periods, commas, parentheses, dashes, and spaces"
        char_pattern = r'[A-Za-z0-9.,() -]'

    if not allowed_pattern.match(text):
        # Find the first invalid character for a helpful error message
        invalid_chars = set()
        for char in text:
            if not re.match(char_pattern, char):
                invalid_chars.add(repr(char))
        raise ValueError(
            f"{field_name} contains invalid characters: {', '.join(sorted(invalid_chars))}. "
            f"Only {allowed_chars_desc} are allowed."
        )

    # Normalize whitespace (collapse multiple consecutive spaces, but preserve newlines if allowed)
    if allow_newlines:
        text = re.sub(r'[^\S\r\n]+', ' ', text)  # Collapse spaces/tabs but not newlines
        text = re.sub(r' *\r?\n *', '\n', text)  # Normalize newlines and trim spaces around them
        text = re.sub(r'\n{3,}', '\n\n', text)   # Collapse 3+ newlines to 2
    else:
        text = re.sub(r' +', ' ', text)

    return text


customize_bp = Blueprint("customize_bp", __name__,
                        template_folder="templates",
                        static_folder="static",
                        url_prefix="/customize")



@customize_bp.route("/datasets", methods=["GET"])
def list_datasets():
    try:
        search_term = request.args.get("search", "").strip().lower()
        limit = int(request.args.get("limit", 100))
        org_details = sspi_metadata.organization_details()
        org_code_to_name = {
            org.get("OrganizationCode"): org.get("OrganizationName", "")
            for org in org_details
        }
        all_datasets = sspi_metadata.dataset_details()
        for dataset in all_datasets:
            org_code = dataset.get("Source", {}).get("OrganizationCode", "")
            # If we have a code and can look up the full name, enrich it
            if org_code and org_code in org_code_to_name:
                full_org_name = org_code_to_name[org_code]
                # Ensure Source.OrganizationName is set to the full name
                if "Source" not in dataset:
                    dataset["Source"] = {}
                dataset["Source"]["OrganizationName"] = full_org_name

        if search_term:
            filtered = [
                d for d in all_datasets
                if search_term in str(d).lower()
            ]
        else:
            filtered = all_datasets
        filtered.sort(key=lambda x: x.get("DatasetCode", ""))
        if limit > 0:
            filtered = filtered[:limit]
        return jsonify({
            "success": True,
            "datasets": filtered
        })
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/datasets/<dataset_code>", methods=["GET"])
def get_dataset_details(dataset_code):
    try:
        dataset = sspi_metadata.get_dataset_detail(dataset_code.upper())
        if not dataset:
            return jsonify({"error": "Dataset not found"}), 404
        return jsonify({
            "success": True,
            "dataset": dataset  # Return metadata as-is
        })
    except Exception as e:
        logger.error(f"Error getting dataset details for {dataset_code}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/default-structure", methods=["GET"])
def get_default_structure():
    """
    Load the complete default SSPI structure with proper hierarchy.
    Enriches indicators with full dataset details and includes all available datasets.
    Enriches organization names using organization code lookup.
    Returns:
    {
        "success": true,
        "metadata": [...],  // Complete SSPI metadata with DatasetDetails included
        "all_datasets": [...]  // All available dataset details with enriched organization info
    }
    """
    try:
        metadata_items = sspi_metadata.item_details()
        # Build organization code-to-name lookup table (code is the key)
        org_details = sspi_metadata.organization_details()
        org_code_to_name = {
            org.get("OrganizationCode"): org.get("OrganizationName", "")
            for org in org_details
        }
        logger.info(f"Built organization lookup with {len(org_code_to_name)} organizations")
        all_datasets_list = sspi_metadata.dataset_details()
        for dataset in all_datasets_list: # Join full organization name from lookup
            org_code = dataset.get("Source", {}).get("OrganizationCode", "")
            if org_code and org_code in org_code_to_name:
                full_org_name = org_code_to_name[org_code]
                if "Source" not in dataset:
                    dataset["Source"] = {}
                dataset["Source"]["OrganizationName"] = full_org_name

        all_datasets = {d["DatasetCode"]: d for d in all_datasets_list}
        logger.info(f"Loaded default SSPI structure with {len(metadata_items)} items and {len(all_datasets_list)} datasets")
        return jsonify({
            "success": True,
            "metadata": metadata_items,
            "datasetDetailsMap": all_datasets,  # Map of DatasetCode -> full dataset object
            "has_scores": True,  # Default SSPI always has pre-computed scores
        })
    except Exception as e:
        logger.error(f"Error loading default structure: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/indicators", methods=["GET"])
def list_indicators():
    """
    List available indicators for adding to custom SSPI structures.
    Returns complete indicator metadata.

    Query parameters:
    - search: Optional search term to filter indicators
    - category: Optional category filter
    - pillar: Optional pillar filter
    - limit: Optional limit on number of results (default 100)

    Returns:
    {
        "success": true,
        "indicators": [
            {
                "IndicatorCode": "ACWAT1",
                "IndicatorName": "Access to Clean Water",
                "Description": "...",
                "CategoryCode": "BHN",
                "PillarCode": "SUS",
                ... (all metadata fields)
            }
        ]
    }
    """
    try:
        search_term = request.args.get('search', '').strip().lower()
        limit = int(request.args.get('limit', 100))
        all_indicators = sspi_metadata.indicator_details()
        if not all_indicators:
            return jsonify({
                "success": True,
                "indicators": [],
                "message": "No indicators found in metadata"
            })
        filtered = []
        for ind in all_indicators:
            # Apply search filter
            if search_term and not any(
                search_term in str(ind.get(f, '')).lower()
                for f in ['IndicatorCode', 'IndicatorName', 'Description']
            ):
                continue
            filtered.append(ind)  # Return full metadata
        if limit > 0:
            filtered = filtered[:limit]

        # Get pillar and category details for dropdown building
        pillar_options = sspi_metadata.pillar_details()
        category_options = sspi_metadata.category_details()

        return jsonify({
            "success": True,
            "indicators": filtered,
            "total_count": len(filtered),
            "pillars": pillar_options,
            "categories": category_options
        })
    except Exception as e:
        logger.error(f"Error listing indicators: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/save", methods=["POST"])
@owner_or_admin_required
def save_configuration():
    """Save a custom SSPI configuration for the current user."""
    try:
        user_id = current_user.username
        data = request.get_json()

        if not data or 'metadata' not in data:
            return jsonify({"success": False, "error": "No metadata provided"}), 400

        config_name = data.get('name', f'Custom SSPI {user_id}')
        config_description = data.get('description', None)
        metadata = data.get('metadata')
        actions = data.get('actions', [])

        # Validate inputs
        if not isinstance(metadata, list):
            return jsonify({"success": False, "error": "metadata must be a list"}), 400

        if not isinstance(actions, list):
            return jsonify({"success": False, "error": "actions must be a list"}), 400

        # Sanitize name and description (strip whitespace, limit length)
        config_name = sanitize_text_input(config_name, max_length=200, field_name="name")
        if config_description:
            config_description = sanitize_text_input(config_description, max_length=1000, field_name="description", allow_newlines=True)

        # Compute counts from metadata
        counts = compute_metadata_counts(metadata)

        # Save to database
        config_id = sspi_custom_user_structure.create_config(
            name=config_name,
            metadata=metadata,
            username=user_id,
            description=config_description,
            actions=actions,
            counts=counts
        )

        logger.info(f"Saved configuration {config_id} for user {user_id} with {len(metadata)} items and {len(actions)} actions")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "name": config_name,
            "description": config_description,
            "message": "Configuration saved successfully"
        })
    except LimitExceededError as e:
        logger.warning(f"User {current_user.username} exceeded config limit: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 429
    except ValueError as e:
        logger.error(f"Validation error saving configuration: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        import traceback
        logger.error(f"Error saving configuration: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/list", methods=["GET"])
@owner_or_admin_required
def list_configurations():
    """List all saved configurations for the current user."""
    try:
        user_id = current_user.username

        # Fetch configurations from database
        configurations = sspi_custom_user_structure.list_config_names(username=user_id)

        logger.info(f"Retrieved {len(configurations)} configurations for user {user_id}")

        return jsonify({
            "success": True,
            "configurations": configurations
        })
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/load/<config_id>", methods=["GET"])
@owner_or_admin_required
def load_configuration(config_id):
    """Load a specific saved configuration."""
    try:
        user_id = current_user.username

        # Fetch configuration from database (verify ownership)
        config = sspi_custom_user_structure.find_by_config_id(config_id, username=user_id)

        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found or access denied"
            }), 404

        # Load dataset details map (reuse logic from /default-structure)
        org_details = sspi_metadata.organization_details()
        org_code_to_name = {
            org.get("OrganizationCode"): org.get("OrganizationName", "")
            for org in org_details
        }

        all_datasets_list = sspi_metadata.dataset_details()
        for dataset in all_datasets_list:
            org_code = dataset.get("Source", {}).get("OrganizationCode", "")
            if org_code and org_code in org_code_to_name:
                full_org_name = org_code_to_name[org_code]
                if "Source" not in dataset:
                    dataset["Source"] = {}
                dataset["Source"]["OrganizationName"] = full_org_name

        all_datasets = {d["DatasetCode"]: d for d in all_datasets_list}

        # Check if configuration has been scored (has cached results)
        # Use the stored scored_hash which reflects the filtered metadata used during scoring
        has_scores = False
        scored_hash = config.get("scored_hash")
        if scored_hash:
            has_scores = sspi_custom_panel_data.has_scores(scored_hash)

        logger.info(f"Loaded configuration {config_id} for user {user_id} (has_scores={has_scores}, scored_hash={scored_hash[:8] if scored_hash else 'None'}...)")

        return jsonify({
            "success": True,
            "config_id": config["config_id"],
            "name": config["name"],
            "description": config.get("description"),
            "metadata": config["metadata"],
            "actions": config.get("actions", []),
            "datasetDetailsMap": all_datasets,
            "has_scores": has_scores,
            "created_at": config.get("created_at"),
            "updated_at": config.get("updated_at")
        })
    except Exception as e:
        logger.error(f"Error loading configuration {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/empty-structure", methods=["GET"])
def get_empty_structure():
    """
    Get minimal SSPI structure with three blank pillars (no categories or indicators).

    Returns a blank canvas with 3 empty pillar slots. All name and code fields are
    empty strings - users fill these in as they build their custom SSPI.

    Returns:
        JSON with success status, empty metadata (SSPI root + 3 blank pillars), and dataset details map
    """
    try:
        # Create blank structure: SSPI root + 3 empty pillars
        # All names and codes are empty strings - users fill them in
        empty_metadata = [
            {
                "DocumentType": "SSPIDetail",
                "ItemType": "SSPI",
                "ItemCode": "SSPI",
                "ItemName": "",
                "Children": [],
                "PillarCodes": [],
                "TreeIndex": [0, -1, -1, -1],
                "TreePath": "sspi",
                "ItemOrder": 0
            },
            {
                "DocumentType": "PillarDetail",
                "ItemType": "Pillar",
                "ItemCode": "",
                "ItemName": "",
                "Pillar": "",
                "PillarCode": "",
                "CategoryCodes": [],
                "Children": [],
                "TreeIndex": [0, 0, -1, -1],
                "TreePath": "",
                "ItemOrder": 0
            },
            {
                "DocumentType": "PillarDetail",
                "ItemType": "Pillar",
                "ItemCode": "",
                "ItemName": "",
                "Pillar": "",
                "PillarCode": "",
                "CategoryCodes": [],
                "Children": [],
                "TreeIndex": [0, 1, -1, -1],
                "TreePath": "",
                "ItemOrder": 1
            },
            {
                "DocumentType": "PillarDetail",
                "ItemType": "Pillar",
                "ItemCode": "",
                "ItemName": "",
                "Pillar": "",
                "PillarCode": "",
                "CategoryCodes": [],
                "Children": [],
                "TreeIndex": [0, 2, -1, -1],
                "TreePath": "",
                "ItemOrder": 2
            }
        ]

        # Load dataset details map (users will need this to add indicators)
        org_details = sspi_metadata.organization_details()
        org_code_to_name = {
            org.get("OrganizationCode"): org.get("OrganizationName", "")
            for org in org_details
        }

        all_datasets_list = sspi_metadata.dataset_details()
        for dataset in all_datasets_list:
            org_code = dataset.get("Source", {}).get("OrganizationCode", "")
            if org_code and org_code in org_code_to_name:
                full_org_name = org_code_to_name[org_code]
                if "Source" not in dataset:
                    dataset["Source"] = {}
                dataset["Source"]["OrganizationName"] = full_org_name

        all_datasets = {d["DatasetCode"]: d for d in all_datasets_list}

        logger.info("Returned blank SSPI structure with 3 empty pillar slots")

        return jsonify({
            "success": True,
            "metadata": empty_metadata,
            "datasetDetailsMap": all_datasets,
            "has_scores": False  # Blank configurations have no scores
        })
    except Exception as e:
        logger.error(f"Error creating empty structure: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/prebuilt/<config_id>", methods=["GET"])
def get_prebuilt_configuration(config_id):
    """Get a pre-built SSPI configuration."""
    try:
        # Map of pre-built configurations
        prebuilt_configs = {
            'default': 'default-structure',
            'environment': 'default-structure',  # TODO: Create environment-focused config
            'economy': 'default-structure'  # TODO: Create economy-focused config
        }

        if config_id not in prebuilt_configs:
            return jsonify({
                "success": False,
                "error": "Pre-built configuration not found"
            }), 404

        # For now, all pre-built configs return default structure
        # TODO: Create actual pre-built configurations
        metadata_items = sspi_metadata.item_details()
        org_details = sspi_metadata.organization_details()
        org_code_to_name = {
            org.get("OrganizationCode"): org.get("OrganizationName", "")
            for org in org_details
        }
        all_datasets_list = sspi_metadata.dataset_details()
        for dataset in all_datasets_list:
            org_code = dataset.get("Source", {}).get("OrganizationCode", "")
            if org_code and org_code in org_code_to_name:
                full_org_name = org_code_to_name[org_code]
                if "Source" not in dataset:
                    dataset["Source"] = {}
                dataset["Source"]["OrganizationName"] = full_org_name

        all_datasets = {d["DatasetCode"]: d for d in all_datasets_list}

        return jsonify({
            "success": True,
            "metadata": metadata_items,
            "datasetDetailsMap": all_datasets
        })
    except Exception as e:
        logger.error(f"Error loading pre-built configuration: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/validate", methods=["POST"])
@owner_or_admin_required
def validate_configuration():
    """Validate a custom SSPI configuration."""
    try:
        data = request.get_json()

        if not data or 'metadata' not in data:
            return jsonify({"success": False, "error": "No metadata provided"}), 400

        metadata = data.get('metadata')

        # TODO: Implement actual validation logic
        # For now, always return valid
        return jsonify({
            "success": True,
            "valid": True,
            "errors": [],
            "warnings": []
        })
    except Exception as e:
        logger.error(f"Error validating configuration: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/update/<config_id>", methods=["PUT"])
@owner_or_admin_required
def update_configuration(config_id):
    """
    Update an existing configuration.

    Accepts partial updates - only provided fields will be updated.
    Allowed fields: name, description, metadata, actions

    Returns:
        JSON with success status
    """
    try:
        user_id = current_user.username
        updates = request.get_json()

        if not updates:
            return jsonify({"success": False, "error": "No updates provided"}), 400

        # Validate allowed fields
        allowed_fields = {"name", "description", "metadata", "actions"}
        provided_fields = set(updates.keys())
        invalid_fields = provided_fields - allowed_fields

        if invalid_fields:
            return jsonify({
                "success": False,
                "error": f"Invalid fields: {', '.join(invalid_fields)}. Allowed: {', '.join(allowed_fields)}"
            }), 400

        # Sanitize name and description if provided
        if "name" in updates:
            updates["name"] = sanitize_text_input(updates["name"], max_length=200, field_name="name")
        if "description" in updates and updates["description"]:
            updates["description"] = sanitize_text_input(updates["description"], max_length=1000, field_name="description", allow_newlines=True)

        # If metadata is being updated, clear the scored_hash since the config changed
        metadata_changed = "metadata" in updates

        # Update configuration
        success = sspi_custom_user_structure.update_config(
            config_id=config_id,
            username=user_id,
            updates=updates
        )

        if not success:
            return jsonify({
                "success": False,
                "error": "Configuration not found or no changes made"
            }), 404

        # Clear scored_hash if metadata changed (config needs to be re-scored)
        if metadata_changed:
            sspi_custom_user_structure.clear_scored_hash(config_id)
            logger.info(f"Cleared scored_hash for config {config_id} due to metadata change")

        logger.info(f"Updated configuration {config_id} for user {user_id}")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Configuration updated successfully"
        })
    except PermissionError as e:
        logger.error(f"Permission error updating config {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Access denied"}), 403
    except ValueError as e:
        logger.error(f"Validation error updating config {config_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error updating configuration {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/duplicate/<config_id>", methods=["POST"])
@owner_or_admin_required
def duplicate_configuration(config_id):
    """
    Duplicate an existing configuration.

    Request body should include:
        - new_name: Name for the duplicated configuration

    Returns:
        JSON with new config_id
    """
    try:
        user_id = current_user.username
        data = request.get_json()

        if not data or 'new_name' not in data:
            return jsonify({"success": False, "error": "new_name is required"}), 400

        new_name = data.get('new_name')

        if not new_name or not isinstance(new_name, str) or len(new_name.strip()) == 0:
            return jsonify({"success": False, "error": "new_name must be a non-empty string"}), 400

        # Duplicate configuration
        new_config_id = sspi_custom_user_structure.duplicate_config(
            config_id=config_id,
            username=user_id,
            new_name=new_name
        )

        logger.info(f"Duplicated configuration {config_id} to {new_config_id} for user {user_id}")

        return jsonify({
            "success": True,
            "original_config_id": config_id,
            "new_config_id": new_config_id,
            "message": "Configuration duplicated successfully"
        })
    except PermissionError as e:
        logger.error(f"Permission error duplicating config {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Access denied or configuration not found"}), 403
    except ValueError as e:
        logger.error(f"Validation error duplicating config {config_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error duplicating configuration {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/delete/<config_id>", methods=["DELETE"])
@owner_or_admin_required
def delete_configuration(config_id):
    """
    Delete a configuration and its associated scoring results.

    Returns:
        JSON with success status
    """
    try:
        user_id = current_user.username

        # Delete configuration (verifies ownership internally)
        deleted = sspi_custom_user_structure.delete_config(
            config_id=config_id,
            username=user_id
        )

        if not deleted:
            return jsonify({
                "success": False,
                "error": "Configuration not found or access denied"
            }), 404

        # Clear legacy scoring results (sspi_custom_user_data)
        # Note: sspi_custom_item_data and sspi_custom_panel_data are cached by
        # config_hash only - no eager deletion on config delete. Cached results
        # remain available for other configs with the same hash.
        cleared_legacy = sspi_custom_user_data.clear_config_results(config_id)

        logger.info(f"Deleted configuration {config_id} for user {user_id}")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Configuration deleted successfully"
        })
    except PermissionError as e:
        logger.error(f"Permission error deleting config {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Access denied"}), 403
    except ValueError as e:
        logger.error(f"Validation error deleting config {config_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error deleting configuration {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/export/<config_id>", methods=["GET"])
@owner_or_admin_required
def export_configuration(config_id):
    """
    Export a configuration as JSON file.

    Returns:
        JSON file download with configuration data
    """
    try:
        user_id = current_user.username
        # Fetch configuration (verify ownership)
        config = sspi_custom_user_structure.find_by_config_id(config_id, username=user_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found or access denied"
            }), 404

        # Remove MongoDB _id field if present
        if "_id" in config:
            del config["_id"]
        # Prepare export data
        export_data = {
            "export_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "configuration": config
        }
        logger.info(f"Exported configuration {config_id} for user {user_id}")
        # Return as downloadable JSON
        response = app.make_response(json.dumps(export_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=sspi-config-{config_id}.json'
        return response
    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error exporting configuration {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@customize_bp.route("/score-stream/<job_id>", methods=["GET"])
@owner_or_admin_required
def score_stream(job_id):
    """
    SSE endpoint for streaming scoring progress.

    Requires authentication - users must be logged in and own the job.

    Events:
    - progress: {"percent": 25, "message": "Scoring indicator BIODIV..."}
    - indicator_start: {"code": "BIODIV", "name": "...", "index": 1, "total": 54}
    - indicator_complete: {"code": "BIODIV", "countries": 57, "duration_ms": 150}
    - complete: {"success": true, "total_scores": 12345, "duration_ms": 8500}
    - error: {"message": "...", "code": "VALIDATION_ERROR"}
    """
    user_id = current_user.username

    # Verify job exists and belongs to user
    job = get_job(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404

    if job.user_id != user_id:
        return jsonify({"success": False, "error": "Access denied"}), 403

    def generate():
        for event in generate_sse_events(job_id):
            yield event

    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )


@customize_bp.route("/score-stream", methods=["GET"])
@owner_or_admin_required
def score_stream_legacy():
    """
    Legacy SSE endpoint (no job_id) - returns error directing to new endpoint.
    """
    return jsonify({
        "success": False,
        "error": "Please use /score-stream/<job_id> endpoint. Get job_id from /score POST response."
    }), 400


@customize_bp.route("/job/<job_id>", methods=["GET"])
@owner_or_admin_required
def get_job_status(job_id):
    """
    Get status of a scoring job.

    Returns:
        JSON with job status, progress, and result if complete
    """
    try:
        user_id = current_user.username

        job = get_job(job_id)
        if not job:
            return jsonify({"success": False, "error": "Job not found"}), 404

        if job.user_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        response = {
            "success": True,
            "job_id": job_id,
            "config_id": job.config_id,
            "config_hash": job.config_hash,
            "status": job.status.value,
            "progress": job.progress,
            "message": job.message,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        }

        if job.status == JobStatus.COMPLETE and job.result:
            response["total_scores"] = len(job.result.get("results", []))
            response["cached"] = job.result.get("cached", False)

        if job.status == JobStatus.ERROR:
            response["error"] = job.error

        return jsonify(response)

    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@customize_bp.route("/score", methods=["POST"])
@owner_or_admin_required
def score_custom_configuration():
    """
    Score a custom SSPI configuration.

    REQUIRES AUTHENTICATION - users must be logged in to generate scores.

    Accepts either:
    1. config_id: Score a saved configuration
    2. metadata + actions: Score an ad-hoc configuration

    Request body:
    {
        "config_id": "optional - score saved config",
        "metadata": [...],  // Required if no config_id
        "actions": [...]    // Optional action history
    }

    Returns:
    {
        "success": true,
        "config_id": "...",
        "config_hash": "...",
        "job_id": "...",
        "stream_url": "/api/v1/customize/score-stream/<job_id>"
    }
    """
    try:
        user_id = current_user.username # Get authenticated user_id (decorator ensures user is logged in)
        json_data = request.get_json()

        if not json_data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        config_id = json_data.get("config_id")
        custom_metadata = json_data.get("metadata", [])
        actions = json_data.get("actions", [])

        # Determine if this is a saved config or ad-hoc
        if config_id:
            # Saved config - verify ownership
            config = sspi_custom_user_structure.find_by_config_id(config_id, username=user_id)
            if not config:
                return jsonify({
                    "success": False,
                    "error": "Configuration not found or access denied"
                }), 404

            custom_metadata = config["metadata"]
            actions = config.get("actions", [])
            logger.info(f"Scoring saved configuration {config_id} for user {user_id}")
        else:
            # Ad-hoc scoring (authenticated user, but not saved)
            if not custom_metadata:
                return jsonify({"success": False, "error": "No metadata provided"}), 400

            config_id = f"adhoc_{user_id}_{secrets.token_hex(8)}"
            logger.info(f"Scoring ad-hoc configuration for user {user_id}")

        # Validate metadata structure
        if not isinstance(custom_metadata, list) or len(custom_metadata) == 0:
            return jsonify({"success": False, "error": "metadata must be a non-empty list"}), 400

        # Quick validation before starting job
        validation_result = validate_custom_metadata(
            custom_metadata,
            validate_score_functions=False  # Full validation in background job
        )
        if not validation_result.valid:
            error_msgs = [e.message for e in validation_result.errors[:3]]
            return jsonify({
                "success": False,
                "error": f"Invalid configuration: {'; '.join(error_msgs)}",
                "validation_errors": validation_result.to_dict()["errors"]
            }), 400

        # Compute config hash for cache lookup
        config_hash = compute_config_hash(custom_metadata)

        # Start background scoring job
        job_id = start_scoring_job(
            config_id=config_id,
            metadata=custom_metadata,
            actions=actions,
            user_id=user_id
        )

        logger.info(
            f"Scoring job {job_id} started for config {config_id} "
            f"(hash: {config_hash[:8]}...) with {len(custom_metadata)} items"
        )

        return jsonify({
            "success": True,
            "config_id": config_id,
            "config_hash": config_hash,
            "job_id": job_id,
            "message": "Scoring initiated. Connect to stream_url for progress updates.",
            "stream_url": f"/api/v1/customize/score-stream/{job_id}"
        })

    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error scoring configuration: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500


@customize_bp.route("/results/<config_id>", methods=["GET"])
@owner_or_admin_required
def get_results_summary(config_id):
    """
    Get summary of scoring results for a configuration.

    Args:
        config_id: Configuration identifier

    Returns:
        JSON with has_results flag and statistics about cached results
    """
    try:
        user_id = current_user.username

        # Verify config exists and user owns it
        config = sspi_custom_user_structure.find_by_config_id(config_id, username=user_id)

        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found or access denied"
            }), 404

        # Compute config_hash from metadata to look up cached results
        metadata = config.get("metadata")
        if not metadata:
            return jsonify({
                "success": True,
                "config_id": config_id,
                "has_results": False,
                "message": "Configuration has no metadata"
            })

        config_hash = compute_config_hash(metadata)

        # Check if results exist in sspi_custom_item_data (by config_hash)
        has_results = sspi_custom_item_data.has_cached_results(config_hash)

        if not has_results:
            return jsonify({
                "success": True,
                "config_id": config_id,
                "has_results": False,
                "message": "No scoring results found for this configuration"
            })

        # Get statistics about results from sspi_custom_item_data
        stats = sspi_custom_item_data.get_cache_stats(config_hash)

        logger.info(f"Retrieved results summary for config {config_id} (hash {config_hash[:8]}..., user {user_id})")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "config_hash": config_hash,
            "has_results": True,
            "stats": stats
        })
    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error getting results for {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@customize_bp.route("/results/<config_id>/chart-data", methods=["GET"])
@owner_or_admin_required
def get_chart_data(config_id):
    """
    Get chart data for a specific item in a scored configuration.

    Query parameters:
        - item_code: SSPI item code (required)
        - countries: Comma-separated list of country codes (optional)
        - years: Comma-separated list of years (optional)

    Returns:
        JSON with time series data formatted for sspi-panel-chart.js
    """
    try:
        user_id = current_user.username
        # Verify config exists and user owns it
        config = sspi_custom_user_structure.find_by_config_id(config_id, username=user_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found or access denied"
            }), 404

        # Compute config_hash from metadata to look up cached results
        metadata = config.get("metadata")
        if not metadata:
            return jsonify({
                "success": True,
                "config_id": config_id,
                "item_code": request.args.get('item_code', ''),
                "data": [],
                "message": "Configuration has no metadata"
            })

        config_hash = compute_config_hash(metadata)

        # Get query parameters
        item_code = request.args.get('item_code')
        if not item_code:
            return jsonify({"success": False, "error": "item_code parameter is required"}), 400
        # Parse optional filters
        countries_param = request.args.get('countries', '')
        years_param = request.args.get('years', '')
        country_codes = [c.strip() for c in countries_param.split(',') if c.strip()] if countries_param else None
        years = [int(y.strip()) for y in years_param.split(',') if y.strip()] if years_param else None

        # Get results from sspi_custom_item_data using config_hash
        filtered_results = sspi_custom_item_data.get_results_by_item(
            config_hash=config_hash,
            item_code=item_code,
            country_codes=country_codes,
            years=years
        )

        if not filtered_results:
            return jsonify({
                "success": True,
                "config_id": config_id,
                "item_code": item_code,
                "data": [],
                "message": "No data found for this item"
            })

        # Format for chart (group by country)
        chart_data = {}
        for result in filtered_results:
            country = result.get("country_code")
            year = result.get("year")
            score = result.get("score")
            if country not in chart_data:
                chart_data[country] = []
            chart_data[country].append({
                "year": year,
                "score": score,
                "rank": result.get("rank")
            })
        # Sort each country's data by year
        for country in chart_data:
            chart_data[country].sort(key=lambda x: x["year"])
        logger.info(f"Retrieved chart data for config {config_id} (hash {config_hash[:8]}...), item {item_code} (user {user_id})")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "item_code": item_code,
            "item_name": filtered_results[0].get("item_name") if filtered_results else "",
            "data": chart_data,
            "total_points": len(filtered_results)
        })
    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid parameter: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error getting chart data for {config_id}/{item_code}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# ============================================================================
# Panel Chart Endpoint for SSPIPanelChart
# ============================================================================

@customize_bp.route("/panel/score/<item_code>", methods=["GET"])
def get_custom_panel_score(item_code):
    """
    Serve custom scoring results for SSPIPanelChart.

    This endpoint returns data in the same format as /api/v1/panel/score/<item_code>
    but for custom SSPI configurations.

    Query parameters:
        - config_hash: Required. SHA-256 hash of the custom configuration.
        - config_id: Optional. Configuration ID for retrieving metadata.

    Returns:
        JSON matching standard panel score format:
        {
            "data": [...],           # Line chart documents
            "tree": {...},           # Hierarchical navigation tree
            "itemCode": "SSPI",
            "itemName": "Custom SSPI",
            "itemType": "SSPI",
            "title": "Custom SSPI Score",
            "labels": [2000, 2001, ..., 2023],
            "groupOptions": [...],
            "countryGroupMap": {...}
        }
    """
    try:
        config_hash = request.args.get("config_hash")
        config_id = request.args.get("config_id")

        if not config_hash:
            return jsonify({
                "success": False,
                "error": "config_hash parameter is required"
            }), 400

        # Validate config_hash format
        if not re.match(r'^[a-f0-9]{32}$', config_hash):
            return jsonify({
                "success": False,
                "error": "config_hash must be 32 lowercase hex characters"
            }), 400

        # Check if line data exists
        if not sspi_custom_panel_data.has_line_data(config_hash):
            return jsonify({
                "success": False,
                "error": "No scoring results found for this configuration. Please score the configuration first."
            }), 404

        # Get line data for the requested item
        line_data = sspi_custom_panel_data.get_line_data(
            config_hash=config_hash,
            item_code=item_code
        )

        if not line_data:
            return jsonify({
                "success": False,
                "error": f"No data found for item {item_code}"
            }), 404

        # Get custom metadata for tree building
        custom_metadata = None
        if config_id:
            # Try to get metadata from sspi_custom_user_structure
            config = sspi_custom_user_structure.find_by_config_id(config_id)
            if config:
                custom_metadata = config.get("metadata", [])

        # If no config_id or config not found, try to infer from line data
        if not custom_metadata:
            # Get all unique item codes from line data to build scored_item_codes set
            all_line_data = sspi_custom_panel_data.get_line_data(config_hash)
            scored_item_codes = {doc["ICode"] for doc in all_line_data}

            # Use default SSPI metadata as base, filtered to scored items
            custom_metadata = sspi_metadata.item_details(
                indicator_filter=list(scored_item_codes)
            )

        # Build tree from custom metadata
        scored_items = {doc["ICode"] for doc in line_data}
        # Get all scored items for proper tree building
        all_line_data = sspi_custom_panel_data.get_line_data(config_hash)
        all_scored_items = {doc["ICode"] for doc in all_line_data}

        tree = build_custom_tree(custom_metadata, all_scored_items)

        if not tree:
            # Fallback: create minimal tree with just the requested item
            item_name = line_data[0].get("IName", item_code) if line_data else item_code
            tree = {
                "ItemCode": item_code,
                "ItemName": item_name,
                "Children": []
            }

        # Get item metadata
        item_name = line_data[0].get("IName", item_code) if line_data else item_code

        # Determine item type from tree or metadata
        item_type = "SSPI"
        for item in custom_metadata:
            if item.get("ItemCode") == item_code:
                item_type = item.get("ItemType", "SSPI")
                break

        # Get country groups from metadata
        country_groups = sspi_metadata.country_groups()
        country_group_map = sspi_metadata.country_group_map()

        # Build response in standard panel format
        years = list(range(2000, 2024))

        logger.info(
            f"Serving custom panel data for item {item_code} "
            f"(config_hash: {config_hash[:8]}..., {len(line_data)} country records)"
        )

        return jsonify({
            "success": True,
            "data": line_data,
            "tree": tree,
            "itemCode": item_code,
            "itemName": item_name,
            "itemType": item_type,
            "title": f"{item_name} Score",
            "labels": years,
            "groupOptions": country_groups,
            "countryGroupMap": country_group_map
        })

    except Exception as e:
        logger.error(f"Error serving custom panel data for {item_code}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500


# ============================================================================
# Session Management Endpoints - REMOVED
# ============================================================================
# Session management migrated to client-side localStorage.
# See REFACTOR_SESSION_TO_LOCALSTORAGE.md for details.
