from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import Response, current_app as app
from sspi_flask_app.models.database import (
    sspi_indicator_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    score_indicator,
    parse_json,
)


@compute_bp.route("/CHMPOL", methods=["POST"])
@login_required
def compute_chmpol():
    def score_chmpol(UNSDG_STKHLM, UNSDG_MINMAT, UNSDG_MONTRL, UNSDG_BASELA, UNSDG_ROTDAM):
        return (UNSDG_STKHLM + UNSDG_MINMAT + UNSDG_MONTRL + UNSDG_BASELA + UNSDG_ROTDAM) / 5 / 100

    sspi_indicator_data.delete_many({"IndicatorCode": "CHMPOL"})
    filtered_chmpol = sspi_clean_api_data.find({
        "DatasetCode": {
            "$in": [
                "UNSDG_STKHLM",
                "UNSDG_MINMAT",
                "UNSDG_MONTRL",
                "UNSDG_BASELA",
                "UNSDG_ROTDAM"
            ]
        }
    })
    scored_list, _ = score_indicator(
        filtered_chmpol, "CHMPOL",
        score_function=score_chmpol,
        unit="Index" 
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
