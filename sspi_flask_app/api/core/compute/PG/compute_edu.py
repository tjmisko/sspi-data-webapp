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
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_enrpri
)



@compute_bp.route("/ENRPRI", methods=['GET'])
@login_required
def compute_enrpri():
    if not sspi_raw_api_data.raw_data_available("ENRPRI"):
        return redirect(url_for("api_bp.collect_bp.ENRPRI"))
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRPRI")
    both_sex_primary = [obs for obs in raw_data if obs["Raw"]
                     ["education_level"] == "PRIMAR" and obs["Raw"]["sex"] == "BOTHSEX"]
    intermediate_list = extract_sdg_pivot_data_to_nested_dictionary(both_sex_primary)
    return parse_json(intermediate_list)

