import csv
import io
import logging

from flask import Blueprint, jsonify, request

from sspi_flask_app.auth.decorators import owner_or_admin_required
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.models.database import (
    sspi_custom_user_data,
    sspi_custom_user_structure,
    sspi_item_data,
    sspi_metadata,
)
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from sspi_flask_app.models.rank import SSPIRankingTable
from sspi_flask_app.models.sspi import FastSSPI

logger = logging.getLogger(__name__)

customize_bp = Blueprint("customize_bp", __name__,
                        template_folder="templates",
                        static_folder="static",
                        url_prefix="/customize")



@customize_bp.route("/datasets", methods=["GET"])
def list_datasets():
    try:
        search_term = request.args.get("search", "").strip().lower()
        limit = int(request.args.get("limit", 100))

        # Build organization code-to-name lookup table (code is the key)
        org_details = sspi_metadata.organization_details()
        org_code_to_name = {
            org.get("OrganizationCode"): org.get("OrganizationName", "")
            for org in org_details
        }

        # Get all dataset details from metadata
        all_datasets = sspi_metadata.dataset_details()

        # Enrich each dataset with full organization name from lookup
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


def validate_custom_metadata(metadata_items: list) -> dict:
    """
    Validate custom SSPI metadata format (same format as `sspi metadata item`).

    :param metadata_items: List of metadata items (SSPI, Pillars, Categories, Indicators)
    :return: Dict with 'valid' boolean and 'errors' list
    """
    errors = []
    if not metadata_items:
        return {"valid": False, "errors": ["Metadata cannot be empty"]}
    # Check for SSPI root
    sspi_items = [item for item in metadata_items if item.get("ItemType") == "SSPI"]
    if not sspi_items:
        errors.append("Missing SSPI root item")
    # Validate required fields for each item type
    for item in metadata_items:
        item_type = item.get("ItemType")
        item_code = item.get("ItemCode")
        if not item_type:
            errors.append(f"Missing ItemType for item: {item}")
            continue
        if not item_code:
            errors.append(f"Missing ItemCode for {item_type}")
            continue
        # Required fields for all items
        if "ItemName" not in item:
            errors.append(f"Missing ItemName for {item_code}")
        if "Children" not in item:
            errors.append(f"Missing Children for {item_code}")
        # Type-specific validation
        if item_type == "SSPI":
            if "PillarCodes" not in item:
                errors.append(f"Missing PillarCodes in SSPI")
        elif item_type == "Pillar":
            if "CategoryCodes" not in item:
                errors.append(f"Missing CategoryCodes in pillar {item_code}")
        elif item_type == "Category":
            if "IndicatorCodes" not in item:
                errors.append(f"Missing IndicatorCodes in category {item_code}")
        elif item_type == "Indicator":
            if "DatasetCodes" not in item:
                errors.append(f"Missing DatasetCodes in indicator {item_code}")
    item_codes = [item.get("ItemCode") for item in metadata_items if item.get("ItemCode")]
    if len(item_codes) != len(set(item_codes)):
        errors.append("Duplicate ItemCodes found in metadata")
    return {"valid": len(errors) == 0, "errors": errors}


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

        # Get all available datasets - they already have OrganizationCode in Source
        all_datasets_list = sspi_metadata.dataset_details()

        # Enrich each dataset with full organization name from lookup
        for dataset in all_datasets_list:
            org_code = dataset.get("Source", {}).get("OrganizationCode", "")
            # If we have a code and can look up the full name, enrich it
            if org_code and org_code in org_code_to_name:
                full_org_name = org_code_to_name[org_code]
                # Ensure Source.OrganizationName is set to the full name
                if "Source" not in dataset:
                    dataset["Source"] = {}
                dataset["Source"]["OrganizationName"] = full_org_name

        all_datasets = {d["DatasetCode"]: d for d in all_datasets_list}

        # Enrich indicators with full dataset details
        for item in metadata_items:
            if item.get("ItemType") == "Indicator" and "DatasetCodes" in item:
                dataset_codes = item.get("DatasetCodes", [])
                # Build DatasetDetails array with full dataset objects
                item["DatasetDetails"] = [
                    all_datasets.get(code, {"DatasetCode": code, "DatasetName": code})
                    for code in dataset_codes
                ]

        logger.info(f"Loaded default SSPI structure with {len(metadata_items)} items and {len(all_datasets_list)} datasets")
        return jsonify({
            "success": True,
            "metadata": metadata_items,
            "all_datasets": all_datasets_list
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
        return jsonify({
            "success": True,
            "indicators": filtered,
            "total_count": len(filtered)
        })
    except Exception as e:
        logger.error(f"Error listing indicators: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/save", methods=["POST"])
@owner_or_admin_required
def save_configuration():
    """
    Save a new custom SSPI configuration.
    Requires authentication - user_id is automatically injected from logged-in user.

    Expected JSON payload:
    {
        "name": "My Custom SSPI",
        "metadata": [...]  // Full metadata array (SSPI, Pillars, Categories, Indicators)
    }
    Returns:
    {
        "success": true,
        "config_id": "generated_config_id",
        "message": "Configuration saved successfully"
    }
    """
    try:
        # Get authenticated user_id and admin status from decorator
        user_id = request.user_id
        is_admin = request.is_admin

        data = request.get_json()

        # Validate required fields
        if "name" not in data:
            return jsonify({"error": "Configuration name is required"}), 400
        if "metadata" not in data:
            return jsonify({"error": "Metadata is required"}), 400

        name = data["name"]
        metadata = data["metadata"]

        # Validate metadata format
        validation = validate_custom_metadata(metadata)
        if not validation["valid"]:
            return jsonify({
                "error": "Invalid metadata format",
                "validation_errors": validation["errors"]
            }), 400

        config_id = sspi_custom_user_structure.create_config(
            name=name,
            metadata=metadata,
            user_id=user_id
        )
        logger.info(f"Created custom metadata configuration: {config_id} for user {user_id} (admin: {is_admin})")
        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Configuration saved successfully"
        })
    except ValueError as e:
        logger.error(f"Validation error saving configuration: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except InvalidDocumentFormatError as e:
        logger.error(f"Validation error saving configuration: {str(e)}")
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/list", methods=["GET"])
@owner_or_admin_required
def list_configurations():
    """
    List saved configuration names for a user.
    Requires authentication - user_id is automatically injected from logged-in user.

    Admins can see all configurations across all users.
    Regular users can only see their own configurations.

    Returns:
    {
        "success": true,
        "configurations": [
            {"config_id": "abc123", "name": "My Custom SSPI"},
            {"config_id": "def456", "name": "Alternative Structure"}
        ]
    }
    """
    try:
        # Get authenticated user_id and admin status from decorator
        user_id = request.user_id
        is_admin = request.is_admin

        configurations = sspi_custom_user_structure.list_config_names(user_id=user_id, is_admin=is_admin)
        return jsonify({
            "success": True,
            "configurations": configurations
        })
    except ValueError as e:
        logger.error(f"Validation error listing configurations: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/load/<config_id>", methods=["GET"])
@owner_or_admin_required
def load_configuration(config_id):
    """
    Load a specific configuration by ID with ownership verification.
    Requires authentication - user_id is automatically injected from logged-in user.

    Admins can load any configuration.
    Regular users can only load their own configurations.

    Returns:
    {
        "success": true,
        "configuration": {
            "config_id": "abc123",
            "name": "My Custom SSPI",
            "metadata": [...],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }
    """
    try:
        # Get authenticated user_id and admin status from decorator
        user_id = request.user_id
        is_admin = request.is_admin

        configuration = sspi_custom_user_structure.find_by_config_id(config_id, user_id, is_admin=is_admin)
        if not configuration:
            return jsonify({"error": "Configuration not found or access denied"}), 404

        return jsonify({
            "success": True,
            "configuration": configuration
        })
    except Exception as e:
        logger.error(f"Error loading configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/update/<config_id>", methods=["PUT"])
@owner_or_admin_required
def update_configuration(config_id):
    """
    Update an existing configuration with ownership verification.
    Requires authentication - user_id is automatically injected from logged-in user.

    Admins can update any configuration.
    Regular users can only update their own configurations.

    Expected JSON payload:
    {
        "name": "Updated Name",        // Optional
        "metadata": [...]              // Optional
    }

    Returns:
    {
        "success": true,
        "message": "Configuration updated successfully"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()

        # Get authenticated user_id and admin status from decorator
        user_id = request.user_id
        is_admin = request.is_admin

        # Remove user_id from updates dict if present (ownership is enforced by decorator)
        updates = {k: v for k, v in data.items() if k != "user_id"}

        success = sspi_custom_user_structure.update_config(config_id, user_id, updates, is_admin=is_admin)
        if success:
            logger.info(f"Updated custom structure configuration: {config_id} by user {user_id} (admin: {is_admin})")
            return jsonify({
                "success": True,
                "message": "Configuration updated successfully"
            })
        else:
            return jsonify({"error": "Failed to update configuration"}), 500

    except ValueError as e:
        logger.error(f"Validation error updating configuration {config_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        logger.error(f"Permission error updating configuration {config_id}: {str(e)}")
        return jsonify({"error": str(e)}), 403
    except InvalidDocumentFormatError as e:
        logger.error(f"Validation error updating configuration {config_id}: {str(e)}")
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error updating configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/delete/<config_id>", methods=["DELETE"])
@owner_or_admin_required
def delete_configuration(config_id):
    """
    Delete a configuration with ownership verification.
    Requires authentication - user_id is automatically injected from logged-in user.

    Admins can delete any configuration.
    Regular users can only delete their own configurations.

    Returns:
    {
        "success": true,
        "message": "Configuration deleted successfully"
    }
    """
    try:
        # Get authenticated user_id and admin status from decorator
        user_id = request.user_id
        is_admin = request.is_admin

        success = sspi_custom_user_structure.delete_config(config_id, user_id, is_admin=is_admin)
        if success:
            logger.info(f"Deleted custom structure configuration: {config_id} by user {user_id} (admin: {is_admin})")
            return jsonify({
                "success": True,
                "message": "Configuration deleted successfully"
            })
        else:
            return jsonify({"error": "Configuration not found"}), 404

    except ValueError as e:
        logger.error(f"Validation error deleting configuration {config_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        logger.error(f"Permission error deleting configuration {config_id}: {str(e)}")
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        logger.error(f"Error deleting configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/duplicate/<config_id>", methods=["POST"])
@owner_or_admin_required
def duplicate_configuration(config_id):
    """
    Create a copy of an existing configuration with ownership verification.
    Requires authentication - user_id is automatically injected from logged-in user.

    Admins can duplicate any configuration (copy will be owned by the admin).
    Regular users can only duplicate their own configurations.

    Expected JSON payload:
    {
        "name": "Copy of My Custom SSPI"  // REQUIRED - new configuration name
    }

    Returns:
    {
        "success": true,
        "config_id": "new_config_id",
        "message": "Configuration duplicated successfully"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()

        if "name" not in data:
            return jsonify({"error": "New configuration name is required"}), 400

        # Get authenticated user_id and admin status from decorator
        user_id = request.user_id
        is_admin = request.is_admin
        new_name = data["name"]

        new_config_id = sspi_custom_user_structure.duplicate_config(config_id, user_id, new_name, is_admin=is_admin)

        logger.info(f"Duplicated configuration {config_id} to {new_config_id} by user {user_id} (admin: {is_admin})")
        return jsonify({
            "success": True,
            "config_id": new_config_id,
            "message": "Configuration duplicated successfully"
        })

    except ValueError as e:
        logger.error(f"Validation error duplicating configuration {config_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except PermissionError as e:
        logger.error(f"Permission error duplicating configuration {config_id}: {str(e)}")
        return jsonify({"error": str(e)}), 403
    except InvalidDocumentFormatError as e:
        logger.error(f"Validation error duplicating configuration {config_id}: {str(e)}")
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error duplicating configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/export/<config_id>", methods=["GET"])
@owner_or_admin_required
def export_configuration(config_id):
    """
    Export a configuration in JSON format with ownership verification.
    Requires authentication - user_id is automatically injected from logged-in user.

    Admins can export any configuration.
    Regular users can only export their own configurations.

    Query parameters:
    - format: json (default) - export format

    Returns the configuration metadata in JSON format.
    """
    try:
        # Get authenticated user_id and admin status from decorator
        user_id = request.user_id
        is_admin = request.is_admin
        export_format = request.args.get("format", "json").lower()

        configuration = sspi_custom_user_structure.find_by_config_id(config_id, user_id, is_admin=is_admin)
        if not configuration:
            return jsonify({"error": "Configuration not found or access denied"}), 404

        if export_format == "json":
            return jsonify({
                "success": True,
                "config_id": config_id,
                "name": configuration["name"],
                "metadata": configuration["metadata"],
                "exported_at": configuration["updated_at"]
            })
        else:
            return jsonify({"error": f"Unsupported export format: {export_format}. Only 'json' is supported."}), 400

    except Exception as e:
        logger.error(f"Error exporting configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/score/<config_id>", methods=["GET"])
def score_custom_configuration():
    scores_data = []
    return parse_json(scores_data)

