from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
)


@compute_bp.route("/GTRANS", methods=["POST"])
@login_required
def compute_gtrans():
    app.logger.info("Running /api/v1/compute/GTRANS")
    sspi_indicator_data.delete_many({"IndicatorCode": "GTRANS"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "GTRANS"})
    tco2em_clean = sspi_clean_api_data.find({"DatasetCode": "IEA_TCO2EM"})
    populn_clean = sspi_clean_api_data.find({"DatasetCode": "WB_POPULN"})
    combined_list = tco2em_clean + populn_clean
    lg, ug = sspi_metadata.get_goalposts("GTRANS")
    clean_list, incomplete_list = score_indicator(
        combined_list,
        "GTRANS",
        score_function=lambda IEA_TCO2EM, WB_POPULN: goalpost(IEA_TCO2EM / WB_POPULN, lg, ug),
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
