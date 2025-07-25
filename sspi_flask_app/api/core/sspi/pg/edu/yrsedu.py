from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.datasource.uis import clean_uis_data, collect_uis_data
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    parse_json,
    score_single_indicator,
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_raw_api_data,
)


# @collect_bp.route("/YRSEDU")
# @login_required
# def yrsedu():
#     def collect_iterator(**kwargs):
#         yield from collect_uis_data("YEARS.FC.COMP.1T3", "YRSEDU", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/YRSEDU", methods=['GET'])
@login_required
def compute_yrsedu():
    app.logger.info("Running /api/v1/compute/YRSEDU")
    sspi_clean_api_data.delete_many({"IndicatorCode": "YRSEDU"})
    raw_data = sspi_raw_api_data.fetch_raw_data("YRSEDU")
    description = (
        "Number of years of compulsory primary and secondary "
        "education guaranteed in legal frameworks"
    )
    cleaned_list = clean_uis_data(raw_data, "YRSEDU", "Years", description)
    scored_list = score_single_indicator(cleaned_list, "YRSEDU")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/YRSEDU", methods=["POST"])
def impute_yrsedu():
    sspi_imputed_data.delete_many({"IndicatorCode": "YRSEDU"})
    clean_data = sspi_clean_api_data.find({"IndicatorCode": "YRSEDU"})
    imputations = extrapolate_backward(clean_data, 2000, impute_only=True)
    sspi_imputed_data.insert_many(imputations)
    return parse_json(imputations)
