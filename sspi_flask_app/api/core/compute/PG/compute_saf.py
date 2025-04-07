from flask import redirect, url_for
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
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
    details = sspi_metadata.find(
        {"DocumentType": "IndicatorDetail", "Metadata.IndicatorCode": "PRISON"})[0]
    lower_goalpost = details["Metadata"]["LowerGoalpost"]
    upper_goalpost = details["Metadata"]["UpperGoalpost"]
    pop_data = sspi_raw_api_data.fetch_raw_data(
        "PRISON", IntermediateCode="UNPOPL")
    cleaned_pop = clean_wb_data(pop_data, "PRISON", "Population")
    clean_data_list, missing_data_list = scrape_stored_pages_for_data()
    combined_list = cleaned_pop + clean_data_list
    final_list = zip_intermediates(
        combined_list, "PRISON",
        ScoreFunction=lambda PRIPOP, UNPOPL: goalpost(
            PRIPOP / UNPOPL * 100000, lower_goalpost, upper_goalpost),
        ScoreBy="Values")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        final_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)


@compute_bp.route("/CYBSEC", methods=['GET'])
@login_required
def compute_cybsec():
    if not sspi_raw_api_data.raw_data_available("CYBSEC"):
        return redirect(url_for("collect_bp.CYBSEC"))
    cybsec_raw = sspi_raw_api_data.fetch_raw_data("CYBSEC")
    cleaned_list = cleanITUData_cybsec(cybsec_raw, 'CYBSEC')
    obs_list = json.loads(cleaned_list.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "CYBSEC")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/SECAPP")
@login_required
def compute_secapp():
    raw_data = sspi_raw_api_data.fetch_raw_data("SECAPP")
    description = (
        "The Security Apparatus is a component of the Fragile State Index, which",
        "considers the security threats to a state such as bombings, attacks/battle-",
        "related deaths, rebel movements, mutinies, coups, or terrorism. It is an",
        "index scored between 0 and 10."
    )
    cleaned_list = cleanFSIdata(
        raw_data, "SECAPP", "Index", description
    )
    scored = score_single_indicator(cleaned_list, "SECAPP")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)
