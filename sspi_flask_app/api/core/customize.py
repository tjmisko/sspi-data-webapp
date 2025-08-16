from flask import Blueprint, jsonify, request
from sspi_flask_app.models.database import sspi_custom_user_structure, sspi_metadata, sspi_item_data
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from sspi_flask_app.models.sspi import SSPI
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
        
        # Support both 'metadata' (new) and 'structure' (legacy) fields
        if "metadata" not in data and "structure" not in data:
            return jsonify({"error": "Metadata or structure data is required"}), 400
        
        name = data["name"]
        
        # Use metadata if provided, otherwise fall back to structure
        if "metadata" in data:
            structure = data["metadata"]
        else:
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
        
        # Return both metadata and structure fields for backward compatibility
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
                'item_order': item.get('ItemOrder', 0)
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
            
            # Convert datasets to frontend format
            datasets = []
            dataset_codes = item.get('DatasetCodes', [])
            for dataset_code in dataset_codes:
                datasets.append({
                    'code': dataset_code,
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
                'ItemOrder': item.get('ItemOrder', 0),
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
        
        # The items are already in the correct metadata format with proper Children fields
        metadata_items = all_items
        
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
            # Transform structure to metadata
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
        indicator_details = sspi_metadata.get_indicator_details()
        
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