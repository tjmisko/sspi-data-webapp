from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    score_single_indicator,
    goalpost
)
from sspi_flask_app.api.datasource.itu import cleanITUData_cybsec
import json


from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)
from sspi_flask_app.api.datasource.prisonstudies import (
    scrape_stored_pages_for_data,
)
from sspi_flask_app.api.datasource.fsi import (
    cleanFSIdata
)


@compute_bp.route("/PRISON", methods=['GET'])
@login_required
def compute_prison():
    app.logger.info("Running /api/v1/compute/PRISON")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PRISON"})
    details = sspi_metadata.find(
        {"DocumentType": "IndicatorDetail", "Metadata.IndicatorCode": "PRISON"})[0]
    lg = details["Metadata"]["LowerGoalpost"]
    ug = details["Metadata"]["UpperGoalpost"]
    pop_data = sspi_raw_api_data.fetch_raw_data(
        "PRISON", IntermediateCode="UNPOPL")
    cleaned_pop = clean_wb_data(pop_data, "PRISON", "Population")
    clean_data_list, missing_data_list = scrape_stored_pages_for_data()
    combined_list = cleaned_pop + clean_data_list
    clean_list, incomplete_list = zip_intermediates(
        combined_list, "PRISON",
        ScoreFunction=lambda PRIPOP, UNPOPL: goalpost(
            PRIPOP / UNPOPL * 100000, lg, ug),
        ValueFunction=lambda PRIPOP, UNPOPL: PRIPOP / UNPOPL * 100000,
        UnitFunction=lambda PRIPOP, UNPOPL: "Prisoners Per 100,000",
        ScoreBy="Value")
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/CYBSEC", methods=['GET'])
@login_required
def compute_cybsec():
    app.logger.info("Running /api/v1/compute/CYBSEC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CYBSEC"})
    cybsec_raw = sspi_raw_api_data.fetch_raw_data("CYBSEC")
    cleaned_list = cleanITUData_cybsec(cybsec_raw, 'CYBSEC')
    obs_list = json.loads(cleaned_list.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "CYBSEC")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/SECAPP")
@login_required
def compute_secapp():
    app.logger.info("Running /api/v1/compute/SECAPP")
    sspi_clean_api_data.delete_many({"IndicatorCode": "SECAPP"})
    raw_data = sspi_raw_api_data.fetch_raw_data("SECAPP")
    description = (
        "The Security Apparatus is a component of the Fragile State Index, "
        "which considers the security threats to a state such as bombings, "
        "attacks/battle-related deaths, rebel movements, mutinies, coups, or "
        "terrorism. It is an index scored between 0 and 10."
    )
    cleaned_list = cleanFSIdata(
        raw_data, "SECAPP", "Index", description
    )
    scored_list = score_single_indicator(cleaned_list, "SECAPP")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
