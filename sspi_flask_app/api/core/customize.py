import csv
import os
import json
import io
import logging
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, jsonify, request, current_app as app
from flask_login import login_required

from sspi_flask_app.auth.decorators import owner_or_admin_required
from sspi_flask_app.utils import session_manager
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


def validate_custom_metadata(metadata_items: list):
    pass # throw error if not valid


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
        user_id = request.__getattribute__("user_id")
        data = request.get_json()

        if not data or 'metadata' not in data:
            return jsonify({"success": False, "error": "No metadata provided"}), 400

        config_name = data.get('name', f'Custom SSPI {user_id}')
        metadata = data.get('metadata')
        actions = data.get('actions', [])

        # Validate inputs
        if not isinstance(metadata, list):
            return jsonify({"success": False, "error": "metadata must be a list"}), 400

        if not isinstance(actions, list):
            return jsonify({"success": False, "error": "actions must be a list"}), 400

        # Save to database
        config_id = sspi_custom_user_structure.create_config(
            name=config_name,
            metadata=metadata,
            username=user_id,
            actions=actions
        )

        logger.info(f"Saved configuration {config_id} for user {user_id} with {len(metadata)} items and {len(actions)} actions")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Configuration saved successfully"
        })
    except ValueError as e:
        logger.error(f"Validation error saving configuration: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/list", methods=["GET"])
