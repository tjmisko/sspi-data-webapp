from io import BytesIO
from flask import Blueprint, request, send_file, jsonify
import pandas as pd
from pymongo.errors import OperationFailure

from ..resources.utilities import lookup_database, parse_json, public_databases
from ..resources.query_builder import get_query_params
from sspi_flask_app.models.database import sspidb, sspi_metadata
from sspi_flask_app.models.errors import InvalidDatabaseError, InvalidQueryError
import json


download_bp = Blueprint(
    "download_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/download"
)

# Filter public databases to only those that exist in the database
db_choices = [db for db in public_databases if db['name'] in sspidb.list_collection_names()]
ic_choices = sspi_metadata.indicator_codes()
cg_choices = sspi_metadata.country_groups()


def fetch_data_for_download(request_args):
    """
    Fetches data for download using the shared query builder.
    Unsupported parameters for the selected database are silently ignored.

    Args:
        request_args: Flask request.args (ImmutableMultiDict)

    Returns:
        list: List of documents matching the query

    Raises:
        InvalidDatabaseError: If the requested database is not allowed
        InvalidQueryError: If query parameters are invalid
        OperationFailure: If database operation fails
    """
    # Get and validate database name
    database_name = request_args.get("database", default="sspi_static_data_2018")
    allowed_db_names = [db['name'] for db in public_databases]

    if database_name not in allowed_db_names:
        raise InvalidDatabaseError(
            f"Database '{database_name}' is not allowed for download. "
            f"Allowed databases: {', '.join(allowed_db_names)}"
        )

    # Lookup database collection
    database = lookup_database(database_name)

    # Build query using shared query builder
    # The query builder will handle database-specific schemas and ignore unsupported parameters
    mongo_query = get_query_params(request, database)

    # Execute query and return results
    data_to_download = parse_json(database.find(mongo_query, options={"_id": 0}))
    return data_to_download


@download_bp.route("/databases")
def list_databases():
    """
    List all available databases with their supported parameters.

    Returns:
        JSON response with database information
    """
    return jsonify({
        "databases": [
            {
                "name": db['name'],
                "description": db['description'],
                "supported_parameters": db['supports'],
                "schema_type": db['schema_type']
            }
            for db in db_choices
        ]
    })


@download_bp.route("/csv")
def download_csv():
    """
    Download the data from the database in CSV format.

    Query Parameters:
        - database: Database name (default: sspi_static_data_2018)
        - SeriesCode / IndicatorCode: Series/indicator codes to filter
        - DatasetCode: Dataset codes to filter (for clean/raw data)
        - CountryCode: Country codes to filter
        - CountryGroup: Country group name to filter
        - Year: Individual years to include
        - timePeriod: Time period labels to expand (e.g., "2000-2004")
        - YearRangeStart / YearRangeEnd: Year range to include

    Note: Not all parameters are supported by all databases. Use /download/databases
    to see which parameters are supported by each database.

    Returns:
        CSV file download or JSON error message
    """
    try:
        data_to_download = fetch_data_for_download(request.args)

        if not data_to_download:
            return jsonify({
                "warning": "No data matched your query criteria",
                "hint": "Try broadening your search parameters or use /download/databases to see supported parameters"
            }), 404

        df = pd.DataFrame(data_to_download).to_csv()
        mem = BytesIO()
        mem.write(df.encode('utf-8'))
        mem.seek(0)
        return send_file(
            mem,
            mimetype='text/csv',
            download_name='SSPIData.csv',
            as_attachment=True
        )
    except InvalidDatabaseError as e:
        return jsonify({"error": str(e)}), 400
    except InvalidQueryError as e:
        return jsonify({"error": str(e)}), 400
    except OperationFailure as e:
        return jsonify({"error": "Database Operation Failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected Error: " + str(e)}), 500


@download_bp.route("/json")
def download_json():
    """
    Download data from the database in JSON format.

    Query Parameters:
        - database: Database name (default: sspi_static_data_2018)
        - SeriesCode / IndicatorCode: Series/indicator codes to filter
        - DatasetCode: Dataset codes to filter (for clean/raw data)
        - CountryCode: Country codes to filter
        - CountryGroup: Country group name to filter
        - Year: Individual years to include
        - timePeriod: Time period labels to expand (e.g., "2000-2004")
        - YearRangeStart / YearRangeEnd: Year range to include

    Note: Not all parameters are supported by all databases. Use /download/databases
    to see which parameters are supported by each database.

    Returns:
        JSON file download or JSON error message
    """
    try:
        data_to_download = fetch_data_for_download(request.args)

        if not data_to_download:
            return jsonify({
                "warning": "No data matched your query criteria",
                "hint": "Try broadening your search parameters or use /download/databases to see supported parameters"
            }), 404

        mem = BytesIO()
        mem.write(json.dumps(data_to_download).encode('utf-8'))
        mem.seek(0)
        return send_file(
            mem,
            mimetype='application/json',
            download_name='SSPIData.json',
            as_attachment=True
        )
    except InvalidDatabaseError as e:
        return jsonify({"error": str(e)}), 400
    except InvalidQueryError as e:
        return jsonify({"error": str(e)}), 400
    except OperationFailure as e:
        return jsonify({"error": "Database Operation Failed: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected Error: " + str(e)}), 500
