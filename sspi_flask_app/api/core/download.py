from io import BytesIO
from flask import Blueprint, request, send_file
import pandas as pd
from ..resources.utilities import lookup_database, parse_json
from sspi_flask_app.models.database import sspidb, sspi_metadata
import json


download_bp = Blueprint(
    "download_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/download"
)

# Only allow downloading from specific databases
allowed_databases = [
    'sspi_score_data',
    'sspi_indicator_data', 
    'sspi_clean_api_data',
    'sspi_main_data_v3'
]
db_choices = [db for db in allowed_databases if db in sspidb.list_collection_names()]
ic_choices = sspi_metadata.indicator_codes()
cg_choices = sspi_metadata.country_groups()


def get_all_indicator_descendants(item_code):
    """
    Recursively get all indicator codes that descend from a given item code.
    
    Args:
        item_code (str): The item code to expand (SSPI, Pillar, Category, or Indicator)
        
    Returns:
        set: Set of indicator codes that are descendants of the given item
    """
    try:
        item_detail = sspi_metadata.get_item_detail(item_code)
        item_type = item_detail.get('ItemType', 'Unknown')
        
        if item_type == 'Indicator':
            return {item_code}
        
        # For SSPI, Pillar, or Category, recursively get all indicators
        indicator_codes = set()
        children_codes = item_detail.get('Children', [])
        
        for child_code in children_codes:
            child_indicators = get_all_indicator_descendants(child_code)
            indicator_codes.update(child_indicators)
        
        return indicator_codes
        
    except Exception as e:
        # If there's an error getting item detail, assume it's an indicator
        return {item_code}


def expand_codes_to_indicators(codes):
    """
    Expand mixed codes (SSPI, pillar, category, indicator) to indicator codes only.
    
    Args:
        codes (list): List of mixed item codes
        
    Returns:
        list: List of indicator codes only
    """
    if not codes:
        return []
    
    indicator_codes = set()
    
    for code in codes:
        if not code:  # Skip empty strings
            continue
            
        # Get all indicator descendants of this code
        descendants = get_all_indicator_descendants(code)
        indicator_codes.update(descendants)
    
    return list(indicator_codes)


def fetch_data_for_download(request_args):
    """
    request_args has type ImmutableMultiDict
    """
    mongo_query = {}
    if request_args.getlist('IndicatorCode'):
        # Expand mixed codes to indicator codes only
        mixed_codes = request.args.getlist('IndicatorCode')
        indicator_codes = expand_codes_to_indicators(mixed_codes)
        mongo_query["IndicatorCode"] = {
            "$in": indicator_codes}
    if request_args.get('CountryGroup'):
        group = request.args.get('CountryGroup')
        if not group:
            return []
        group_countries = sspi_metadata.country_group(group)
        mongo_query['CountryCode'] = {
            "$in": group_countries
        }
    elif request_args.getlist('CountryCode'):
        mongo_query["CountryCode"] = {
            "$in": request.args.getlist('CountryCode')
        }
    if request_args.getlist('Year'):
        mongo_query["Year"] = {
            "$in": [int(year) for year in request.args.getlist('Year')]
        }
    elif request_args.getlist('timePeriod'):
        mongo_query["Year"] = {
            "$in": [int(year) for year in request.args.getlist('timePeriod')]
        }
    database_name = request_args.get("database", default="sspi_main_data_v3")
    
    # Validate that requested database is allowed
    if database_name not in allowed_databases:
        return []
    
    database = lookup_database(database_name)
    data_to_download = parse_json(database.find(mongo_query))
    return data_to_download


@download_bp.route("/csv")
def download_csv():
    """
    Download the data from the database in csv format
    """
    data_to_download = fetch_data_for_download(request.args)
    df = pd.DataFrame(data_to_download).to_csv()
    mem = BytesIO()
    mem.write(df.encode('utf-8'))
    mem.seek(0)
    return send_file(
        mem,
        mimetype='text/csv',
        download_name='SSPIData.csv',
        as_attachment=True
    )


@download_bp.route("/json")
def download_json():
    """
    Download data from the database in json format
    """
    data_to_download = fetch_data_for_download(request.args)
    mem = BytesIO()
    mem.write(json.dumps(data_to_download).encode('utf-8'))
    mem.seek(0)
    return send_file(
        mem,
        mimetype='application/json',
        download_name='SSPIData.json',
        as_attachment=True
    )