@owner_or_admin_required
def list_configurations():
    """List all saved configurations for the current user."""
    try:
        user_id = request.__getattribute__("user_id")

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
        user_id = request.__getattribute__("user_id")

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

        logger.info(f"Loaded configuration {config_id} for user {user_id}")

        return jsonify({
            "success": True,
            "config_id": config["config_id"],
            "name": config["name"],
            "metadata": config["metadata"],
            "actions": config.get("actions", []),
            "datasetDetailsMap": all_datasets,
            "created_at": config.get("created_at"),
            "updated_at": config.get("updated_at")
        })
    except Exception as e:
        logger.error(f"Error loading configuration {config_id}: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@customize_bp.route("/empty-structure", methods=["GET"])
def get_empty_structure():
    """
    Get minimal SSPI structure with only pillars (no categories or indicators).

    Returns:
        JSON with success status, empty metadata (just SSPI root + pillars), and dataset details map
    """
    try:
        # Create minimal structure: SSPI root + 3 pillars only
        empty_metadata = [
            {
                "ItemType": "SSPI",
                "ItemCode": "SSPI",
                "ItemName": "Sustainable and Shared-Prosperity Policy Index",
                "Children": ["SUS", "MS", "PG"]
            },
            {
                "ItemType": "Pillar",
                "ItemCode": "SUS",
                "ItemName": "Sustainability",
                "PillarCode": "SUS",
                "CategoryCodes": [],
                "IndicatorCodes": [],
                "Children": []
            },
            {
                "ItemType": "Pillar",
                "ItemCode": "MS",
                "ItemName": "Market Structure",
                "PillarCode": "MS",
                "CategoryCodes": [],
                "IndicatorCodes": [],
                "Children": []
            },
            {
                "ItemType": "Pillar",
                "ItemCode": "PG",
                "ItemName": "Public Goods",
                "PillarCode": "PG",
                "CategoryCodes": [],
                "IndicatorCodes": [],
                "Children": []
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

        logger.info("Returned empty SSPI structure with 3 pillars")

        return jsonify({
            "success": True,
            "metadata": empty_metadata,
            "datasetDetailsMap": all_datasets
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
    Allowed fields: name, metadata, actions

    Returns:
        JSON with success status
    """
    try:
        user_id = request.__getattribute__("user_id")
        updates = request.get_json()

        if not updates:
            return jsonify({"success": False, "error": "No updates provided"}), 400

        # Validate allowed fields
        allowed_fields = {"name", "metadata", "actions"}
        provided_fields = set(updates.keys())
        invalid_fields = provided_fields - allowed_fields

        if invalid_fields:
            return jsonify({
                "success": False,
                "error": f"Invalid fields: {', '.join(invalid_fields)}. Allowed: {', '.join(allowed_fields)}"
            }), 400

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
        user_id = request.__getattribute__("user_id")
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
        user_id = request.__getattribute__("user_id")

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

        # Clear associated scoring results
        cleared_count = sspi_custom_user_data.clear_config_results(config_id)

        logger.info(f"Deleted configuration {config_id} and {cleared_count} result records for user {user_id}")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": f"Configuration and {cleared_count} result records deleted successfully"
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
        user_id = request.__getattribute__("user_id")

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


@customize_bp.route("/score-stream", methods=["GET"])
@owner_or_admin_required
def score_stream():
    """
    SSE endpoint for streaming scoring progress (test stream).

    Requires authentication - users must be logged in to score configurations.
    """
    import time

    def generate():
        # Test stream - simulate scoring progress
        steps = [
            (10, "Validating configuration..."),
            (20, "Loading indicator data..."),
            (40, "Computing scores for Sustainability pillar..."),
            (60, "Computing scores for Market Structure pillar..."),
            (80, "Computing scores for Public Goods pillar..."),
            (90, "Aggregating results..."),
            (100, "Finalizing scores...")
        ]

        for progress, message in steps:
            data = {
                "progress": progress,
                "message": message
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.5)  # Simulate processing time

        # Send completion event
        completion_data = {
            "progress": 100,
            "message": "Scoring complete!",
            "success": True
        }
        yield f"event: complete\ndata: {json.dumps(completion_data)}\n\n"

    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@customize_bp.route("/score", methods=["POST"])
@owner_or_admin_required
def score_custom_configuration():
    """
    Score a custom SSPI configuration.

    REQUIRES AUTHENTICATION - users must be logged in to generate scores.

    Accepts either:
    1. config_id: Score a saved configuration
    2. metadata + actions: Score an ad-hoc configuration

    Returns:
        JSON with success status and stream URL
    """
    try:
        # Get authenticated user_id (decorator ensures user is logged in)
        user_id = request.__getattribute__("user_id")
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

        # Save to file for debugging
        filepath = Path(os.path.join(app.root_path, "custom-sspi.json"))
        logger.info(f"Saving custom SSPI to: {filepath}")
        filepath.write_text(json.dumps({
            "config_id": config_id,
            "user_id": user_id,
            "metadata": custom_metadata,
            "actions": actions
        }, indent=2))

        # TODO: Implement actual scoring logic
        # For now, just return success and point to stream
        # In future: trigger background job here

        logger.info(f"Scoring initiated for config {config_id} with {len(custom_metadata)} items")

        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Scoring initiated. Connect to /score-stream for progress updates.",
            "stream_url": "/api/v1/customize/score-stream"
        })
    except AttributeError:
        return jsonify({"success": False, "error": "No user_id in request"}), 401
    except Exception as e:
        logger.error(f"Error scoring configuration: {str(e)}")
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
        user_id = request.__getattribute__("user_id")

        # Verify config exists and user owns it
        config = sspi_custom_user_structure.find_by_config_id(config_id, username=user_id)

        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found or access denied"
            }), 404

        # Check if results exist
        has_results = sspi_custom_user_data.config_has_results(config_id)

        if not has_results:
            return jsonify({
                "success": True,
                "config_id": config_id,
                "has_results": False,
                "message": "No scoring results found for this configuration"
            })

        # Get statistics about results
        stats = sspi_custom_user_data.get_config_stats(config_id)

        logger.info(f"Retrieved results summary for config {config_id} (user {user_id})")

        return jsonify({
            "success": True,
            "config_id": config_id,
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
        user_id = request.__getattribute__("user_id")

        # Verify config exists and user owns it
        config = sspi_custom_user_structure.find_by_config_id(config_id, username=user_id)

        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found or access denied"
            }), 404

        # Get query parameters
        item_code = request.args.get('item_code')
        if not item_code:
            return jsonify({"success": False, "error": "item_code parameter is required"}), 400

        # Parse optional filters
        countries_param = request.args.get('countries', '')
        years_param = request.args.get('years', '')

        country_codes = [c.strip() for c in countries_param.split(',') if c.strip()] if countries_param else None
        years = [int(y.strip()) for y in years_param.split(',') if y.strip()] if years_param else None

        # Get results from database
        results = sspi_custom_user_data.get_config_results(
            config_id=config_id,
            country_codes=country_codes,
            years=years
        )

        # Filter by item_code
        filtered_results = [r for r in results if r.get("item_code") == item_code]

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

        logger.info(f"Retrieved chart data for config {config_id}, item {item_code} (user {user_id})")

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
# Session Management Endpoints
# ============================================================================

@customize_bp.route("/session/start", methods=["POST"])
@login_required
def start_session():
    """
    Create a new editing session from a configuration.
    Clears any existing session and starts a new one.
    """
    try:
        data = parse_json(request.get_json())
        config_id = data.get("config_id")
        config_name = data.get("name", "Unnamed Configuration")
        metadata = data.get("metadata")

        if not config_id:
            return jsonify({"success": False, "error": "config_id is required"}), 400

        # Create/update session
        session_data = session_manager.set_active_session(
            config_id=config_id,
            config_name=config_name,
            metadata=metadata
        )

        logger.info(f"Started editing session for config {config_id}")

        return jsonify({
            "success": True,
            "session": session_data
        })

    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        return jsonify({"success": False, "error": "Failed to start session"}), 500


@customize_bp.route("/session/current", methods=["GET"])
@login_required
def get_current_session():
    """
    Get the current active editing session.
    """
    try:
        active_session = session_manager.get_active_session()

        if not active_session:
            return jsonify({
                "success": True,
                "session": None
            })

        return jsonify({
            "success": True,
            "session": active_session
        })

    except Exception as e:
        logger.error(f"Error getting current session: {str(e)}")
        return jsonify({"success": False, "error": "Failed to get session"}), 500


@customize_bp.route("/session/clear", methods=["POST"])
@login_required
def clear_session():
    """
    End the current editing session.
    """
    try:
        session_manager.clear_active_session()

        logger.info("Cleared editing session")

        return jsonify({
            "success": True,
            "message": "Session cleared"
        })

    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return jsonify({"success": False, "error": "Failed to clear session"}), 500


@customize_bp.route("/session/heartbeat", methods=["POST"])
@login_required
def session_heartbeat():
    """
    Update last activity timestamp to prevent session expiry.
    Should be called periodically during active editing (every 5 minutes).
    """
    try:
        session_manager.update_last_activity()

        return jsonify({
            "success": True,
            "message": "Session activity updated"
        })

    except Exception as e:
        logger.error(f"Error updating session heartbeat: {str(e)}")
        return jsonify({"success": False, "error": "Failed to update heartbeat"}), 500


@customize_bp.route("/session/mark-unsaved", methods=["POST"])
@login_required
def mark_session_unsaved():
    """
    Mark the current session as having unsaved changes.
    """
    try:
        data = parse_json(request.get_json())
        has_unsaved = data.get("has_unsaved", True)

        session_manager.mark_unsaved_changes(has_unsaved)

        return jsonify({
            "success": True,
            "has_unsaved": has_unsaved
        })

    except Exception as e:
        logger.error(f"Error marking session unsaved: {str(e)}")
        return jsonify({"success": False, "error": "Failed to mark session"}), 500

