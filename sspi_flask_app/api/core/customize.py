import csv
import os
import json
import io
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request, current_app as app

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
    return ""

@customize_bp.route("/list", methods=["GET"])
@owner_or_admin_required
def list_configurations():
    return ""

@customize_bp.route("/load/<config_id>", methods=["GET"])
@owner_or_admin_required
def load_configuration(config_id):
    return ""


@customize_bp.route("/update/<config_id>", methods=["PUT"])
@owner_or_admin_required
def update_configuration(config_id):
    return""

@customize_bp.route("/duplicate/<config_id>", methods=["POST"])
@owner_or_admin_required
def duplicate_configuration(config_id):
    return ""

@customize_bp.route("/export/<config_id>", methods=["GET"])
@owner_or_admin_required
def export_configuration(config_id):
    return ""


@customize_bp.route("/score", methods=["POST"])
@owner_or_admin_required
def score_custom_configuration():
    try:
        user_id = request.__getattribute__("user_id")
    except AttributeError:
        return parse_json({"error": "No user_id in request"})
    print("User:", user_id)
    json_metadata = request.get_json()
    print(type(json_metadata))
    if not json_metadata:
        return parse_json({"error": "No Metadata to Score"})
    custom_metadata = json_metadata.get("metadata", [])
    actions = json_metadata.get("actions", [])
    filepath = Path(os.path.join(app.root_path, "custom-sspi.json"))
    logger.info("Filepath: " + str(filepath))
    filepath.write_text(json.dumps(json_metadata))
    return parse_json(custom_metadata)

