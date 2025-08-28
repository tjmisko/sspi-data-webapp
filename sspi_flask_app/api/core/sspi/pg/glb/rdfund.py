from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
)


# @collect_bp.route("/RDFUND", methods=['POST'])
# @login_required
# def rdfund():
#     def collect_iterator(**kwargs):
#         yield from collect_sdg_indicator_data("9.5.1", "RDFUND", **kwargs)
#         yield from collect_sdg_indicator_data("9.5.2", "RDFUND", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/RDFUND", methods=['POST'])
@login_required
def compute_rdfund():
    """
    metadata_map = {
        "GB_XPD_RSDV": "GVTRDP",
        "GB_POP_SCIERD": "NRSRCH"
    }
    """
    app.logger.info("Running /api/v1/compute/RDFUND")
    sspi_indicator_data.delete_many({"IndicatorCode": "RDFUND"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "RDFUND"})
    rdfund_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_RDFUND"})
    clean_list, incomplete_list = score_indicator(
        rdfund_clean, "RDFUND",
        score_function=lambda GVTRDP, NRSRCH: (GVTRDP + NRSRCH) / 2,
        unit="Index"
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


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
# @login_required
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
