from flask import redirect, url_for
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    jsonify_df,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)
import pandas as pd
from io import StringIO


from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_intrnt,
)


@compute_bp.route("/INTRNT", methods=['GET'])
@login_required
def compute_intrnt():
    if not sspi_raw_api_data.raw_data_available("INTRNT"):
        return redirect(url_for("collect_bp.INTRNT"))
    # worldbank #
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="AVINTR")
    wb_clean = clean_wb_data(wb_raw, "INTRNT", unit="Percent")
    # sdg #
    sdg_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="QLMBPS")
    sdg_clean = extract_sdg_pivot_data_to_nested_dictionary(sdg_raw)
    sdg_clean = flatten_nested_dictionary_intrnt(sdg_clean)
    combined_list = wb_clean + sdg_clean
    cleaned_list = zip_intermediates(combined_list, "INTRNT",
                                     ScoreFunction=lambda AVINTR, QUINTR: 0.5 * AVINTR + 0.5 * QUINTR,
                                     ScoreBy="Score")
    filtered_list, incomplete_observations = filter_incomplete_data(
        cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)


@compute_bp.route("/AQELEC", methods=["GET"])
@login_required
def compute_aqelec():
    """
    Compute route for AQELEC.

    - Checks if raw data for AQELEC is available; if not, redirects to the collection route.
    - Processes each raw document to extract CountryCode, Year, IntermediateCode, and Value.
      If the value is not directly available, CSV content is parsed.
    - Uses CSV data to extract a valid CountryCode if the raw document does not include one.
    - Skips any document that does not yield a valid numeric value or a valid 3-character CountryCode.
    - Uses zip_intermediates to group observations by CountryCode and Year and computes the
      final score as the average of the available intermediate values.
    - Filters out incomplete documents. If no clean documents exist, returns an empty JSON array.
    - Otherwise, stores the cleaned data and returns a JSON response.
    """
    quality_data = sspi_raw_api_data.fetch_raw_data("AQELEC", IntermediateCode="QUELCT")[0]
    quality_df = pd.read_csv(StringIO(quality_data["Raw"]["csv"]))
    ## cleaning steps here
    list_of_quality_observation = []
    availability_data = sspi_raw_api_data.fetch_raw_data("AQELEC", IntermediateCode="AVELEC")
    ## cleaning steps here
    list_of_quality_observation = []
    zip_intermediates
    return jsonify_df(quality_df)
