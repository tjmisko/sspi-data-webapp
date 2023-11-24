from ...models.errors import InvalidDatabaseError, InvalidObservationFormatError, InvalidQueryError
from .utilities import lookup_database
from .metadata import indicator_codes
import re
## test these!

def is_safe(query_string):
    """
    Returns True if the query_string meets the sanitization criteria.

    Fairly restrictive sanitization that allows only alphanumeric characters, ampersands, and underscores
    """
    if query_string is None:
        return True
    safe_pattern = r"^[\w\d&]*$"
    return bool(re.match(safe_pattern, query_string))

def validate_query_safety(raw_query_input):
    """
    Uses is_safe to check that the query parameters are safe
    """ 
    if len(raw_query_input.keys()) > 200:
        raise InvalidQueryError(f"Invalid Query: Too many parameters passed")
    for key, value in enumerate(raw_query_input):
        if type(value) is str and not is_safe(value):
            raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for {key}: {value}")
        elif type(value) is list and any([not is_safe(item) for item in value]):
            raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for list {key}")
    return raw_query_input

def validate_query_logic(raw_query_input, requires_database=False):
    """
    Checks that the query parameters are logically valid
    """
    if raw_query_input["IndicatorCode"] and raw_query_input["IndicatorGroup"] is not None:
        raise InvalidQueryError("Invalid Query: Cannot query both IndicatorCode and IndicatorGroup")
    if raw_query_input["CountryCode"] and raw_query_input["CountryGroup"] is not None:
        raise InvalidQueryError("Invalid Query: Cannot query both CountryCode and CountryGroup")
    if raw_query_input["YearRangeStart"] is not None and raw_query_input["YearRangeEnd"] is None:
        raise InvalidQueryError("Invalid Query: Must specify both YearRangeStart and YearRangeEnd to use a Year Range")
    if raw_query_input["YearRangeStart"] is None and raw_query_input["YearRangeEnd"] is not None:
        raise InvalidQueryError("Invalid Query: Must specify both YearRangeStart and YearRangeEnd to use a Year Range")
    if raw_query_input["Year"] and (raw_query_input["YearRangeStart"] is not None or raw_query_input["YearRangeEnd"] is not None):
        raise InvalidQueryError("Invalid Query: Cannot query both Year and Year Range")
    if raw_query_input["Year"]:
        try:
            raw_query_input["Year"] = [int(year) for year in raw_query_input["Year"]]
        except ValueError:
            raise InvalidQueryError("Invalid Query: Year must be integers")
    if raw_query_input["YearRangeStart"] is not None and raw_query_input["YearRangeEnd"] is not None:
        try:
            year_list = list(range(int(raw_query_input["YearRangeStart"]), int(raw_query_input["YearRangeEnd"])+1))
        except ValueError:
            raise InvalidQueryError("Invalid Query: Year Range must be integers")
        if len(year_list) == 0:
            raise InvalidQueryError("Invalid Query: YearRangeStart must be greater than YearRangeEnd")
        raw_query_input["Year"] = year_list
    if requires_database:
        if raw_query_input["Database"] is None:
            raise InvalidQueryError("Invalid Query: Must specify a database")
        database = lookup_database(raw_query_input["Database"])
        if database is None:
            raise InvalidQueryError("Invalid Query: Database not found")
        raw_query_input["Database"] = database
    return raw_query_input

def validate_observation_list(observations_list, database_name, IndicatorCode):
    """
    Checks that observations being inserted into a database have the correct format
    """
    database = lookup_database(database_name)
    for i, obs in enumerate(observations_list):
        print(obs)
        CountryCode = obs.get("CountryCode")
        Year = obs.get("Year")
        IndicatorCodeFromData = obs.get("IndicatorCode")
        if IndicatorCodeFromData != IndicatorCode:
            raise InvalidObservationFormatError(f"Observation has incorrect Indicator Code for observation {i+1}")
        if CountryCode is None or Year is None or IndicatorCodeFromData is None:
            raise InvalidObservationFormatError(f"Observation missing required ID variable for observation {i+1}")
        if IndicatorCodeFromData not in indicator_codes():
            raise InvalidObservationFormatError(f"Invalid Indicator Code for observation {i+1}")
    return True
