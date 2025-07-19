from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
from sspi_flask_app.api.datasource.who import (
    collectCSTUNTData
)
import jq


# @collect_bp.route("/CSTUNT", methods=['GET'])
# @login_required
# def cstunt():
#     def collect_iterator(**kwargs):
#         yield from collectCSTUNTData(**kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/CSTUNT", methods=['GET'])
@login_required
def compute_cstunt():
    """
    GHO Reports Two Different Kinds of Series:
    1. NUTRITION_ANT_HAZ_NE2 - Survey-based estimates of child stunting
    2. NUTSTUNTINGPREV       - Model-based estimates of child stunting

    Modeled data has better coverage:
    NUTRITION_ANT_HAZ_NE2 - 999 observations
    NUTSTUNTINGPREV       - 3634 observations
    """
    app.logger.info("Running /api/v1/compute/CSTUNT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CSTUNT"})
    raw_data = sspi_raw_api_data.fetch_raw_data("CSTUNT")[0]["Raw"]["fact"]
    # Slice out the relevant data and identifiers (in Dim array)
    first_slice = '.[] | {IndicatorCode: "CSTUNT", Value: .value.numeric, Dim }'
    first_slice_filter = jq.compile(first_slice)
    dim_list = first_slice_filter.input(raw_data).all()
    # Reduce/Flatten the Dim array
    map_reduce = (
        '.[] |  reduce .Dim[] as $d (.; .[$d.category] = $d.code) | '
        'select(.GHO == "NUTSTUNTINGPREV")'
    )
    map_reduce_filter = jq.compile(map_reduce)
    reduced_list = map_reduce_filter.input(dim_list).all()
    # Remap the keys to the correct names
    rename_keys = (
        '.[] | { IndicatorCode, CountryCode: .COUNTRY,'
        'Year: .YEAR, Value, Unit: "Percentage" }'
    )
    rename_keys_filter = jq.compile(rename_keys)
    value_list = rename_keys_filter.input(reduced_list).all()
    # Score the indicator data
    scored_list = score_single_indicator(value_list, "CSTUNT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
