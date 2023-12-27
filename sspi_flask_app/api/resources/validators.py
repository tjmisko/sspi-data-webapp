from ...models.errors import InvalidQueryError
from .utilities import lookup_database
import re

def validate_data_query(raw_query_input:dict):
    """
    Returns the raw_query_input iff the query is valid. Raises InvalidQueryError if the query is invalid.
    """
        
    def _is_safe(query_string):
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
        Uses _is_safe to check that the query parameters are safe
        """ 
        if len(raw_query_input.keys()) > 200:
            raise InvalidQueryError(f"Invalid Query: Too many parameters passed")
        for key, value in enumerate(raw_query_input):
            if type(value) is str and not _is_safe(value):
                raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for {key}: {value}")
            elif type(value) is list and any([not _is_safe(item) for item in value]):
                raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for list {key}")
        return raw_query_input

    def validate_query_logic(raw_query_input):
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
        return raw_query_input

    return validate_query_logic(validate_query_safety(raw_query_input))
