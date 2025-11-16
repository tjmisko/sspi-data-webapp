from flask import Blueprint, jsonify, request
from sspi_flask_app.models.database import sspi_custom_user_structure, sspi_custom_user_data, sspi_metadata, sspi_item_data
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app.models.rank import SSPIRankingTable
import logging

logger = logging.getLogger(__name__)

customize_bp = Blueprint("customize_bp", __name__,
                        template_folder="templates",
                        static_folder="static",
                        url_prefix="/customize")


def convert_metadata_to_structure(metadata):
    """
    Convert metadata format (with SSPI, Pillars, Categories, Indicators)
    to structure format (only indicators with full hierarchy info).

    Args:
        metadata: List of metadata items including all hierarchy levels

    Returns:
        List of indicator configurations suitable for validation
    """
    structure = []

    # Extract items by type
    indicators = [item for item in metadata if item.get("ItemType") == "Indicator"]
    categories = {item["ItemCode"]: item for item in metadata if item.get("ItemType") == "Category"}
    pillars = {item["ItemCode"]: item for item in metadata if item.get("ItemType") == "Pillar"}

    # Build structure from indicators
    for idx, indicator in enumerate(indicators):
        indicator_code = indicator.get("ItemCode") or indicator.get("IndicatorCode")
        category_code = indicator.get("CategoryCode")
        pillar_code = indicator.get("PillarCode")

        # Get category and pillar names from the hierarchy
        category = categories.get(category_code, {})
        pillar = pillars.get(pillar_code, {})

        # Extract or derive the names
        indicator_name = indicator.get("ItemName") or indicator.get("Indicator") or indicator_code
        category_name = category.get("ItemName") or category.get("Category") or category_code
        pillar_name = pillar.get("ItemName") or pillar.get("Pillar") or pillar_code

        # Convert dataset codes to expected format
        dataset_codes = indicator.get("DatasetCodes", [])
        datasets = [{"dataset_code": code, "weight": 1.0} for code in dataset_codes]

        structure_item = {
            "Indicator": indicator_name,
            "IndicatorCode": indicator_code,
            "Category": category_name,
            "CategoryCode": category_code,
            "Pillar": pillar_name,
            "PillarCode": pillar_code,
            "LowerGoalpost": indicator.get("LowerGoalpost"),
            "UpperGoalpost": indicator.get("UpperGoalpost"),
            "Inverted": indicator.get("Inverted", False),
            "ItemOrder": indicator.get("ItemOrder", idx + 1),  # ItemOrder must be positive (>= 1)
            "datasets": datasets
        }

        structure.append(structure_item)

    # Sort by item order
    structure.sort(key=lambda x: (x["ItemOrder"], x["IndicatorCode"]))

    return structure


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
    OR
    {
        "name": "My Custom SSPI",
        "metadata": [...],  // Full metadata array (SSPI, Pillars, Categories, Indicators)
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
        data = request.get_json()
        if "name" not in data:
            return jsonify({"error": "Configuration name is required"}), 400
        if "metadata" not in data and "structure" not in data:
            return jsonify({"error": "Metadata or structure data is required"}), 400
        name = data["name"]
        if "metadata" in data:
            structure = convert_metadata_to_structure(data["metadata"])
        else:
            structure = data["structure"]
        user_id = data.get("user_id")
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
        configuration_response = configuration.copy()
        if "structure" in configuration_response:
            configuration_response["metadata"] = configuration_response["structure"]
        return jsonify({
            "success": True,
            "configuration": configuration_response
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
        existing_config = sspi_custom_user_structure.find_by_config_id(config_id)
        if not existing_config:
            return jsonify({"error": "Configuration not found"}), 404
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
        all_datasets = sspi_metadata.dataset_details()
        
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
            dataset_type = dataset.get("DatasetType", "Unknown")
            # Extract organization from dataset code (e.g., EPI_CO2GRW -> EPI)
            organization = dataset_code.split("_")[0] if "_" in dataset_code else ""
            # Get organization name from source if available
            source = dataset.get("Source", {})
            organization_name = source.get("OrganizationName", organization)
            # Create short description (first 60 words)
            description_short = description
            if description:
                words = description.split()
                if len(words) > 60:
                    description_short = " ".join(words[:60]) + "..."
            # Determine topic category based on common patterns
            topic_category = "General"
            if any(keyword in dataset_code.upper() for keyword in ["CO2", "GHG", "EMISS", "CARB", "CLIM", "ENV", "ECO", "BIO", "FOREST", "MARIN"]):
                topic_category = "SUS"
            elif any(keyword in dataset_code.upper() for keyword in ["TAX", "GDSP", "ECON", "FINA", "MARK", "TRAD", "EMPL", "UNEM"]):
                topic_category = "MS"
            elif any(keyword in dataset_code.upper() for keyword in ["EDU", "HEAL", "DEMO", "RIGH", "GOV", "SAFE", "INFR", "PUBL"]):
                topic_category = "PG"
            # Apply filters
            if search_term and search_term not in dataset_code.upper() and search_term not in dataset_name.upper() and search_term not in description.upper():
                continue
            if organization_filter and organization_filter != organization:
                continue
            filtered_datasets.append({
                "dataset_code": dataset_code,
                "dataset_name": dataset_name,
                "description": description,
                "description_short": description_short,
                "organization": organization,
                "organization_name": organization_name,
                "dataset_type": dataset_type,
                "topic_category": topic_category
            })
            if len(filtered_datasets) >= limit:
                break
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


def structure_to_metadata(structure_data: list) -> list:
    """
    Convert frontend structure format to SSPI metadata format with proper Children fields.
    
    :param structure_data: List of structure items from frontend export
    :return: List of metadata items suitable for SSPI class
    """
    metadata_items = []
    # Group items by type for building hierarchy
    pillars = {}
    categories = {}
    indicators = {}
    # First pass: collect all items and group them
    for item in structure_data:
        pillar_code = item.get('PillarCode', '')
        category_code = item.get('CategoryCode', '')
        indicator_code = item.get('IndicatorCode', '')
        # Store pillar info
        if pillar_code and pillar_code not in pillars:
            pillars[pillar_code] = {
                'code': pillar_code,
                'name': item.get('Pillar', pillar_code),
                'categories': set()
            }
        # Store category info
        if category_code and category_code not in categories:
            categories[category_code] = {
                'code': category_code,
                'name': item.get('Category', category_code),
                'pillar_code': pillar_code,
                'indicators': set()
            }
        # Store indicator info
        if indicator_code:
            indicators[indicator_code] = {
                'code': indicator_code,
                'name': item.get('Indicator', indicator_code),
                'category_code': category_code,
                'pillar_code': pillar_code,
                'datasets': item.get('datasets', []),
                'lower_goalpost': item.get('LowerGoalpost'),
                'upper_goalpost': item.get('UpperGoalpost'),
                'inverted': item.get('Inverted', False),
                'item_order': item.get('ItemOrder', 1)  # Default to 1 (must be positive)
            }
        
        # Build relationships
        if pillar_code and category_code:
            pillars[pillar_code]['categories'].add(category_code)
        
        if category_code and indicator_code:
            categories[category_code]['indicators'].add(indicator_code)
    # Create root SSPI item
    pillar_codes = sorted(pillars.keys())
    if pillar_codes:
        metadata_items.append({
            "ItemType": "SSPI",
            "ItemCode": "SSPI",
            "ItemName": "Custom SSPI",
            "Children": pillar_codes,
            "PillarCodes": pillar_codes,
            "Description": "Custom SSPI structure created through the customization interface"
        })
    # Create pillar items
    for pillar_code, pillar_data in pillars.items():
        category_codes = sorted(list(pillar_data['categories']))
        metadata_items.append({
            "ItemType": "Pillar",
            "ItemCode": pillar_code,
            "ItemName": pillar_data['name'],
            "Children": category_codes,
            "CategoryCodes": category_codes,
            "Pillar": pillar_data['name'],
            "PillarCode": pillar_code
        })
    # Create category items
    for category_code, category_data in categories.items():
        indicator_codes = sorted(list(category_data['indicators']))
        metadata_items.append({
            "ItemType": "Category",
            "ItemCode": category_code,
            "ItemName": category_data['name'],
            "Children": indicator_codes,
            "IndicatorCodes": indicator_codes,
            "Category": category_data['name'],
            "CategoryCode": category_code,
            "Pillar": pillars[category_data['pillar_code']]['name'],
            "PillarCode": category_data['pillar_code']
        })
    
    # Create indicator items
    for indicator_code, indicator_data in indicators.items():
        dataset_codes = [d.get('code') if isinstance(d, dict) else d for d in indicator_data['datasets']]
        metadata_items.append({
            "ItemType": "Indicator",
            "ItemCode": indicator_code,
            "ItemName": indicator_data['name'],
            "Children": [],
            "DatasetCodes": dataset_codes,
            "Indicator": indicator_data['name'],
            "IndicatorCode": indicator_code,
            "Category": categories[indicator_data['category_code']]['name'],
            "CategoryCode": indicator_data['category_code'],
            "Pillar": pillars[indicator_data['pillar_code']]['name'],
            "PillarCode": indicator_data['pillar_code'],
            "LowerGoalpost": indicator_data['lower_goalpost'],
            "UpperGoalpost": indicator_data['upper_goalpost'],
            "Inverted": indicator_data['inverted'],
            "ItemOrder": indicator_data['item_order']
        })
    
    return metadata_items


def metadata_to_structure(metadata_items: list) -> list:
    """
    Convert SSPI metadata format to frontend structure format.
    
    :param metadata_items: List of metadata items from SSPI system
    :return: List of structure items for frontend consumption
    """
    structure_items = []
    
    # Create lookup tables
    items_by_code = {item['ItemCode']: item for item in metadata_items}
    
    # Find all indicators and build structure items from them
    for item in metadata_items:
        if item.get('ItemType') == 'Indicator':
            indicator_code = item['ItemCode']
            category_code = item.get('CategoryCode', '')
            pillar_code = item.get('PillarCode', '')
            
            # Get parent items
            category = items_by_code.get(category_code, {})
            pillar = items_by_code.get(pillar_code, {})
            
            # Convert datasets to frontend format using enriched DatasetDetails
            datasets = []
            dataset_details = item.get('DatasetDetails', [])
            for detail in dataset_details:
                datasets.append({
                    'code': detail.get('dataset_code'),
                    'name': detail.get('dataset_name'),
                    'description': detail.get('description'),
                    'organization': detail.get('organization'),
                    'dataset_type': detail.get('dataset_type'),
                    'weight': 1.0  # Default weight
                })
            
            structure_items.append({
                'Indicator': item.get('ItemName', indicator_code),
                'IndicatorCode': indicator_code,
                'Category': category.get('ItemName', category_code),
                'CategoryCode': category_code,
                'Pillar': pillar.get('ItemName', pillar_code),
                'PillarCode': pillar_code,
                'LowerGoalpost': item.get('LowerGoalpost'),
                'UpperGoalpost': item.get('UpperGoalpost'),
                'Inverted': item.get('Inverted', False),
                'ItemOrder': item.get('ItemOrder', 1),  # Default to 1 (must be positive)
                'datasets': datasets
            })
    
    # Sort by ItemOrder if available, otherwise by codes
    structure_items.sort(key=lambda x: (
        x.get('ItemOrder', 999),
        x.get('PillarCode', ''),
        x.get('CategoryCode', ''),
        x.get('IndicatorCode', '')
    ))
    
    return structure_items


def validate_custom_structure(structure_data: list) -> dict:
    """
    Validate that a custom structure is valid for SSPI scoring.
    
    :param structure_data: List of structure items to validate
    :return: Dict with 'valid' boolean and 'errors' list
    """
    errors = []
    if not structure_data:
        errors.append("Structure cannot be empty")
        return {"valid": False, "errors": errors}
    # Check for required codes
    pillar_codes = set()
    category_codes = set()
    indicator_codes = set()
    for item in structure_data:
        pillar_code = item.get('PillarCode', '').strip()
        category_code = item.get('CategoryCode', '').strip()
        indicator_code = item.get('IndicatorCode', '').strip()
        
        if not pillar_code:
            errors.append(f"Missing PillarCode for item: {item}")
            continue
        
        if not category_code:
            errors.append(f"Missing CategoryCode for item: {item}")
            continue
            
        if not indicator_code:
            errors.append(f"Missing IndicatorCode for item: {item}")
            continue
        pillar_codes.add(pillar_code)
        category_codes.add(category_code)
        indicator_codes.add(indicator_code)
        # Validate goalpost values
        lower = item.get('LowerGoalpost')
        upper = item.get('UpperGoalpost')
        if lower is not None and upper is not None:
            try:
                lower_val = float(lower)
                upper_val = float(upper)
                if lower_val >= upper_val:
                    errors.append(f"Invalid goalposts for {indicator_code}: lower ({lower_val}) must be less than upper ({upper_val})")
            except (ValueError, TypeError):
                errors.append(f"Invalid goalpost values for {indicator_code}: must be numeric")
    # Check minimum structure requirements
    if len(pillar_codes) == 0:
        errors.append("Structure must contain at least one pillar")
    if len(category_codes) == 0:
        errors.append("Structure must contain at least one category")
    if len(indicator_codes) == 0:
        errors.append("Structure must contain at least one indicator")
    # Check for duplicate codes
    if len(set(indicator_codes)) != len(indicator_codes):
        errors.append("Duplicate indicator codes found")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "stats": {
            "pillars": len(pillar_codes),
            "categories": len(category_codes), 
            "indicators": len(indicator_codes)
        }
    }


@customize_bp.route("/default-structure", methods=["GET"])
def get_default_structure():
    """
    Load the complete default SSPI structure with proper hierarchy.
    
    Returns:
    {
        "success": true,
        "structure": [...],  // Frontend structure format
        "metadata": [...],   // SSPI metadata format
        "stats": {...}
    }
    """
    try:
        # Get all item details directly - this includes SSPI, Pillars, Categories, and Indicators
        all_items = sspi_metadata.item_details()

        if not all_items:
            return jsonify({
                "success": False,
                "error": "No items found in metadata"
            }), 404

        # Get dataset details and create lookup map
        dataset_details_map = {}
        all_datasets = sspi_metadata.dataset_details()
        for dataset in all_datasets:
            dataset_code = dataset.get('DatasetCode')
            if dataset_code:
                dataset_details_map[dataset_code] = {
                    'dataset_code': dataset_code,
                    'dataset_name': dataset.get('DatasetName', dataset_code),
                    'description': dataset.get('Description', ''),
                    'organization': dataset_code.split('_')[0] if '_' in dataset_code else '',
                    'dataset_type': dataset.get('DatasetType', 'Unknown')
                }

        # Enrich indicators with dataset details
        metadata_items = all_items
        for item in metadata_items:
            if item.get('ItemType') == 'Indicator':
                dataset_codes = item.get('DatasetCodes', [])
                item['DatasetDetails'] = []
                for code in dataset_codes:
                    if code in dataset_details_map:
                        item['DatasetDetails'].append(dataset_details_map[code])
                    else:
                        # Include code even if details not found
                        item['DatasetDetails'].append({
                            'dataset_code': code,
                            'dataset_name': code,
                            'description': '',
                            'organization': '',
                            'dataset_type': 'Unknown'
                        })

                # Log dataset details and score function for debugging
                logger.info(f"Indicator {item.get('ItemCode')}: {len(item['DatasetDetails'])} datasets, ScoreFunction: {'Yes' if item.get('ScoreFunction') else 'No'}")

        # Convert to frontend structure format
        structure_items = metadata_to_structure(metadata_items)
        
        # Get stats
        stats = {
            "pillars": len([item for item in metadata_items if item.get('ItemType') == 'Pillar']),
            "categories": len([item for item in metadata_items if item.get('ItemType') == 'Category']), 
            "indicators": len([item for item in metadata_items if item.get('ItemType') == 'Indicator']),
            "total_items": len(metadata_items)
        }
        
        logger.info(f"Loaded default SSPI structure: {stats}")
        
        return jsonify({
            "success": True,
            "structure": structure_items,
            "metadata": metadata_items,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error loading default structure: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/validate-structure", methods=["POST"])
def validate_structure():
    """
    Validate a custom structure for completeness and correctness.
    
    Expected JSON payload:
    {
        "structure": [...]  // Frontend structure format
    }
    
    Returns:
    {
        "success": true,
        "valid": true,
        "errors": [...],
        "stats": {...}
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        structure = data.get("structure", [])
        
        validation_result = validate_custom_structure(structure)
        
        return jsonify({
            "success": True,
            **validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating structure: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/transform", methods=["POST"])
def transform_structure():
    """
    Transform between frontend structure format and SSPI metadata format.
    
    Expected JSON payload:
    {
        "data": [...],
        "from_format": "structure",  // "structure" or "metadata"
        "to_format": "metadata"      // "structure" or "metadata"
    }
    
    Returns:
    {
        "success": true,
        "data": [...],
        "stats": {...}
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        input_data = data.get("data", [])
        from_format = data.get("from_format", "structure")
        to_format = data.get("to_format", "metadata")
        
        if from_format == to_format:
            return jsonify({
                "success": True,
                "data": input_data,
                "message": "No transformation needed"
            })
        
        transformed_data = []
        
        if from_format == "structure" and to_format == "metadata":
            transformed_data = structure_to_metadata(input_data)
        elif from_format == "metadata" and to_format == "structure":
            transformed_data = metadata_to_structure(input_data)
        else:
            return jsonify({"error": f"Unsupported transformation: {from_format} to {to_format}"}), 400
        
        # Get stats
        stats = {}
        if to_format == "metadata":
            stats = {
                "items_by_type": {}
            }
            for item in transformed_data:
                item_type = item.get('ItemType', 'Unknown')
                stats["items_by_type"][item_type] = stats["items_by_type"].get(item_type, 0) + 1
        else:
            pillar_codes = set()
            category_codes = set()
            indicator_codes = set()
            for item in transformed_data:
                if item.get('PillarCode'):
                    pillar_codes.add(item.get('PillarCode'))
                if item.get('CategoryCode'):
                    category_codes.add(item.get('CategoryCode'))
                if item.get('IndicatorCode'):
                    indicator_codes.add(item.get('IndicatorCode'))
            
            stats = {
                "pillars": len(pillar_codes),
                "categories": len(category_codes),
                "indicators": len(indicator_codes)
            }
        
        return jsonify({
            "success": True,
            "data": transformed_data,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error transforming structure: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/score", methods=["POST"])
def score_custom_structure():
    """
    Score a custom SSPI structure using real indicator data.
    
    Expected JSON payload:
    {
        "metadata": [...],        // SSPI metadata format items
        "country_code": "USA",    // Country to score
        "year": 2023             // Year to score
    }
    
    OR
    
    {
        "structure": [...],       // Frontend structure format
        "country_code": "USA",
        "year": 2023
    }
    
    OR
    
    {
        "config_id": "abc123",    // Saved configuration ID
        "country_code": "USA", 
        "year": 2023
    }
    
    Returns:
    {
        "success": true,
        "scores": {...},          // All item scores
        "sspi_score": 75.5,      // Root SSPI score
        "country_code": "USA",
        "year": 2023,
        "stats": {...}
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        data = request.get_json()
        country_code = data.get("country_code", "").upper()
        year = data.get("year", 2023)
        if not country_code:
            return jsonify({"error": "country_code is required"}), 400
        # Get metadata format - from direct metadata, structure, or config
        metadata_items = None
        if "metadata" in data:
            metadata_items = data["metadata"]
        elif "structure" in data:
            structure_data = data["structure"]
            validation_result = validate_custom_structure(structure_data)
            if not validation_result["valid"]:
                return jsonify({
                    "error": "Invalid structure",
                    "validation_errors": validation_result["errors"]
                }), 400
            metadata_items = structure_to_metadata(structure_data)
        elif "config_id" in data:
            # Load saved configuration
            config = sspi_custom_user_structure.find_by_config_id(data["config_id"])
            if not config:
                return jsonify({"error": "Configuration not found"}), 404
            metadata_items = structure_to_metadata(config["structure"])
        else:
            return jsonify({"error": "Must provide metadata, structure, or config_id"}), 400
        
        if not metadata_items:
            return jsonify({"error": "No metadata items to score"}), 400
        
        # Get indicator codes from metadata
        indicator_codes = []
        for item in metadata_items:
            if item.get("ItemType") == "Indicator":
                indicator_codes.append(item.get("ItemCode"))
        
        if not indicator_codes:
            return jsonify({"error": "No indicators found in structure"}), 400
        
        # Fetch indicator scores from database
        indicator_scores = []
        missing_indicators = []
        
        for indicator_code in indicator_codes:
            # Query the SSPI item data for this indicator, country, and year
            score_data = sspi_item_data.get_item_score(
                country_code=country_code,
                item_code=indicator_code,
                year=year
            )
            
            if score_data and score_data.get("Score") is not None:
                indicator_scores.append({
                    "IndicatorCode": indicator_code,
                    "Score": score_data["Score"],
                    "Year": year
                })
            else:
                missing_indicators.append(indicator_code)
        
        if not indicator_scores:
            return jsonify({
                "error": f"No indicator scores found for {country_code} in {year}",
                "missing_indicators": missing_indicators
            }), 404
        
        if missing_indicators:
            logger.warning(f"Missing scores for indicators: {missing_indicators}")
        
        # Create SSPI instance and calculate scores
        try:
            sspi_instance = SSPI(
                item_details=metadata_items,
                indicator_scores=indicator_scores,
                strict_year=True
            )
        except Exception as e:
            logger.error(f"Error creating SSPI instance: {str(e)}")
            return jsonify({
                "error": f"SSPI calculation failed: {str(e)}",
                "metadata_items_count": len(metadata_items),
                "indicator_scores_count": len(indicator_scores)
            }), 500
        
        # Export scores in rank dict format
        all_scores = sspi_instance.to_rank_dict(country_code, year)
        sspi_score = all_scores.get("SSPI", {}).get("Score")
        
        # Get detailed stats
        stats = {
            "total_indicators": len(indicator_codes),
            "scored_indicators": len(indicator_scores),
            "missing_indicators": len(missing_indicators),
            "total_items": len(metadata_items),
            "pillars": len([item for item in metadata_items if item.get("ItemType") == "Pillar"]),
            "categories": len([item for item in metadata_items if item.get("ItemType") == "Category"]),
            "indicators": len([item for item in metadata_items if item.get("ItemType") == "Indicator"])
        }
        
        logger.info(f"Scored custom SSPI for {country_code} {year}: {sspi_score} ({stats})")
        
        return jsonify({
            "success": True,
            "scores": all_scores,
            "sspi_score": sspi_score,
            "country_code": country_code,
            "year": year,
            "stats": stats,
            "missing_indicators": missing_indicators if missing_indicators else None
        })
        
    except Exception as e:
        logger.error(f"Error scoring custom structure: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/score-dynamic/<config_id>", methods=["POST"])
def score_dynamic_configuration(config_id):
    """
    Score a custom SSPI configuration across all years and countries.
    Follows the finalize.py pattern for dynamic scoring.
    Stores results in sspi_custom_user_data collection.

    Returns:
    {
        "success": true,
        "config_id": "config_id",
        "documents_scored": 12345,
        "years": [2000, 2001, ...],
        "countries_count": 67
    }
    """
    try:
        # 1. Load configuration
        config = sspi_custom_user_structure.find_by_config_id(config_id)
        if not config:
            return jsonify({"error": "Configuration not found"}), 404

        logger.info(f"Scoring dynamic configuration: {config_id}")

        # 2. Convert structure to metadata
        structure = config.get("structure", [])
        if not structure:
            return jsonify({"error": "Configuration has no structure"}), 400

        metadata_items = structure_to_metadata(structure)
        if not metadata_items:
            return jsonify({"error": "Could not convert structure to metadata"}), 400

        # 3. Get indicator codes
        indicator_codes = [
            item["ItemCode"] for item in metadata_items
            if item.get("ItemType") == "Indicator"
        ]

        if not indicator_codes:
            return jsonify({"error": "No indicators in structure"}), 400

        logger.info(f"Scoring {len(indicator_codes)} indicators across years and countries")

        # 4. Define scope
        years = list(range(2000, 2024))
        countries = sspi_metadata.country_group("SSPI67")

        # 5. Build data map (following finalize.py pattern)
        data_map = {}
        for country in countries:
            data_map[country] = {}
            for year in years:
                # Get indicator scores for this country/year
                year_scores = []
                for ind_code in indicator_codes:
                    score_doc = sspi_item_data.get_item_score(
                        country_code=country,
                        item_code=ind_code,
                        year=year
                    )
                    if score_doc and score_doc.get("Score") is not None:
                        year_scores.append({
                            "IndicatorCode": ind_code,
                            "Score": score_doc["Score"],
                            "Year": year
                        })

                # Only add if we have data for this year
                if year_scores:
                    data_map[country][year] = year_scores

        # 6. Score each country/year combination
        documents = []
        for country, year_data in data_map.items():
            for year, indicator_scores in year_data.items():
                try:
                    # Create SSPI instance (following finalize.py pattern)
                    sspi_instance = SSPI(
                        item_details=metadata_items,
                        indicator_scores=indicator_scores,
                        strict_year=True
                    )

                    # Get score documents
                    score_docs = sspi_instance.to_score_documents(country)

                    # Add config_id to each document for filtering
                    for doc in score_docs:
                        doc["config_id"] = config_id
                        documents.append(doc)

                except Exception as e:
                    logger.warning(f"Could not score {country} {year}: {str(e)}")
                    continue

        if not documents:
            return jsonify({"error": "No scores could be calculated"}), 400

        # 7. Store in database
        logger.info(f"Storing {len(documents)} score documents for config {config_id}")
        sspi_custom_user_data.delete_many({"config_id": config_id})  # Clear old scores
        sspi_custom_user_data.insert_many(documents)

        # 8. Return success
        return jsonify({
            "success": True,
            "config_id": config_id,
            "documents_scored": len(documents),
            "years": years,
            "countries_count": len(countries),
            "indicators_count": len(indicator_codes)
        })

    except Exception as e:
        logger.error(f"Error in score_dynamic_configuration: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@customize_bp.route("/score/<config_id>", methods=["GET"])
def score_saved_configuration(config_id):
    """
    Score a saved configuration.
    
    Query parameters:
    - country_code: Country to score (required)
    - year: Year to score (default: 2023)
    
    Returns same format as /score endpoint.
    """
    try:
        country_code = request.args.get("country_code", "").upper()
        year = int(request.args.get("year", 2023))
        
        if not country_code:
            return jsonify({"error": "country_code parameter is required"}), 400
        
        # Load configuration
        config = sspi_custom_user_structure.find_by_config_id(config_id)
        if not config:
            return jsonify({"error": "Configuration not found"}), 404
        
        # Score the configuration using the metadata transformation
        structure_data = config["structure"]
        validation_result = validate_custom_structure(structure_data)
        if not validation_result["valid"]:
            return jsonify({
                "error": "Invalid saved structure",
                "validation_errors": validation_result["errors"]
            }), 400
        
        metadata_items = structure_to_metadata(structure_data)
        
        # Get indicator codes from metadata
        indicator_codes = []
        for item in metadata_items:
            if item.get("ItemType") == "Indicator":
                indicator_codes.append(item.get("ItemCode"))
        
        if not indicator_codes:
            return jsonify({"error": "No indicators found in configuration"}), 400
        
        # Fetch indicator scores from database
        indicator_scores = []
        missing_indicators = []
        
        for indicator_code in indicator_codes:
            score_data = sspi_item_data.get_item_score(
                country_code=country_code,
                item_code=indicator_code,
                year=year
            )
            
            if score_data and score_data.get("Score") is not None:
                indicator_scores.append({
                    "IndicatorCode": indicator_code,
                    "Score": score_data["Score"],
                    "Year": year
                })
            else:
                missing_indicators.append(indicator_code)
        
        if not indicator_scores:
            return jsonify({
                "error": f"No indicator scores found for {country_code} in {year}",
                "missing_indicators": missing_indicators
            }), 404
        
        # Create SSPI instance and calculate scores
        sspi_instance = SSPI(
            item_details=metadata_items,
            indicator_scores=indicator_scores,
            strict_year=True
        )
        
        # Export scores in rank dict format
        all_scores = sspi_instance.to_rank_dict(country_code, year)
        sspi_score = all_scores.get("SSPI", {}).get("Score")
        
        stats = {
            "total_indicators": len(indicator_codes),
            "scored_indicators": len(indicator_scores),
            "missing_indicators": len(missing_indicators),
            "config_name": config.get("name", "Unknown")
        }
        
        return jsonify({
            "success": True,
            "scores": all_scores,
            "sspi_score": sspi_score,
            "country_code": country_code,
            "year": year,
            "config_id": config_id,
            "stats": stats,
            "missing_indicators": missing_indicators if missing_indicators else None
        })
        
    except ValueError:
        return jsonify({"error": "Invalid year parameter"}), 400
    except Exception as e:
        logger.error(f"Error scoring saved configuration {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/indicators", methods=["GET"])
def list_indicators():
    """
    List available indicators for adding to custom SSPI structures.
    
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
                "indicator_code": "ACWAT1",
                "indicator_name": "Access to Clean Water",
                "description": "Percentage of population with access to clean water",
                "category_code": "BHN",
                "category_name": "Basic Human Needs",
                "pillar_code": "SUS",
                "pillar_name": "Sustainability"
            }
        ]
    }
    """
    try:
        # Get query parameters
        search_term = request.args.get('search', '').strip()
        category_filter = request.args.get('category', '').strip()
        pillar_filter = request.args.get('pillar', '').strip()
        limit = int(request.args.get('limit', 100))
        
        # Get all indicator details from metadata
        indicator_details = sspi_metadata.indicator_details()
        
        if not indicator_details:
            return jsonify({
                "success": True,
                "indicators": [],
                "message": "No indicators found in metadata"
            })
        
        # Filter indicators based on query parameters
        filtered_indicators = []
        
        for indicator in indicator_details:
            # Apply search filter
            if search_term:
                search_fields = [
                    indicator.get('IndicatorCode', ''),
                    indicator.get('IndicatorName', ''),
                    indicator.get('Description', '')
                ]
                if not any(search_term.lower() in field.lower() for field in search_fields if field):
                    continue
            
            # Apply category filter
            if category_filter:
                if indicator.get('CategoryCode', '').upper() != category_filter.upper():
                    continue
            
            # Apply pillar filter
            if pillar_filter:
                if indicator.get('PillarCode', '').upper() != pillar_filter.upper():
                    continue
            
            # Format indicator data for response
            indicator_data = {
                "indicator_code": indicator.get('IndicatorCode', ''),
                "indicator_name": indicator.get('IndicatorName', ''),
                "description": indicator.get('Description', ''),
                "category_code": indicator.get('CategoryCode', ''),
                "category_name": indicator.get('CategoryName', ''),
                "pillar_code": indicator.get('PillarCode', ''),
                "pillar_name": indicator.get('PillarName', '')
            }
            
            filtered_indicators.append(indicator_data)
        
        # Apply limit
        if limit > 0:
            filtered_indicators = filtered_indicators[:limit]
        
        return jsonify({
            "success": True,
            "indicators": filtered_indicators,
            "total_count": len(filtered_indicators)
        })
        
    except Exception as e:
        logger.error(f"Error listing indicators: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/indicators/<indicator_code>", methods=["GET"])
def get_indicator_details(indicator_code):
    """
    Get detailed information about a specific indicator.
    
    Returns:
    {
        "success": true,
        "indicator": {
            "indicator_code": "ACWAT1",
            "indicator_name": "Access to Clean Water",
            "description": "Percentage of population with access to clean water",
            "category_code": "BHN",
            "category_name": "Basic Human Needs",
            "pillar_code": "SUS",
            "pillar_name": "Sustainability",
            "lower_goalpost": 0,
            "upper_goalpost": 100,
            "inverted": false
        }
    }
    """
    try:
        indicator_detail = sspi_metadata.get_indicator_detail(indicator_code.upper())
        
        if not indicator_detail:
            return jsonify({"error": "Indicator not found"}), 404
        
        # Format indicator data for response
        indicator_data = {
            "indicator_code": indicator_detail.get('IndicatorCode', ''),
            "indicator_name": indicator_detail.get('IndicatorName', ''),
            "description": indicator_detail.get('Description', ''),
            "category_code": indicator_detail.get('CategoryCode', ''),
            "category_name": indicator_detail.get('CategoryName', ''),
            "pillar_code": indicator_detail.get('PillarCode', ''),
            "pillar_name": indicator_detail.get('PillarName', ''),
            "lower_goalpost": indicator_detail.get('LowerGoalpost', 0),
            "upper_goalpost": indicator_detail.get('UpperGoalpost', 100),
            "inverted": indicator_detail.get('Inverted', False),
            "dataset_codes": indicator_detail.get('DatasetCodes', [])
        }
        
        return jsonify({
            "success": True,
            "indicator": indicator_data
        })
        
    except Exception as e:
        logger.error(f"Error getting indicator details for {indicator_code}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


def format_results_for_panel_chart(results: list, config: dict) -> dict:
    """
    Format cached results for consumption by panel chart components.
    
    Args:
        results: List of cached scoring results
        config: Configuration metadata
        
    Returns:
        Dictionary formatted for panel chart consumption
    """
    try:
        if not results:
            return {
                "success": True,
                "data": [],
                "labels": [],
                "title": config.get("name", "Custom SSPI"),
                "itemType": "custom",
                "groupOptions": [],
                "itemOptions": [],
                "description": "Custom SSPI structure with no available data"
            }
        
        # Group results by country and item
        country_data = {}
        item_codes = set()
        years = set()
        
        for result in results:
            country_code = result["country_code"]
            item_code = result["item_code"]
            year = result["year"]
            score = result["score"]
            
            if country_code not in country_data:
                country_data[country_code] = {
                    "CCode": country_code,
                    "CName": country_code,  # Would need country name lookup
                    "CGroup": ["CUSTOM"],   # Custom group
                    "data": [],
                    "scores": [],
                    "ICode": item_code
                }
            
            country_data[country_code]["data"].append(score)
            country_data[country_code]["scores"].append(score)
            
            item_codes.add(item_code)
            years.add(year)
        
        # Convert to list format expected by panel charts
        datasets = list(country_data.values())
        
        # Create labels (years)
        labels = sorted(list(years))
        
        # Create item options for dropdown
        item_options = []
        for item_code in sorted(item_codes):
            # Find an example result to get the item name
            example_result = next((r for r in results if r["item_code"] == item_code), {})
            item_options.append({
                "Code": item_code,
                "Name": example_result.get("item_name", item_code)
            })
        
        return {
            "success": True,
            "data": datasets,
            "labels": [str(year) for year in labels],
            "title": config.get("name", "Custom SSPI"),
            "itemType": "custom",
            "itemCode": item_options[0]["Code"] if item_options else "CUSTOM",
            "groupOptions": ["CUSTOM"],
            "itemOptions": item_options,
            "description": f"Custom SSPI structure: {config.get('name', 'Unnamed')}"
        }
        
    except Exception as e:
        logger.error(f"Error formatting results for panel chart: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to format results: {str(e)}"
        }


@customize_bp.route("/score-and-cache/<config_id>", methods=["POST"])
def score_and_cache_configuration(config_id):
    """
    Score a custom SSPI structure and cache the results.
    
    Expected JSON payload:
    {
        "structure": {...},  // Optional: structure to score (if not using saved config)
        "country_codes": ["USA", "GBR"],  // Optional: specific countries
        "years": [2020, 2021],  // Optional: specific years
        "force_refresh": false  // Optional: force recalculation even if cached
    }
    
    Returns:
    {
        "success": true,
        "config_id": "config_id",
        "message": "Configuration scored and cached successfully",
        "cached_results_count": 1234
    }
    """
    try:
        data = request.get_json() if request.is_json else {}
        
        # Get configuration or use provided structure
        if "structure" in data:
            # Use provided structure (for unsaved configurations)
            structure = data["structure"]
            config_name = structure.get("itemName", "Temporary Configuration")
        else:
            # Load saved configuration
            config = sspi_custom_user_structure.find_by_config_id(config_id)
            if not config:
                return jsonify({"error": "Configuration not found"}), 404
            structure = config["structure"] 
            config_name = config["name"]
        
        # Convert structure to metadata format
        try:
            metadata_items = convert_structure_to_metadata(structure)
        except Exception as e:
            logger.error(f"Error converting structure to metadata: {str(e)}")
            return jsonify({"error": f"Invalid structure format: {str(e)}"}), 400
        
        # Extract optional parameters
        country_codes = data.get("country_codes")
        years = data.get("years")  
        force_refresh = data.get("force_refresh", False)
        
        # Check if we already have cached results (unless force refresh)
        if not force_refresh:
            existing_results = sspi_custom_user_data.get_config_results(config_id)
            if existing_results:
                return jsonify({
                    "success": True,
                    "config_id": config_id,
                    "message": "Using cached results (use force_refresh=true to recalculate)",
                    "cached_results_count": len(existing_results)
                })
        
        # Score the custom structure
        try:
            scoring_results = score_custom_metadata(
                metadata_items, 
                country_codes=country_codes,
                years=years
            )
        except Exception as e:
            logger.error(f"Error scoring custom structure: {str(e)}")
            return jsonify({"error": f"Scoring failed: {str(e)}"}), 500
        
        if not scoring_results.get("success", False):
            return jsonify({
                "error": f"Scoring failed: {scoring_results.get('error', 'Unknown error')}"
            }), 500
        
        # Clear existing cached results if force refresh
        if force_refresh:
            sspi_custom_user_data.clear_config_results(config_id)
        
        # Store results in cache
        try:
            cache_results = sspi_custom_user_data.store_scoring_results(
                config_id, scoring_results["results"]
            )
            
            if not cache_results["success"]:
                logger.error(f"Failed to cache results: {cache_results.get('error')}")
                return jsonify({
                    "error": f"Failed to cache results: {cache_results.get('error')}"
                }), 500
                
        except Exception as e:
            logger.error(f"Error caching scoring results: {str(e)}")
            return jsonify({"error": f"Failed to cache results: {str(e)}"}), 500
        
        logger.info(f"Successfully scored and cached configuration {config_id}")
        return jsonify({
            "success": True,
            "config_id": config_id,
            "message": "Configuration scored and cached successfully",
            "cached_results_count": len(scoring_results["results"])
        })
        
    except Exception as e:
        logger.error(f"Error in score_and_cache_configuration: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/cached-scores/<config_id>", methods=["GET"])
def get_cached_scores(config_id):
    """
    Retrieve cached scoring results for a configuration.
    
    Query parameters:
    - format: 'raw' (default) or 'panel_data' (formatted for SSPIPanelChart)
    - country_codes: comma-separated list of countries to filter
    - years: comma-separated list of years to filter
    - item_types: comma-separated list of item types (SSPI,Pillar,Category,Indicator)
    
    Returns:
    {
        "success": true,
        "config_id": "config_id", 
        "results": [...],
        "count": 123
    }
    """
    try:
        # Get cached results
        results = sspi_custom_user_data.get_config_results(config_id)
        
        if not results:
            return jsonify({"error": "No cached results found for this configuration"}), 404
        
        # Apply filters if provided
        country_filter = request.args.get("country_codes")
        if country_filter:
            country_codes = [c.strip().upper() for c in country_filter.split(",")]
            results = [r for r in results if r.get("country_code") in country_codes]
        
        years_filter = request.args.get("years")
        if years_filter:
            years = [int(y.strip()) for y in years_filter.split(",") if y.strip().isdigit()]
            results = [r for r in results if r.get("year") in years]
            
        item_types_filter = request.args.get("item_types")
        if item_types_filter:
            item_types = [t.strip() for t in item_types_filter.split(",")]
            results = [r for r in results if r.get("item_type") in item_types]
        
        # Format for panel charts if requested
        response_format = request.args.get("format", "raw").lower()
        if response_format == "panel_data":
            # Get the configuration for metadata
            config = sspi_custom_user_structure.find_by_config_id(config_id)
            formatted_data = format_results_for_panel_chart(results, config)
            return jsonify(formatted_data)
        
        # Return raw results
        return jsonify({
            "success": True,
            "config_id": config_id,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving cached scores for {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@customize_bp.route("/cached-scores/<config_id>", methods=["DELETE"])
def clear_cached_scores(config_id):
    """
    Clear cached scoring results for a configuration.
    
    Returns:
    {
        "success": true,
        "message": "Cached results cleared successfully"
    }
    """
    try:
        success = sspi_custom_user_data.clear_config_results(config_id)
        
        if success:
            logger.info(f"Cleared cached results for configuration: {config_id}")
            return jsonify({
                "success": True,
                "message": "Cached results cleared successfully"
            })
        else:
            return jsonify({"error": "No cached results found for this configuration"}), 404
            
    except Exception as e:
        logger.error(f"Error clearing cached scores for {config_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


def score_custom_metadata(metadata_items: list, country_codes: list = None, years: list = None) -> dict:
    """
    Score a custom SSPI structure using the existing SSPI class.
    
    Args:
        metadata_items: List of metadata items in SSPI format
        country_codes: Optional list of country codes to score
        years: Optional list of years to score
    
    Returns:
        dict: {
            "success": bool,
            "results": [list of scored documents],
            "error": str (if success=False)
        }
    """
    try:
        # Extract indicator codes from metadata
        indicator_codes = []
        for item in metadata_items:
            if item.get("ItemType") == "Indicator":
                indicator_codes.append(item.get("ItemCode"))
        
        if not indicator_codes:
            return {
                "success": False,
                "error": "No indicators found in structure"
            }
        
        # Get indicator scores from the database
        query = {"ItemCode": {"$in": indicator_codes}}
        
        if country_codes:
            query["CountryCode"] = {"$in": country_codes}
            
        if years:
            query["Year"] = {"$in": years}
        
        # Query existing indicator data
        indicator_scores = list(sspi_item_data.find(query))
        
        if not indicator_scores:
            return {
                "success": False,
                "error": "No indicator data found for the specified structure"
            }
        
        # Create SSPI instance with custom metadata
        try:
            sspi_instance = SSPI(
                item_details=metadata_items,
                indicator_scores=indicator_scores,
                strict_year=True
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to initialize SSPI instance: {str(e)}"
            }
        
        # Calculate scores for all levels of the hierarchy
        try:
            sspi_instance.calculate_all_scores()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to calculate scores: {str(e)}"
            }
        
        # Extract all calculated results
        results = []
        
        # Get all countries and years from the indicator scores
        all_countries = set(score.get("CountryCode") for score in indicator_scores)
        all_years = set(score.get("Year") for score in indicator_scores)
        
        # Create ranking table for relative rankings
        ranking_table = SSPIRankingTable()
        
        # Process each metadata item to extract scores
        for item in metadata_items:
            item_code = item.get("ItemCode")
            item_name = item.get("ItemName", item_code)
            item_type = item.get("ItemType")
            
            for country_code in all_countries:
                for year in all_years:
                    # Get score from SSPI instance
                    try:
                        if item_type == "Indicator":
                            # For indicators, get from indicator_scores
                            score_doc = next((
                                s for s in indicator_scores 
                                if s.get("ItemCode") == item_code 
                                and s.get("CountryCode") == country_code 
                                and s.get("Year") == year
                            ), None)
                            
                            if score_doc:
                                score_value = score_doc.get("Score")
                            else:
                                continue
                        else:
                            # For higher-level items, get from SSPI instance
                            score_value = sspi_instance.get_score(item_code, country_code, year)
                            if score_value is None:
                                continue
                        
                        # Calculate rank (simple ranking within this dataset)
                        rank = ranking_table.calculate_rank(
                            item_code, country_code, year, score_value
                        ) if hasattr(ranking_table, 'calculate_rank') else None
                        
                        # Create result document
                        result = {
                            "config_id": "temp",  # Will be updated by caller
                            "country_code": country_code,
                            "year": year,
                            "item_code": item_code,
                            "item_name": item_name,
                            "item_type": item_type,
                            "score": round(score_value, 3) if score_value is not None else None,
                            "rank": rank,
                            "calculated_at": None,  # Will be set by storage function
                            "metadata": {
                                "structure_hash": None,  # Will be calculated if needed
                                "indicator_count": len(indicator_codes),
                                "data_source": "custom_structure"
                            }
                        }
                        
                        results.append(result)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get score for {item_code}/{country_code}/{year}: {str(e)}")
                        continue
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in score_custom_metadata: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def convert_structure_to_metadata(structure):
    """
    Convert frontend structure format to SSPI metadata format.
    
    Args:
        structure: Hierarchical structure from frontend
        
    Returns:
        list: Flat list of metadata items in SSPI format
    """
    metadata_items = []
    
    def process_item(item, parent_code=None):
        # Create metadata item
        metadata_item = {
            "ItemCode": item["itemCode"],
            "ItemName": item["itemName"], 
            "ItemType": item["itemType"],
            "Children": [child["itemCode"] for child in item.get("children", [])]
        }
        
        # Add parent relationship if exists
        if parent_code:
            metadata_item["Parent"] = parent_code
            
        # Add any additional fields from the item
        for key, value in item.items():
            if key not in ["itemCode", "itemName", "itemType", "children"]:
                metadata_item[key] = value
                
        metadata_items.append(metadata_item)
        
        # Process children recursively
        for child in item.get("children", []):
            process_item(child, item["itemCode"])
    
    process_item(structure)
    return metadata_items
