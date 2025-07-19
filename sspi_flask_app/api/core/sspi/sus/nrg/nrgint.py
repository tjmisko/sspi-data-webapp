from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.datasource.sdg import (
    collectSDGIndicatorData,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.api.resources.utilities import (
    extrapolate_forward,
    parse_json,
    score_single_indicator,
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_raw_api_data,
)


# @collect_bp.route("/NRGINT", methods=['GET'])
# @login_required
# def nrgint():
#     def collect_iterator(**kwargs):
#         yield from collectSDGIndicatorData("7.3.1", "NRGINT", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/NRGINT", methods=['GET'])
@login_required
def compute_nrgint():
    app.logger.info("Running /api/v1/compute/NRGINT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "NRGINT"})
    nrgint_raw = sspi_raw_api_data.fetch_raw_data("NRGINT")
    extracted_nrgint = extract_sdg(nrgint_raw)
    filtered_nrgint = filter_sdg(
        extracted_nrgint, {"EG_EGY_PRIM": "NRGINT"},
    )
    scored_list = score_single_indicator(filtered_nrgint, "NRGINT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/NRGINT", methods=["POST"])
def impute_nrgint():
    sspi_imputed_data.delete_many({"IndicatorCode": "NRGINT"})
    clean_data = sspi_clean_api_data.find({"IndicatorCode": "NRGINT"})
    imputations = extrapolate_forward(clean_data, 2023, impute_only=True)
    sspi_imputed_data.insert_many(imputations)
    return parse_json(imputations)
