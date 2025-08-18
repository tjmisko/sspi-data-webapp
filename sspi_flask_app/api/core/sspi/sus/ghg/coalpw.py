from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.api.core.sspi import compute_bp
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
import pandas as pd
import json


@compute_bp.route("/COALPW", methods=["POST"])
@login_required
def compute_coalpw():
    lg, ug = sspi_metadata.get_goalposts("COALPW")
    def score_coalpw(IEA_TLCOAL, IEA_NATGAS, IEA_NCLEAR, IEA_HYDROP, IEA_GEOPWR, IEA_BIOWAS, IEA_FSLOIL):
        IEA_TTLSUM = IEA_TLCOAL + IEA_NATGAS + IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS + IEA_FSLOIL
        return goalpost(IEA_TLCOAL / IEA_TTLSUM, lg, ug)
        
    sspi_indicator_data.delete_many({"IndicatorCode": "COALPW"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "COALPW"})
    dataset_codes = ["IEA_TLCOAL", "IEA_NATGAS", "IEA_NCLEAR", "IEA_HYDROP", "IEA_GEOPWR", "IEA_BIOWAS", "IEA_FSLOIL"]
    coalpw_datasets = sspi_clean_api_data.find({"DatasetCode": {"$in": dataset_codes}})
    clean_list, incomplete_list = score_indicator(
        coalpw_datasets,
        "COALPW",
        score_function=score_coalpw,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
