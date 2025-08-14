from flask import Blueprint, jsonify, request
from sspi_flask_app.models.database import sspi_custom_user_structure, sspi_metadata
from sspi_flask_app.models.errors import InvalidDocumentFormatError
import logging

logger = logging.getLogger(__name__)

customize_bp = Blueprint("customize_bp", __name__,
                        template_folder="templates",
                        static_folder="static",
                        url_prefix="/customize")


@customize_bp.route("/save", methods=["POST"])
def save_configuration():
    """
    Save a new custom SSPI structure configuration.
    
    Expected JSON payload:
    {
        "name": "My Custom SSPI",
        "structure": [...],  // Array of indicator objects from CustomizableSSPIStructure
        "user_id": "optional_user_id"
    }
    
    Returns:
    {
        "success": true,
        "config_id": "generated_config_id",
        "message": "Configuration saved successfully"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if "name" not in data:
            return jsonify({"error": "Configuration name is required"}), 400
        
        if "structure" not in data:
            return jsonify({"error": "Structure data is required"}), 400
        
        name = data["name"]
        structure = data["structure"]
        user_id = data.get("user_id")
        
        # Create the configuration
        config_id = sspi_custom_user_structure.create_config(
            name=name,
            structure=structure,
            user_id=user_id
        )
        
        logger.info(f"Created custom structure configuration: {config_id}")
        
        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Configuration saved successfully"
        })
        
    except InvalidDocumentFormatError as e:
        logger.error(f"Validation error saving configuration: {str(e)}")
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/list", methods=["GET"])
def list_configurations():
    """
    List all saved configuration names.
    
    Query parameters:
    - user_id: Optional filter by user
    
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
        user_id = request.args.get("user_id")
        
        configurations = sspi_custom_user_structure.list_config_names(user_id=user_id)
        
        return jsonify({
            "success": True,
            "configurations": configurations
        })
        
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/load/<config_id>", methods=["GET"])
def load_configuration(config_id):
    """
    Load a specific configuration by ID.
    
    Returns:
    {
        "success": true,
        "configuration": {
            "config_id": "abc123",
            "name": "My Custom SSPI",
            "structure": [...],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }
    """
    try:
        configuration = sspi_custom_user_structure.find_by_config_id(config_id)
        
        if not configuration:
            return jsonify({"error": "Configuration not found"}), 404
        
        return jsonify({
            "success": True,
            "configuration": configuration
        })
        
    except Exception as e:
        logger.error(f"Error loading configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/update/<config_id>", methods=["PUT"])
