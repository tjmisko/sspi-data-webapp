from sspi_flask_app.models.errors import InvalidQueryError
# from sspi_flask_app.resources.utilities import lookup_database
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
        return bool(re.match(safe_pattern, str(query_string)))

    def validate_query_safety(raw_query_input):
        """
        Uses _is_safe to check that the query parameters are safe
        """ 
        if len(raw_query_input.keys()) > 200:
            raise InvalidQueryError("Invalid Query: Too many parameters passed")
        for key, value in enumerate(raw_query_input):
            if (type(value) is str or type(value) is int) and not _is_safe(value):
                raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for {key}: {value}")
            elif type(value) is list and any([not _is_safe(item) for item in value]):
                raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for list {key}")
        return raw_query_input

    return validate_query_safety(raw_query_input)
