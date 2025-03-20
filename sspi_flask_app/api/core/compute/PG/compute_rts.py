from flask import redirect, url_for
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)


@compute_bp.route("/EDEMOC", methods=['GET'])
@login_required
def compute_edemoc():
    # Check if raw data is available; if not, redirect to the collection route.
    if not sspi_raw_api_data.raw_data_available("EDEMOC"):
        return redirect(url_for("collect_bp.EDEMOC"))
    # Fetch the raw data for EDEMOC.
    raw_data = sspi_raw_api_data.fetch_raw_data("EDEMOC")
    document_list = []
    for obs in raw_data:
        try:
            # Access the nested raw data.
            data = obs["Raw"]["Raw"]
            country_code = data["Country"]  # Should be a three-letter ISO code (e.g., "MEX")
            # Convert the raw "Year" field to an integer.
            raw_year = int(data["Year"])
            # Drop observations where the year is not within the allowed range.
            if raw_year < 1900 or raw_year > 2030:
                print(f"Skipping observation with out-of-range year: {raw_year}")
                continue
            # Convert the v2x_polyarchy value to a float.
            v2x_polyarchy = float(data["Value"])
            # Build the computed document.
            document = {
                "IndicatorCode": "EDEMOC",
                "CountryCode": country_code,
                "Year": raw_year,
                "Intermediates": {"v2x_polyarchy": v2x_polyarchy},
                "Value": v2x_polyarchy,  # The computed value is the v2x_polyarchy value.
                "Unit": "Index",  # Data is sourced from a published index.
                "Score": v2x_polyarchy  # Score is the computed value.
            }
            document_list.append(document)
        except Exception as e:
            # Log error and skip this observation if an exception occurs.
            print(f"Error processing observation: {e}")
            continue
    # Insert computed documents into the clean API data collection.
    sspi_clean_api_data.insert_many(document_list)
    return parse_json(document_list)
