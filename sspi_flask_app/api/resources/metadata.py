from .utilities import parse_json
from ... import sspi_metadata
####################
# METADATA QUERIES #
####################

def country_groups():
    """
    Return a list of all country groups in the database
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"]
    except TypeError:
        return ["Metadata not Loaded"]
    return parse_json(query_result.keys())

def country_group(country_group):
    """
    Return a list of all countries in a given country group
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"][country_group]
    except TypeError:
        return ["Metadata not Loaded"]
    return query_result

def indicator_codes():
    """
    Return a list of all indicator codes in the database
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"indicator_codes": {"$exists": True}}))["indicator_codes"]
    except TypeError:
        return ["Metadata not loaded"]
    return query_result

def indicator_group(indicator_group):
    """
    Return a list of all indicators in a given indicator group
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"indicator_groups": {"$exists": True}}))["indicator_groups"][indicator_group]
    except TypeError:
        return ["Metadata not loaded"]
    return query_result

def indicator_details():
    indicator_details = parse_json(sspi_metadata.find_one({"indicator_details": {"$exists": True}}))["indicator_details"].values()
    return parse_json(indicator_details)