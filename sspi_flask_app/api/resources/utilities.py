import json
from bson import json_util
from flask import jsonify
import pandas as pd
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

def jsonify_df(df:pd.DataFrame):
    """
    Utility function for converting a dataframe to a JSON object
    """
    return jsonify(json.loads(str(df.to_json(orient='records'))))

def goalpost(value, lower, upper):
    """ Implement the goalposting formula"""
    return max(0, min(1, (value - lower)/(upper - lower)))

def parse_json(data):
    return json.loads(json_util.dumps(data))

def lookup_database(database_name):
    """
    Utility function used for safe database lookup

    Throws an error otherwise
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

def zip_intermediates(intermediate_document_list, IndicatorCode, ScoreFunction, ScoreBy="Value"):
    """
    Utility function for zipping together the sspi_data and source_data
    """
    validated_intermediate_list = validate_intermediate_list(intermediate_document_list)
    gp_intermediate_list = append_goalpost_info(validated_intermediate_list)
    indicator_document_list = group_by_indicator(gp_intermediate_list)
    scored_indicator_document_list = score_indicator_documents(indicator_document_list, ScoreFunction, ScoreBy)
    return scored_indicator_document_list
    
    
def validate_intermediate_list(intermediate_document_list):
    """
    Utility function for validating the format of a document
    """
    for document in intermediate_document_list:
