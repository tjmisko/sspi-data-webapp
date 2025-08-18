from flask import current_app as app
from flask_login import login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    extrapolate_forward,
    goalpost,
    parse_json,
    score_indicator,
    slice_dataset
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_incomplete_indicator_data,
    sspi_indicator_data,
    sspi_metadata
)


@compute_bp.route("/ALTNRG", methods=["POST"])
@login_required
def compute_altnrg():
    def score_altnrg(IEA_TLCOAL, IEA_NATGAS, IEA_NCLEAR, IEA_HYDROP, IEA_GEOPWR, IEA_BIOWAS, IEA_FSLOIL):
        lg, ug = sspi_metadata.get_goalposts("ALTNRG")
        return goalpost(
            ((IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS) - 0.5 * IEA_BIOWAS) / 
            (IEA_TLCOAL + IEA_NATGAS + IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS + IEA_FSLOIL) * 100, lg, ug)

    app.logger.info("Running /api/v1/compute/ALTNRG")
    sspi_indicator_data.delete_many({"IndicatorCode": "ALTNRG"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "ALTNRG"})
    
    # Fetch clean datasets - these already exist from the metadata
    dataset_codes = ["IEA_TLCOAL", "IEA_NATGAS", "IEA_NCLEAR", "IEA_HYDROP", "IEA_GEOPWR", "IEA_BIOWAS", "IEA_FSLOIL"]
    datasets_clean = sspi_clean_api_data.find({"DatasetCode": {"$in": dataset_codes}})
    
    clean_list, incomplete_list = score_indicator(
        datasets_clean,
        "ALTNRG",
        score_function=score_altnrg,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
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
    kwt_incomplete = sspi_incomplete_indicator_data.find(
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
    kwt_clean, kwt_still_missing = score_indicator(
        slice_dataset(kwt_incomplete, ["IEA_TTLSUM", "IEA_ALTSUM", "IEA_BIOWAS"]),
        "ALTNRG", 
        score_function=lambda TTLSUM, ALTSUM, BIOWAS: (ALTSUM - 0.5 * BIOWAS) / TTLSUM,
        unit="%",
    )
    imputations = extrapolate_forward(kwt_clean, 2023) + forward_extrap
    sspi_imputed_data.insert_many(imputations)
    return parse_json(imputations)
