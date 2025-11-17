from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_incomplete_indicator_data)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_reference_class_average,
    filter_imputations
)


@compute_bp.route("/RDFUND", methods=['POST'])
@admin_required
def compute_rdfund():
    def score_rdfund(UNSDG_RDPGDP, UNSDG_NRSRCH):
        unsdg_edurdp_score = goalpost(UNSDG_RDPGDP, 0, 4)
        unsdg_nrsrch_score = goalpost(UNSDG_NRSRCH, 0, 5000)
        return (unsdg_edurdp_score + unsdg_nrsrch_score) / 2

    sspi_indicator_data.delete_many({"IndicatorCode": "RDFUND"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "RDFUND"})
    rdfund_clean = sspi_clean_api_data.find({"DatasetCode": {"$in": ["UNSDG_RDPGDP", "UNSDG_NRSRCH"]}})
    clean_list, incomplete_list = score_indicator(
        rdfund_clean, "RDFUND",
        score_function=score_rdfund,
        unit="Index"
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)

@impute_bp.route("/RDFUND", methods=['POST'])
@admin_required
def impute_rdfund():
    def score_rdfund(UNSDG_RDPGDP, UNSDG_NRSRCH):
        unsdg_edurdp_score = goalpost(UNSDG_RDPGDP, 0, 4)
        unsdg_nrsrch_score = goalpost(UNSDG_NRSRCH, 0, 5000)
        return (unsdg_edurdp_score + unsdg_nrsrch_score) / 2
    sspi_imputed_data.delete_many({"IndicatorCode": "RDFUND"})
    unsdg_rdpgdp = sspi_clean_api_data.find({"DatasetCode": "UNSDG_RDPGDP"})
    rdpgdp_forward = extrapolate_forward(unsdg_rdpgdp, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    rdpgdp_backward = extrapolate_backward(unsdg_rdpgdp, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    rdpgdp_interpolated = interpolate_linear(unsdg_rdpgdp, ["CountryCode", "DatasetCode"], impute_only=True)
    rdpgdp_ref_average_bgd = impute_reference_class_average(
        "BGD", 2000, 2023, "Dataset", "UNSDG_RDPGDP", unsdg_rdpgdp
    )
    unsdg_nrsrch = sspi_clean_api_data.find({"DatasetCode": "UNSDG_NRSRCH"})
    nrsrch_forward = extrapolate_forward(unsdg_nrsrch, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    nrsrch_backward = extrapolate_backward(unsdg_nrsrch, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    nrsrch_interpolated = interpolate_linear(unsdg_nrsrch, ["CountryCode", "DatasetCode"], impute_only=True)
    nrsrch_ref_average_per = impute_reference_class_average(
        "PER", 2000, 2023, "Dataset", "UNSDG_NRSRCH", unsdg_nrsrch
    )
    nrsrch_ref_average_bgd = impute_reference_class_average(
        "BGD", 2000, 2023, "Dataset", "UNSDG_NRSRCH", unsdg_nrsrch
    )
    nrsrch_ref_average_isr = impute_reference_class_average(
        "ISR", 2000, 2023, "Dataset", "UNSDG_NRSRCH", unsdg_nrsrch
    )
    combined_list = unsdg_rdpgdp + rdpgdp_forward + rdpgdp_backward + rdpgdp_interpolated + \
                    unsdg_nrsrch + nrsrch_forward + nrsrch_backward + nrsrch_interpolated + \
                    nrsrch_ref_average_per + nrsrch_ref_average_bgd + nrsrch_ref_average_isr + \
                    rdpgdp_ref_average_bgd
    clean_list, _ = score_indicator(
        combined_list, "RDFUND",
        score_function=score_rdfund,
        unit="Index"
    )
    imputed_rdfund = filter_imputations(clean_list)
    sspi_imputed_data.insert_many(imputed_rdfund)
    return parse_json(imputed_rdfund)


# @compute_bp.route("/MILEXP", methods=['GET'])
# def compute_milexp():
#     app.logger.info("Running /api/v1/compute/MILEXP")
#     sspi_clean_api_data.delete_many({"IndicatorCode": "MILEXP"})
#     milexp_raw = sspi_raw_api_data.fetch_raw_data("MILEXP")
#     cleaned_list = cleanSIPRIData(milexp_raw, 'MILEXP')
#     obs_list = json.loads(cleaned_list.to_json(orient="records"))
#     scored_list = score_single_indicator(obs_list, "MILEXP")
#     sspi_clean_api_data.insert_many(scored_list)
#     return parse_json(scored_list)


# @compute_bp.route("/ARMEXP", methods=['GET'])
# def compute_armexp():
#     app.logger.info("Running /api/v1/compute/ARMEXP")
#     sspi_clean_api_data.delete_many({"IndicatorCode": "ARMEXP"})
#     # armexp_raw = sspi_raw_api_data.fetch_raw_data("ARMEXP")
#     description = (
#         "The supply of military weapons through sales, aid, gifts, and those "
#         "made through manufacturing licenses."
#     )
#     cleaned_list = cleanSIPRIData(
#         'local/armexp.csv',
#         'ARMEXP',
#         'Millions of arms',
#         description
#     ) 
#     obs_list = json.loads(cleaned_list.to_json(orient="records"))
#     scored_list = score_single_indicator(obs_list, "ARMEXP")
#     sspi_clean_api_data.insert_many(scored_list)
#     return parse_json(scored_list)


# @compute_bp.route("/RDFUND", methods=['GET'])
# @admin_required
# def compute_rdfund():
#     """
#     metadata_map = {
#         "GB_XPD_RSDV": "GVTRDP",
#         "GB_POP_SCIERD": "NRSRCH"
#     }
#     """
#     app.logger.info("Running /api/v1/compute/RDFUND")
#     sspi_clean_api_data.delete_many({"IndicatorCode": "RDFUND"})
#     raw_data = sspi_raw_api_data.fetch_raw_data("RDFUND")
#     watman_data = extract_sdg(raw_data)
#     intermediate_map = {
#         "GB_XPD_RSDV": "GVTRDP",
#         "GB_POP_SCIERD": "NRSRCH"
#     }
#     intermediate_list = filter_sdg(
#         watman_data, intermediate_map, activity="TOTAL"
#     )
#     clean_list, incomplete_list = zip_intermediates(
#         intermediate_list, "RDFUND",
#         ScoreFunction=lambda GVTRDP, NRSRCH: (GVTRDP + NRSRCH) / 2,
#         ScoreBy="Score"
#     )
#     sspi_clean_api_data.insert_many(clean_list)
#     print(incomplete_list)
#     return parse_json(clean_list)
