from sspi_flask_app.models.errors import InvalidQueryError
# from sspi_flask_app.resources.utilities import lookup_database
import re


def validate_data_query(raw_query_input:dict):
    """
    Returns the raw_query_input iff the query is valid. Raises InvalidQueryError if the query is invalid.

    Validates query parameters including:
    - SeriesCodes, IndicatorCode: Series or indicator codes
    - CountryCode, CountryGroup: Country filters
    - Year, TimePeriod: Time filters
    - YearRangeStart, YearRangeEnd: Year range filters
    """

    def _is_safe(query_string):
        """
        Returns True if the query_string meets the sanitization criteria.

        Fairly restrictive sanitization that allows only alphanumeric characters,
        ampersands, underscores, and hyphens (for time periods like "2000-2004")
        """
        if query_string is None:
            return True
        safe_pattern = r"^[\w\d&-]*$"
        return bool(re.match(safe_pattern, str(query_string)))

    def validate_query_safety(raw_query_input):
        """
        Uses _is_safe to check that the query parameter VALUES are safe.

        Previously this iterated ``enumerate(raw_query_input)``, which for a dict
        yields ``(index, key)`` -- so ``value`` was always a static field name and
        the user-supplied values were never inspected, silently disabling the
        filter. We now validate each value (and each item of list-valued params)
        and reject operator objects (e.g. ``{"$ne": null}``). (Audit finding F6.)
        """
        if len(raw_query_input.keys()) > 200:
            raise InvalidQueryError("Invalid Query: Too many parameters passed")
        for key, value in raw_query_input.items():
            items = value if isinstance(value, list) else [value]
            for item in items:
                if isinstance(item, dict):
                    raise InvalidQueryError(
                        f"Invalid Query: operator objects are not allowed for '{key}'"
                    )
                if not _is_safe(item):
                    raise InvalidQueryError(
                        f"Invalid Query: Unsafe Parameters Passed for '{key}': {item}"
                    )
        return raw_query_input

    return validate_query_safety(raw_query_input)
