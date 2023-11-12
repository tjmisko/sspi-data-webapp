from .utilities import parse_json
from ... import sspi_metadata
####################
# METADATA QUERIES #
####################

### List commands ##############################################################

### Indicators
def indicator_codes():
    """
    Return a list of all indicator codes in the database
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"indicator_codes": {"$exists": True}}))["indicator_codes"]
    except TypeError:
        return ["Metadata not loaded"]
    return query_result

def indicator_details():
    """
    Return a JSON Object containg indicator details
    """
    indicator_details = parse_json(sspi_metadata.find_one({"indicator_details": {"$exists": True}}))["indicator_details"].values()
    return parse_json(indicator_details)

### Indicator groups
def indicator_groups():
    return pillars().append(categories())

def pillars():
    metadata_response = parse_json(sspi_metadata.find({"PillarCode": {"$exists": True}}))
    return list(set([obs["PillarCode"] for obs in metadata_response]))

def categories():
    metadata_response = parse_json(sspi_metadata.find({"CategoryCode": {"$exists": True}}))
    return list(set([obs["CategoryCode"] for obs in metadata_response]))

def category_details():
    details_object = indicator_details()
    return "Not Implemented Yet"

def pillar_details():
    details_object = indicator_details()
    return "Not Implemented Yet"

### Countries
def country_codes():
    """
    Return a list of all country codes in the database
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"country_codes": {"$exists": True}}))["country_codes"]
    except TypeError:
        return ["Metadata not Loaded"]
    return query_result

def country_groups():
    """
    Return a list of all country groups in the database
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"]
    except TypeError:
        return ["Metadata not Loaded"]
    return parse_json(query_result.keys())

### Query handlers ##############################################################

def country_group(country_group):
    """
    Return a list of all countries in a given country group
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"][country_group]
    except TypeError:
        return ["Metadata not Loaded"]
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
