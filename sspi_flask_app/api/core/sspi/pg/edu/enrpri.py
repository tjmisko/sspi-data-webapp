from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import collect_bp, compute_bp, impute_bp
from sspi_flask_app.api.datasource.uis import (
    cleanUISdata,
    collectUISdata,
)
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    extrapolate_forward,
    impute_global_average,
    interpolate_linear,
    parse_json,
    score_single_indicator,
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_metadata,
    sspi_raw_api_data,
)


# @collect_bp.route("/ENRPRI", methods=['GET'])
# @login_required
# def enrpri():
#     def collect_iterator(**kwargs):
#         yield from collectUISdata("NERT.1.CP", "ENRPRI", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ENRPRI", methods=['GET'])
@login_required
def compute_enrpri():
    app.logger.info("Running /api/v1/compute/ENRPRI")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ENRPRI"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRPRI")
    description = "Net enrollment in primary school (%)"
    cleaned_list = cleanUISdata(raw_data, "ENRPRI", "Percent", description)
    scored_list = score_single_indicator(cleaned_list, "ENRPRI")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/ENRPRI", methods=['POST'])
@login_required
def impute_enrpri():
    app.logger.info("Running /api/v1/impute/ENRPRI")
    sspi_imputed_data.delete_many({"IndicatorCode": "ENRPRI"})
    clean_enrpri = sspi_clean_api_data.find({"IndicatorCode": "ENRPRI"})
    forward = extrapolate_forward(clean_enrpri, 2023, impute_only=True)
    backward = extrapolate_backward(clean_enrpri, 2000, impute_only=True)
    interpolated = interpolate_linear(clean_enrpri, impute_only=True)
    imputed_enrpri = forward + backward + interpolated
    # Handle China, which is missing all observations
    # chn_enrpri = impute_global_average("CHN", 2000, 2023, "Indicator", "ENRPRI", clean_enrpri)
    # Actually: China has observations from the 1990s. Would it be better to extrapolate these forward for twenty five years? Or to rely on the global average?
    # sspi_imputed_data.insert_many(imputed_enrpri + chn_enrpri)
    sspi_imputed_data.insert_many(imputed_enrpri)
    # return parse_json(imputed_enrpri + chn_enrpri)
    return parse_json(imputed_enrpri)
