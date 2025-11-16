"""
Shared query building utilities for SSPI API endpoints.

This module provides database-aware query construction that handles:
- Input validation and sanitization
- Time period expansion (e.g., "2000-2004" -> [2000, 2001, 2002, 2003, 2004])
- Different database schemas (raw data vs processed data)
- Multiple code types (ItemCode, DatasetCode, IndicatorCode, etc.)
- Country groups and year ranges
"""

from sspi_flask_app.models.database import sspi_metadata, sspi_raw_api_data
from sspi_flask_app.api.resources.validators import validate_data_query
from sspi_flask_app.models.errors import InvalidQueryError


def get_query_params(request, database=None):
    """
    Extracts and validates query parameters from a Flask request.

    Supports both standard parameter names and aliases:
    - Year / timePeriod: Individual years or time period labels
    - SeriesCode / IndicatorCode / DatasetCode: Series/indicator/dataset codes to query

    Args:
        request: Flask request object containing query parameters
        database: MongoDB collection object for database-specific handling

    Returns:
        dict: MongoDB query dictionary ready for database.find()

    Raises:
        InvalidQueryError: If query parameters are invalid or unsafe
    """
    # Extract and normalize parameters
    # SeriesCodes can come from SeriesCode, IndicatorCode, or DatasetCode params
    series_codes = (
        request.args.getlist("SeriesCode") or
        request.args.getlist("IndicatorCode") or
        request.args.getlist("DatasetCode")
    )

    raw_query_input = {
        "SeriesCodes": series_codes,
        "CountryCode": request.args.getlist("CountryCode"),
        "CountryGroup": request.args.get("CountryGroup"),
        "Year": request.args.getlist("Year"),
        "TimePeriod": request.args.getlist("timePeriod"),
        "YearRangeStart": request.args.get("YearRangeStart"),
        "YearRangeEnd": request.args.get("YearRangeEnd"),
    }

    # Validate input for security
    validated_query_input = validate_data_query(raw_query_input)

    # Build and return MongoDB query
    return build_mongo_query(validated_query_input, database)


def expand_time_periods(time_period_labels):
    """
    Expands time period labels to lists of years using sspi_metadata.

    Args:
        time_period_labels: List of time period labels (e.g., ["2000", "2000-2004"])

    Returns:
        list: Expanded list of years as integers

    Example:
        >>> expand_time_periods(["2000", "2000-2004"])
        [2000, 2000, 2001, 2002, 2003, 2004]
    """
    if not time_period_labels:
        return []

    expanded_years = []
    for label in time_period_labels:
        if not label:  # Skip empty strings
            continue

        # Try to get time period detail from metadata
        time_period_detail = sspi_metadata.get_time_period_detail(label)

        if time_period_detail and "Metadata" in time_period_detail:
            # Found a defined time period - use its years
            years = time_period_detail["Metadata"].get("Years", [])
            expanded_years.extend(years)
        else:
            # Not a defined time period - try to parse as a single year
            try:
                year = int(label)
                expanded_years.append(year)
            except ValueError:
                # Invalid time period label - skip it
                pass

    return expanded_years


def build_mongo_query(raw_query_input, database=None):
    """
    Builds a MongoDB query from validated input parameters.

    Handles database-specific schemas:
    - Raw data: Uses Source.OrganizationCode and Source.QueryCode
    - Processed data: Uses standard fields (ItemCode, CountryCode, Year, etc.)

    Args:
        raw_query_input: Validated query parameters dictionary
        database: MongoDB collection object for database-specific handling

    Returns:
        dict: MongoDB query dictionary

    Raises:
        InvalidQueryError: If query construction fails
    """
    mongo_query = {}  # Empty query returns all documents

    # Handle SeriesCodes (ItemCodes, IndicatorCodes, DatasetCodes, etc.)
    if raw_query_input["SeriesCodes"]:
        item_codes = raw_query_input["SeriesCodes"]
        dataset_codes = []

        # Get all dataset dependencies for the series codes
        for sc in raw_query_input["SeriesCodes"]:
            dataset_codes += sspi_metadata.get_dataset_dependencies(sc)
        dataset_codes = list(set(dataset_codes))

        # Special handling for raw data queries - use Source fields
        if database is sspi_raw_api_data:
            source_queries = []
            for dataset_code in dataset_codes:
                source_info = sspi_metadata.get_source_info(dataset_code)
                source_queries.append(
                    {
                        "Source.OrganizationCode": source_info["OrganizationCode"],
                        "Source.QueryCode": source_info["QueryCode"],
                    }
                )
            mongo_query = {"$or": source_queries}
            if not source_queries:
                raise InvalidQueryError(
                    "Invalid Query: No valid source queries found for raw data. "
                    "The provided SeriesCodes did not resolve to valid datasets."
                )
        else:
            # Standard databases - query by various code types
            mongo_query = {
                "$or": [
                    {"ItemCode": {"$in": item_codes}},
                    {"DatasetCode": {"$in": dataset_codes}},
                    {"IndicatorCode": {"$in": item_codes}},
                    {"CategoryCode": {"$in": item_codes}},
                    {"PillarCode": {"$in": item_codes}},
                ]
            }

    # Don't apply CountryCode and Year filters to raw data - it doesn't have these fields
    if database is not sspi_raw_api_data:
        # Handle Country filtering
        country_codes = set()
        if raw_query_input["CountryGroup"]:
            country_codes.update(
                sspi_metadata.country_group(raw_query_input["CountryGroup"])
            )
        if raw_query_input["CountryCode"]:
            country_codes.update(raw_query_input["CountryCode"])
        if country_codes:
            mongo_query["CountryCode"] = {"$in": list(country_codes)}

        # Handle Year filtering with time period expansion
        years = set()

        # Add individual years
        if raw_query_input["Year"]:
            years.update([int(y) for y in raw_query_input["Year"]])

        # Expand and add time periods
        if raw_query_input["TimePeriod"]:
            expanded_years = expand_time_periods(raw_query_input["TimePeriod"])
            years.update(expanded_years)

        # Add year ranges
        if raw_query_input["YearRangeStart"] and raw_query_input["YearRangeEnd"]:
            start_year = int(raw_query_input["YearRangeStart"])
            end_year = int(raw_query_input["YearRangeEnd"])
            years.update(range(start_year, end_year + 1))

        if years:
            mongo_query["Year"] = {"$in": list(years)}

    return mongo_query
