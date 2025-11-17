from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    parse_json,
    score_indicator,
    goalpost)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)


@compute_bp.route("/YRSEDU", methods=['POST'])
@admin_required
def compute_yrsedu():
    app.logger.info("Running /api/v1/compute/YRSEDU")
    sspi_indicator_data.delete_many({"IndicatorCode": "YRSEDU"})
    yrsedu_clean = sspi_clean_api_data.find({"DatasetCode": "UIS_YRSEDU"})
    lg, ug = sspi_metadata.get_goalposts("YRSEDU")
    scored_list, _ = score_indicator(
        yrsedu_clean, "YRSEDU",
        score_function=lambda UIS_YRSEDU: goalpost(UIS_YRSEDU, lg, ug),
        unit="Years"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/YRSEDU", methods=["POST"])
@admin_required
def impute_yrsedu():
    sspi_imputed_data.delete_many({"IndicatorCode": "YRSEDU"})
    clean_data = sspi_clean_api_data.find({"DatasetCode": "UIS_YRSEDU"})
    imputations = extrapolate_backward(clean_data, 2000, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("YRSEDU")
    scored_list, _ = score_indicator(
        imputations, "YRSEDU",
        score_function=lambda UIS_YRSEDU: goalpost(UIS_YRSEDU, lg, ug),
        unit="Years"
    )
    sspi_imputed_data.insert_many(scored_list)
    return parse_json(scored_list)
