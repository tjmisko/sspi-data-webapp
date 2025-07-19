from flask_login import login_required, current_user
from flask import Response, current_app as app
from sspi_flask_app.api.datasource.iea import collectIEAData
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data,
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
)
import pandas as pd
from sspi_flask_app.api.datasource.iea import cleanIEAData_altnrg
import json


# @collect_bp.route("/COALPW", methods=["GET"])
# @login_required
# def coalpw():
#     def collect_iterator(**kwargs):
#         yield from collectIEAData("TESbySource", "COALPW", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/COALPW", methods=["GET"])
@login_required
def compute_coalpw():
    """
    product_codes = {
        "COAL": "Coal",
        "NATGAS": "Natural gas",
        "NUCLEAR": "Nuclear",
        "HYDRO": "Hydro",
        "GEOTHERM": "Wind, solar, etc.",
        "COMRENEW": "Biofuels and waste",
        "MTOTOIL": "Oil"
    }
    """
    app.logger.info("Running /api/v1/compute/COALPW")
    sspi_clean_api_data.delete_many({"IndicatorCode": "COALPW"})
    raw_data = sspi_raw_api_data.fetch_raw_data("COALPW")
    metadata_code_map = {
        "COAL": "TLCOAL",
        "NATGAS": "NATGAS",
        "NUCLEAR": "NCLEAR",
        "HYDRO": "HYDROP",
        "GEOTHERM": "GEOPWR",
        "COMRENEW": "BIOWAS",
        "MTOTOIL": "FSLOIL",
    }
    intermediate_data = pd.DataFrame(cleanIEAData_altnrg(raw_data, "COALPW"))
    intermediate_data.drop(
        intermediate_data[
            intermediate_data["CountryCode"].map(lambda s: len(s) != 3)
        ].index.tolist(),
        inplace=True,
    )
    intermediate_data["IntermediateCode"] = intermediate_data["IntermediateCode"].map(
        lambda x: metadata_code_map[x]
    )
    intermediate_data.astype({"Year": "int", "Value": "float"})
    # adding sum of available intermediates as an intermediate, in order to complete data
    sums = (
        intermediate_data.groupby(["Year", "CountryCode"])
        .agg({"Value": "sum"})
        .reset_index()
    )
    sums["IntermediateCode"], sums["Unit"], sums["IndicatorCode"] = (
        "TTLSUM",
        "TJ",
        "COALPW",
    )
    intermediate_list = pd.concat([intermediate_data, sums])
    intermediate_document_list = json.loads(
        str(intermediate_list.to_json(orient="records")),
        parse_int=int,
        parse_float=float,
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_document_list,
        "COALPW",
        ScoreFunction=lambda TLCOAL, TTLSUM: (TLCOAL) / (TTLSUM),
        ScoreBy="Value",
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)
