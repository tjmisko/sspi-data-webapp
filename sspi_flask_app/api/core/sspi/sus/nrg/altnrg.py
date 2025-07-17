import json

import pandas as pd
from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import collect_bp, compute_bp, impute_bp
from sspi_flask_app.api.datasource.iea import cleanIEAData_altnrg, collectIEAData
from sspi_flask_app.api.resources.utilities import (
    extrapolate_forward,
    parse_json,
    zip_intermediates,
    slice_intermediate
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_incomplete_api_data,
    sspi_raw_api_data,
)


# @collect_bp.route("/ALTNRG", methods=["GET"])
# @login_required
# def altnrg():
#     def collect_iterator(**kwargs):
#         yield from collectIEAData("TESbySource", "ALTNRG", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


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
    sspi_incomplete_api_data.delete_many({"IndicatorCode": "ALTNRG"})
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


@impute_bp.route("/ALTNRG", methods=["POST"])
@login_required
def impute_altnrg():
    """
    Imputation for alternative energy sources is not implemented yet.
    """
    app.logger.info("Running /api/v1/impute/ALTNRG")
    sspi_imputed_data.delete_many({"IndicatorCode": "ALTNRG"})
    # Forward Extrapolate from 2022 to 2023
    clean_data = sspi_clean_api_data.find({"IndicatorCode": "ALTNRG", "CountryCode": {"$ne": "KWT"}})
    forward_extrap = extrapolate_forward(clean_data, 2023, impute_only=True)
    # Handle KWT: All sources confirm that almost all energy is from fossil fuels
    kwt_incomplete = sspi_incomplete_api_data.find(
        {"IndicatorCode": "ALTNRG", "CountryCode": "KWT"}
    )
    impute_info = {
        "Imputed": True,
        "ImputationMethod": "ManualSourcing",
        "ImputationDescription": (
            "Kuwait's energy supply is almost entirely from fossil "
                "fuels, with negligible contributions from renewable "
                "sources, which includes Biowaste sources. Most of the "
                "available sources are from recent years, but given KWT's "
                "long-standing status as a major oil producer, it is "
                "reasonable to assume that this pattern has been consistent"
                " for many years."
        ),
        "ImputationSources": [
            {
                "URL": "https://www.iea.org/countries/kuwait/energy-mix",
                "Evidence": "Oil and natural gas account for >99% of Kuwait's Total Energy Supply in 2022. See figure ' Largest source of energy in Kuwait, 2022.'",
            },
            {
                "URL": "https://www.eia.gov/international/content/analysis/countries_long/Kuwait/kuwait.pdf",
                "Evidence": "Primary energy consumption by fuel is >99% petroleum/other liquids and natural gas in 2021.",
            },
            {
                "URL": "https://www.irena.org/-/media/Files/IRENA/Agency/Statistics/Statistical_Profiles/Middle%20East/Kuwait_Middle%20East_RE_SP.pdf",
                "Evidence": "Renewable energy supply is only 8715 TJ out of 517,966 TJ of TES in 2021, and only 619 TJ in 2016.",
            },
        ]
    }
    for i, obs in enumerate(kwt_incomplete):
        obs["Imputed"] = True
        obs["ImputationMethod"] = True
        obs["ImputationDistance"] = 0
        year = obs["Year"]
        country_code = obs["CountryCode"]
        int_codes = [inter["IntermediateCode"] for inter in obs["Intermediates"]]
        if "BIOWAS" not in int_codes:
            imputed_intermediate = {
                "IntermediateCode": "BIOWAS",
                "Value": 0.0,
                "Unit": "TJ",
                "Year": year,
                "CountryCode": country_code
            }
            imputed_intermediate.update(impute_info)
            obs["Intermediates"].append(imputed_intermediate)
        if "ALTSUM" not in int_codes:
            imputed_intermediate = {
                "IntermediateCode": "ALTSUM",
                "Value": 0.0,
                "Unit": "TJ",
                "Year": year,
                "CountryCode": country_code
            }
            imputed_intermediate.update(impute_info)
            obs["Intermediates"].append(imputed_intermediate)
    kwt_clean, kwt_still_missing = zip_intermediates(
        slice_intermediate(kwt_incomplete, ["TTLSUM", "ALTSUM", "BIOWAS"]),
        "ALTNRG", 
        ScoreFunction=lambda TTLSUM, ALTSUM, BIOWAS: (ALTSUM - 0.5 * BIOWAS) / TTLSUM,
        ValueFunction=lambda TTLSUM, ALTSUM, BIOWAS: (ALTSUM - 0.5 * BIOWAS) / TTLSUM * 100,
        ScoreBy="Value",
    )
    imputations = extrapolate_forward(kwt_clean, 2023) + forward_extrap
    sspi_imputed_data.insert_many(imputations)
    return parse_json(imputations)
