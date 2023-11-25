import json
from bson import json_util
import math
from ... import sspi_main_data_v3, sspi_bulk_data, sspi_raw_api_data, sspi_clean_api_data, sspi_imputed_data, sspi_metadata, sspi_dynamic_data
from sspi_flask_app.models.errors import InvalidDatabaseError

def format_m49_as_string(input):
    """
    Utility function ensuring that all M49 data is correctly formatted as a
    string of length 3 for use with the pycountry library
    """
    input = int(input)
    if input >= 100:
        return str(input) 
    elif input >= 10:
        return '0' + str(input)
    else: 
        return '00' + str(input)

def parse_json(data):
    return json.loads(json_util.dumps(data))

def print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

def lookup_database(database_name):
    """
    Utility function used for safe database lookup
    Returns nothing if the database name is incorrect
    """
    if database_name == "sspi_main_data_v3":
        return sspi_main_data_v3
    elif database_name == "sspi_bulk_data":
        return sspi_bulk_data
    elif database_name == "sspi_raw_api_data":
        return sspi_raw_api_data
    elif database_name == "sspi_clean_api_data":
        return sspi_clean_api_data
    elif database_name == "sspi_imputed_data":
        return sspi_imputed_data
    elif database_name == "sspi_metadata":
        return sspi_metadata
    elif database_name == "sspi_dynamic_data":
        return sspi_dynamic_data
    raise InvalidDatabaseError(database_name)

def string_to_float(string):
    """
    Passes back string 'NaN' instead of float NaN
    """
    if math.isnan(float(string)):
        return "NaN"
    return float(string)

def string_to_int(string):
    return int(string)

def missing_countries(sspi_country_list, source_country_list):
    missing_countries = []
    for country in sspi_country_list:
        if country not in source_country_list:
            missing_countries.append(country)
    return missing_countries

def added_countries(sspi_country_list, source_country_list):
    additional_countries = []
    for other_country in source_country_list:
        if other_country not in sspi_country_list:
            additional_countries.append(other_country)
    return additional_countries