from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator, goalpost
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data)

from sspi_flask_app.auth.decorators import admin_required


@compute_bp.route("/TXRDST", methods=["POST"])
@admin_required
def compute_txrdst():
    lg, ug = sspi_metadata.get_goalposts("TXRDST")
    def score_txrdst(WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50, WID_NINCSH_POSTTAX_EQUALSPLIT_P90P100, WID_NINCSH_PRETAX_P0P50, WID_NINCSH_PRETAX_P90P100): 
        pretax_ratio = WID_NINCSH_PRETAX_P0P50 / WID_NINCSH_PRETAX_P90P100
        posttax_ratio = WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50 / WID_NINCSH_POSTTAX_EQUALSPLIT_P90P100
        if pretax_ratio == 0:
            app.logger.warning("Pretax ratio is zero, cannot compute TXRDST.")
            return goalpost(0, lg, ug)
        return goalpost((posttax_ratio - pretax_ratio) / pretax_ratio * 100, lg, ug)

    app.logger.info("Running /api/v1/compute/TXRDST")
    sspi_indicator_data.delete_many({"IndicatorCode": "TXRDST"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "TXRDST"})
    lg, ug = sspi_metadata.get_goalposts("TXRDST")
    # Fetch clean datasets
    topten_pretax = sspi_clean_api_data.find({"DatasetCode": "WID_NINCSH_PRETAX_P90P100"})
    bfifty_pretax = sspi_clean_api_data.find({"DatasetCode": "WID_NINCSH_PRETAX_P0P50"})
    topten_posttax = sspi_clean_api_data.find({"DatasetCode": "WID_NINCSH_POSTTAX_EQUALSPLIT_P90P100"})
    bfifty_posttax = sspi_clean_api_data.find({"DatasetCode": "WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50"})
    combined_list = topten_pretax + bfifty_pretax + topten_posttax + bfifty_posttax
    unit = "Ratio of Bottom 50% Income Share to to Top 10% Income Share"
    clean_list, incomplete_list = score_indicator(
        combined_list, "TXRDST",
        score_function=score_txrdst,
        unit=unit
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)

