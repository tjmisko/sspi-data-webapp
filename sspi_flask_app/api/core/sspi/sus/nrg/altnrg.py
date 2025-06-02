from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.api.datasource.iea import collectIEAData, cleanIEAData_altnrg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data,
)
from sspi_flask_app.api.resources.utilities import parse_json, zip_intermediates
import pandas as pd
import json


@collect_bp.route("/ALTNRG", methods=["GET"])
@login_required
def altnrg():
    def collect_iterator(**kwargs):
        yield from collectIEAData("TESbySource", "ALTNRG", **kwargs)

    return Response(
        collect_iterator(Username=current_user.username), mimetype="text/event-stream"
    )


@compute_bp.route("/ALTNRG", methods=["GET"])
@login_required
def compute_altnrg():
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
    app.logger.info("Running /api/v1/compute/ALTNRG")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ALTNRG"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ALTNRG")
    metadata_code_map = {
        "COAL": "TLCOAL",
        "NATGAS": "NATGAS",
        "NUCLEAR": "NCLEAR",
        "HYDRO": "HYDROP",
        "GEOTHERM": "GEOPWR",
        "COMRENEW": "BIOWAS",
        "MTOTOIL": "FSLOIL",
    }
    intermediate_data = pd.DataFrame(cleanIEAData_altnrg(raw_data, "ALTNRG"))
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
        "ALTNRG",
    )
    # running the samce operations for alternative energy sources
    inter_sums = intermediate_data[
        intermediate_data["IntermediateCode"].isin(
            ["HYDROP", "NCLEAR", "GEOPWR", "BIOWAS"]
        )
    ]
    alt_sums = (
        inter_sums.groupby(["Year", "CountryCode"]).agg({"Value": "sum"}).reset_index()
    )
    alt_sums["IntermediateCode"], alt_sums["Unit"], alt_sums["IndicatorCode"] = (
        "ALTSUM",
        "TJ",
        "ALTNRG",
    )
    intermediate_list = pd.concat([pd.concat([intermediate_data, sums]), alt_sums])
    intermediate_document_list = json.loads(
        str(intermediate_list.to_json(orient="records")),
        parse_int=int,
        parse_float=float,
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_document_list,
        "ALTNRG",
        ScoreFunction=lambda TTLSUM, ALTSUM, BIOWAS: (ALTSUM - 0.5 * BIOWAS) / TTLSUM,
        ValueFunction=lambda TTLSUM, ALTSUM, BIOWAS: (ALTSUM - 0.5 * BIOWAS)
        / TTLSUM
        * 100,
        ScoreBy="Value",
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)
