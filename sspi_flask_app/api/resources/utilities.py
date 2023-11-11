import json
from bson import json_util
import math

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