def update_configuration(config_id):
    """
    Update an existing configuration.
    
    Expected JSON payload:
    {
        "name": "Updated Name",
        "structure": [...]  // Optional - only include fields to update
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
        
        # Check if configuration exists
        existing_config = sspi_custom_user_structure.find_by_config_id(config_id)
        if not existing_config:
            return jsonify({"error": "Configuration not found"}), 404
        
        # Update the configuration
        success = sspi_custom_user_structure.update_config(config_id, data)
        
        if success:
            logger.info(f"Updated custom structure configuration: {config_id}")
            return jsonify({
                "success": True,
                "message": "Configuration updated successfully"
            })
        else:
            return jsonify({"error": "Failed to update configuration"}), 500
        
    except InvalidDocumentFormatError as e:
        logger.error(f"Validation error updating configuration {config_id}: {str(e)}")
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    
    except Exception as e:
        logger.error(f"Error updating configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/delete/<config_id>", methods=["DELETE"])
def delete_configuration(config_id):
    """
    Delete a configuration.
    
    Returns:
    {
        "success": true,
        "message": "Configuration deleted successfully"
    }
    """
    try:
        success = sspi_custom_user_structure.delete_config(config_id)
        
        if success:
            logger.info(f"Deleted custom structure configuration: {config_id}")
            return jsonify({
                "success": True,
                "message": "Configuration deleted successfully"
            })
        else:
            return jsonify({"error": "Configuration not found"}), 404
        
    except Exception as e:
        logger.error(f"Error deleting configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/duplicate/<config_id>", methods=["POST"])
def duplicate_configuration(config_id):
    """
    Create a copy of an existing configuration.
    
    Expected JSON payload:
    {
        "name": "Copy of My Custom SSPI"
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
        
        new_name = data["name"]
        
        new_config_id = sspi_custom_user_structure.duplicate_config(config_id, new_name)
        
        if new_config_id:
            logger.info(f"Duplicated configuration {config_id} to {new_config_id}")
            return jsonify({
                "success": True,
                "config_id": new_config_id,
                "message": "Configuration duplicated successfully"
            })
        else:
            return jsonify({"error": "Source configuration not found"}), 404
        
    except InvalidDocumentFormatError as e:
        logger.error(f"Validation error duplicating configuration {config_id}: {str(e)}")
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    
    except Exception as e:
        logger.error(f"Error duplicating configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/export/<config_id>", methods=["GET"])
def export_configuration(config_id):
    """
    Export a configuration in various formats.
    
    Query parameters:
    - format: json (default), csv
    
    Returns the configuration data in the requested format.
    """
    try:
        export_format = request.args.get("format", "json").lower()
        
        configuration = sspi_custom_user_structure.find_by_config_id(config_id)
        
        if not configuration:
            return jsonify({"error": "Configuration not found"}), 404
        
        if export_format == "json":
            # Return the structure data as JSON
            return jsonify({
                "success": True,
                "config_id": config_id,
                "name": configuration["name"],
                "structure": configuration["structure"],
                "exported_at": configuration["updated_at"]
            })
        
        elif export_format == "csv":
            # Convert structure to CSV format
            import csv
            import io
            
            output = io.StringIO()
            fieldnames = [
                "Category", "CategoryCode", "Indicator", "IndicatorCode", 
                "Pillar", "PillarCode", "LowerGoalpost", "UpperGoalpost",
                "ItemOrder", "Inverted"
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in configuration["structure"]:
                # Only write fields that exist in fieldnames
                row = {k: v for k, v in item.items() if k in fieldnames}
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            response = jsonify({
                "success": True,
                "config_id": config_id,
                "name": configuration["name"],
                "format": "csv",
                "data": csv_content
            })
            
            return response
        
        else:
            return jsonify({"error": f"Unsupported export format: {export_format}"}), 400
        
    except Exception as e:
        logger.error(f"Error exporting configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/datasets", methods=["GET"])
def list_datasets():
    """
    List available datasets for custom indicator creation.
    
    Query parameters:
    - search: Optional search term to filter datasets
    - organization: Optional organization filter (e.g., EPI, UNSDG, WB)
    - limit: Optional limit on number of results (default 100)
    
    Returns:
    {
        "success": true,
        "datasets": [
            {
                "dataset_code": "EPI_CO2GRW",
                "dataset_name": "CO2 Growth",
                "description": "Annual growth rate of CO2 emissions",
                "organization": "EPI",
                "dataset_type": "Primary"
            }
        ]
    }
    """
    try:
        search_term = request.args.get("search", "").upper()
        organization_filter = request.args.get("organization", "").upper()
        limit = int(request.args.get("limit", 100))
        
        # Get all dataset details from metadata
        all_datasets = sspi_metadata.get_dataset_details()
        
        if not all_datasets:
            return jsonify({
                "success": True,
                "datasets": []
            })
        
        # Filter datasets based on search criteria
        filtered_datasets = []
        
        for dataset in all_datasets:
            dataset_code = dataset.get("DatasetCode", "")
            dataset_name = dataset.get("DatasetName", "")
            description = dataset.get("Description", "")
            
            # Extract organization from dataset code (e.g., EPI_CO2GRW -> EPI)
            organization = dataset_code.split("_")[0] if "_" in dataset_code else ""
            
            # Apply filters
            if search_term and search_term not in dataset_code.upper() and search_term not in dataset_name.upper():
                continue
                
            if organization_filter and organization_filter != organization:
                continue
            
            filtered_datasets.append({
                "dataset_code": dataset_code,
                "dataset_name": dataset_name,
                "description": description,
                "organization": organization,
                "dataset_type": dataset.get("DatasetType", "Unknown")
            })
            
            # Apply limit
            if len(filtered_datasets) >= limit:
                break
        
        # Sort by dataset code for consistency
        filtered_datasets.sort(key=lambda x: x["dataset_code"])
        
        return jsonify({
            "success": True,
            "datasets": filtered_datasets
        })
        
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/datasets/<dataset_code>", methods=["GET"])
def get_dataset_details(dataset_code):
    """
    Get detailed information about a specific dataset.
    
    Returns:
    {
        "success": true,
        "dataset": {
            "dataset_code": "EPI_CO2GRW",
            "dataset_name": "CO2 Growth",
            "description": "Annual growth rate of CO2 emissions",
            "organization": "EPI",
            "dataset_type": "Primary",
            "source": {...}
        }
    }
    """
    try:
        dataset_detail = sspi_metadata.get_dataset_detail(dataset_code.upper())
        
        if not dataset_detail:
            return jsonify({"error": "Dataset not found"}), 404
        
        # Extract organization from dataset code
        organization = dataset_code.split("_")[0] if "_" in dataset_code else ""
        
        dataset_info = {
            "dataset_code": dataset_detail.get("DatasetCode", dataset_code),
            "dataset_name": dataset_detail.get("DatasetName", ""),
            "description": dataset_detail.get("Description", ""),
            "organization": organization,
            "dataset_type": dataset_detail.get("DatasetType", "Unknown"),
            "source": dataset_detail.get("Source", {})
        }
        
        return jsonify({
            "success": True,
            "dataset": dataset_info
        })
        
    except Exception as e:
        logger.error(f"Error getting dataset details for {dataset_code}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/validate-code", methods=["POST"])
def validate_code():
    """
    Validate a pillar, category, or indicator code for format and uniqueness.
    
    Expected JSON payload:
    {
        "code": "SUS",
        "type": "pillar",  // pillar, category, or indicator
        "existing_codes": ["SUS", "MAR", "PUB"]  // codes already in use
    }
    
    Returns:
    {
        "success": true,
        "valid": true,
        "message": "Code is valid and unique"
    }
    """
    try:
        import re
        
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        code = data.get("code", "").upper()
        code_type = data.get("type", "").lower()
        existing_codes = data.get("existing_codes", [])
        
        if not code or not code_type:
            return jsonify({
                "success": True,
                "valid": False,
                "message": "Code and type are required"
            })
        
        # Validate format
        if code_type == "pillar":
            if not re.match(r'^[A-Z]{2,3}$', code):
                return jsonify({
                    "success": True,
                    "valid": False,
                    "message": "Must be 2-3 uppercase letters"
                })
        elif code_type == "category":
            if not re.match(r'^[A-Z]{3}$', code):
                return jsonify({
                    "success": True,
                    "valid": False,
                    "message": "Must be exactly 3 uppercase letters"
                })
        elif code_type == "indicator":
            if not re.match(r'^[A-Z0-9]{6}$', code):
                return jsonify({
                    "success": True,
                    "valid": False,
                    "message": "Must be exactly 6 uppercase letters/numbers"
                })
        else:
            return jsonify({
                "success": True,
                "valid": False,
                "message": "Invalid code type"
            })
        
        # Check uniqueness
        if code in existing_codes:
            return jsonify({
                "success": True,
                "valid": False,
                "message": "Code already in use"
            })
        
        # Check against existing SSPI codes
        if code_type == "indicator":
            existing_indicators = sspi_metadata.get_indicator_codes()
            if code in existing_indicators:
                return jsonify({
                    "success": True,
                    "valid": False,
                    "message": "Code conflicts with existing SSPI indicator"
                })
        
        return jsonify({
            "success": True,
            "valid": True,
            "message": "Code is valid and unique"
        })
        
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500