from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_dataset_value
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)
import json

@compute_bp.route("/MILEXP", methods=['POST'])
@login_required
def compute_milexp():
    sspi_indicator_data.delete_many({"IndicatorCode": "MILEXP"})
    sipri_milexp_clean = sspi_clean_api_data.find({"DatasetCode": "SIPRI_MILEXP"})
    lg, ug = sspi_metadata.get_goalposts("MILEXP")
    scored_list, _ = score_indicator(
        sipri_milexp_clean, "MILEXP",
        score_function=lambda SIPRI_MILEXP: goalpost(SIPRI_MILEXP, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)

@impute_bp.route("/MILEXP", methods=['POST'])
@login_required
def impute_milexp():
    sspi_imputed_data.delete_many({"IndicatorCode": "MILEXP"})
    clean_milexp = sspi_clean_api_data.find({"DatasetCode": "SIPRI_MILEXP"})
    forward = extrapolate_forward(clean_milexp, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(clean_milexp, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_milexp, ["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("MILEXP")
    milexp_isl = impute_dataset_value("ISL", 2000, 2023, "SIPRI_MILEXP", 0, clean_milexp[0]["Unit"])
    imputed_milexp, _ = score_indicator(
        forward + backward + interpolated + milexp_isl, "MILEXP",
        score_function=lambda SIPRI_MILEXP: goalpost(SIPRI_MILEXP, lg, ug),
        unit="%"
    )
    sspi_imputed_data.insert_many(imputed_milexp)
    return parse_json(imputed_milexp)

