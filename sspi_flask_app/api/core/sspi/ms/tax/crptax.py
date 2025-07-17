from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import collect_bp, compute_bp, impute_bp
from sspi_flask_app.api.datasource.taxfoundation import (
    cleanTaxFoundation,
    collectTaxFoundationData,
)
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    interpolate_linear,
    parse_json,
    score_single_indicator,
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_raw_api_data,
)


# @collect_bp.route("/CRPTAX", methods=['GET'])
# @login_required
# def crptax():
#     def collect_iterator(**kwargs):
#         yield from collectTaxFoundationData('CRPTAX', **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/CRPTAX")
@login_required
def compute_crptax():
    app.logger.info("Running /api/v1/compute/CRPTAX")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CRPTAX"})
    crptax_raw = sspi_raw_api_data.fetch_raw_data("CRPTAX")
    crptax_clean = cleanTaxFoundation(crptax_raw, "CRPTAX", "Tax Rate", "Corporate Taxes")
    scored_list = score_single_indicator(crptax_clean, "CRPTAX")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/CRPTAX", methods=['POST'])
@login_required
def impute_crptax():
    app.logger.info("Running /api/v1/impute/CRPTAX")
    sspi_imputed_data.delete_many({"IndicatorCode": "CRPTAX"})
    clean_crptax = sspi_clean_api_data.find({"IndicatorCode": "CRPTAX"})
    # forward = extrapolate_forward(clean_crptax, 2023, impute_only=True)
    backward = extrapolate_backward(clean_crptax, 2000, impute_only=True)
    interpolated = interpolate_linear(clean_crptax, impute_only=True)
    imputed_crptax = backward + interpolated
    sspi_imputed_data.insert_many(imputed_crptax) 
    return parse_json(imputed_crptax)
