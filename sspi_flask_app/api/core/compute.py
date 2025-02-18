import os
import json
import jq
import bs4 as bs
import numpy as np
from bs4 import BeautifulSoup
from flask import (
    Blueprint,
    redirect,
    url_for,
    jsonify,
    Response,
    stream_with_context
)
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    # goalpost,
    # jsonify_df,
    zip_intermediates,
    # format_m49_as_string,
    filter_incomplete_data,
    score_single_indicator
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_raw_api_data,
    sspi_raw_outcome_data,
    sspi_clean_outcome_data,
    sspi_dynamic_line_data
    # sspi_analysis
)
from ..datasource.prisonstudies import (
    scrape_stored_pages_for_data, compute_prison_rate
    )

from ..datasource.sdg import (
    flatten_nested_dictionary_biodiv,
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_airpol,
    flatten_nested_dictionary_redlst,
    flatten_nested_dictionary_intrnt,
    flatten_nested_dictionary_watman,
    flatten_nested_dictionary_stkhlm,
    flatten_nested_dictionary_nrgint,
    flatten_nested_dictionary_fampln
)
# from ..datasource.worldbank import cleanedWorldBankData, cleaned_wb_current
from ..datasource.oecdstat import (
    # organizeOECDdata,
    # OECD_country_list,
    extractAllSeries,
    # filterSeriesList,
    filterSeriesListSeniors
)
from ..datasource.iea import (
    filterSeriesListiea,
    cleanIEAData_altnrg,
    clean_IEA_data_GTRANS,

)
from ..datasource.who import (
    cleanWHOdata
)
import pandas as pd
# from pycountry import countries
from io import StringIO
import re
# from ..datasource.ilo import cleanILOData
from sspi_flask_app.api.core.finalize import (
    finalize_iterator
)


compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates",
                       static_folder="static",
                       url_prefix="/compute")

################################################
# Compute Routes for Pillar: SUSTAINABILITY #
################################################

###########################
### Category: ECOSYSTEM ###
###########################


@compute_bp.route("/all", methods=['GET'])
@login_required
def compute_all():
    """
    """
    sspi_clean_api_data.delete_many({})

    def compute_iterator():
        yield "Cleared existing sspi_clean_api_data collection\n"
        with app.app_context():
            yield "Computing BIODIV\n"
            with app.app_context():
                compute_biodiv()
            yield "Computing REDLST\n"
            with app.app_context():
                compute_rdlst()
            yield "Computing NITROG\n"
            with app.app_context():
                compute_nitrog()
            # yield "Computing WATMAN"
            # compute_watman()
            yield "Computing STKHLM\n"
            with app.app_context():
                compute_stkhlm()
            yield "Computing INTRNT\n"
            with app.app_context():
                compute_intrnt()
            yield "Computing FDEPTH\n"
            with app.app_context():
                compute_fdepth()
            yield "Computing ALTNRG\n"
            with app.app_context():
                compute_altnrg()
            yield "Finalizing Production Data\n"
            yield from finalize_iterator()
            yield "Data is up to date\n"

    return Response(
        stream_with_context(compute_iterator()),
        mimetype='text/event-stream'
    )


@compute_bp.route("/BIODIV", methods=['GET'])
@login_required
def compute_biodiv():
    """
    If indicator is not in database, return a page with a button to collect the data
    - If no collection route is implemented, return a page with a message
    - If collection route is implemented, return a page with a button to collect the data
    If indicator is in database, compute the indicator from the raw data
    - Indicator computation: average of the three scores for percentage of biodiversity in
    marine, freshwater, and terrestrial ecosystems
    """
    if not sspi_raw_api_data.raw_data_available("BIODIV"):
        return redirect(url_for("api_bp.collect_bp.BIODIV"))
    raw_data = sspi_raw_api_data.fetch_raw_data("BIODIV")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(
        raw_data)
    # implement a computation function as an argument which can be adapted to different contexts
    final_data_list = flatten_nested_dictionary_biodiv(intermediate_obs_dict)
    # store the cleaned data in the database
    zipped_document_list = zip_intermediates(final_data_list, "BIODIV",
                                             ScoreFunction=lambda MARINE, TERRST, FRSHWT: 0.33 *
                                             MARINE + 0.33 * TERRST + 0.33 * FRSHWT,
                                             ScoreBy="Score")
    clean_observations, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    sspi_clean_api_data.insert_many(clean_observations)
    print(incomplete_observations)
    return parse_json(clean_observations)


@compute_bp.route("/REDLST", methods=['GET'])
@login_required
def compute_rdlst():
    if not sspi_raw_api_data.raw_data_available("REDLST"):
        return redirect(url_for("api_bp.collect_bp.REDLST"))
    raw_data = sspi_raw_api_data.fetch_raw_data("REDLST")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(
        raw_data)
    final_list = flatten_nested_dictionary_redlst(intermediate_obs_dict)
    meta_data_added = score_single_indicator(final_list, "REDLST")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        meta_data_added)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)

######################
### Category: LAND ###
#######################


@compute_bp.route("/NITROG", methods=['GET'])
@login_required
def compute_nitrog():
    if not sspi_raw_api_data.raw_data_available("NITROG"):
        return redirect(url_for("collect_bp.NITROG"))
    raw_data = sspi_raw_api_data.fetch_raw_data("NITROG")
    csv_virtual_file = StringIO(raw_data[0]["Raw"]["csv"])
    SNM_raw = pd.read_csv(csv_virtual_file)
    SNM_raw = SNM_raw.drop(columns=['code', 'country'])
    SNM_raw = SNM_raw.rename(columns={'iso': 'CountryCode'})
    SNM_long = SNM_raw.melt(
        id_vars=['CountryCode'],
        var_name='YearString',
        value_name='Value'
    )
    SNM_long["Year"] = [
        re.search(r"\d{4}", s).group(0)
        for s in SNM_long["YearString"]
    ]
    SNM_long.drop(columns=['YearString'], inplace=True)
    SNM_long.drop(SNM_long[SNM_long['Value'] < 0].index, inplace=True)
    SNM_long.drop(SNM_long[SNM_long['Value'].isna()].index, inplace=True)
    SNM_long['IndicatorCode'] = 'NITROG'
    SNM_long['Unit'] = 'Index'
    obs_list = json.loads(SNM_long.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "NITROG")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/WATMAN", methods=['GET'])
@login_required
def compute_watman():
    """
    metadata_map = {
        "ER_H2O_WUEYST": "CWUEFF",
        "ER_H2O_STRESS": "WTSTRS"
    }
    """
    if not sspi_raw_api_data.raw_data_available("WATMAN"):
        return redirect(url_for("collect_bp.WATMAN"))
    raw_data = sspi_raw_api_data.fetch_raw_data("WATMAN")
    total_list = [obs for obs in raw_data if obs["Raw"]["activity"] == "TOTAL"]
    intermediate_list = extract_sdg_pivot_data_to_nested_dictionary(total_list)
    final_list = flatten_nested_dictionary_watman(intermediate_list)
    zipped_document_list = zip_intermediates(final_list, "WATMAN",
                                             ScoreFunction=lambda CWUEFF, WTSTRS: 0.50 * CWUEFF + 0.50 * WTSTRS,
                                             ScoreBy="Score")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)


@compute_bp.route("/STKHLM", methods=['GET'])
@login_required
def compute_stkhlm():
    if not sspi_raw_api_data.raw_data_available("STKHLM"):
        return redirect(url_for("api_bp.collect_bp.STKHLM"))
    raw_data = sspi_raw_api_data.fetch_raw_data("STKHLM")
    full_stk_list = [obs for obs in raw_data if obs["Raw"]
                     ["series"] == "SG_HAZ_CMRSTHOLM"]
    intermediate_list = extract_sdg_pivot_data_to_nested_dictionary(
        full_stk_list)
    flattened_lst = flatten_nested_dictionary_stkhlm(intermediate_list)
    scored_list = score_single_indicator(flattened_lst, "STKHLM")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)

########################
### Category: ENERGY ###
########################

@compute_bp.route("/NRGINT")
@login_required
def compute_nrgint():
    if not sspi_raw_api_data.raw_data_available("NRGINT"):
        return redirect(url_for("api_bp.collect_bp.NRGINT"))
    raw_data = sspi_raw_api_data.fetch_raw_data("NRGINT")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    computed = flatten_nested_dictionary_nrgint(intermediate_obs_dict)
    scored_list = score_single_indicator(computed, "NRGINT")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)

@compute_bp.route("/COALPW", methods=['GET'])
@login_required
def compute_coalpw():
    if not sspi_raw_api_data.raw_data_available("COALPW"):
        return redirect(url_for("api_bp.collect_bp.COALPW"))
    raw_data = sspi_raw_api_data.fetch_raw_data("COALPW")

    product_codes = {
        "COAL": "Coal",
        "NATGAS": "Natural gas",
        "NUCLEAR": "Nuclear",
        "HYDRO": "Hydro",
        "GEOTHERM": "Wind, solar, etc.",
        "COMRENEW": "Biofuels and waste",
        "MTOTOIL": "Oil"
    }

    metadata_code_map = {
        "COAL": "TLCOAL",
        "NATGAS": "NATGAS",
        "NUCLEAR": "NCLEAR",
        "HYDRO": "HYDROP",
        "GEOTHERM": "GEOPWR",
        "COMRENEW": "BIOWAS",
        "MTOTOIL": "FSLOIL"
    }

    intermediate_data = pd.DataFrame(cleanIEAData_altnrg(raw_data, "COALPW"))
    intermediate_data.drop(intermediate_data[intermediate_data["CountryCode"].map(
        lambda s: len(s) != 3)].index, inplace=True)
    intermediate_data["IntermediateCode"] = intermediate_data["IntermediateCode"].map(
        lambda x: metadata_code_map[x])
    intermediate_data.astype({"Year": "int", "Value": "float"})
    # adding sum of available intermediates as an intermediate, in order to complete data
    sums = intermediate_data.groupby(['Year', 'CountryCode']).agg({
        'Value': 'sum'}).reset_index()
    sums['IntermediateCode'], sums['Unit'], sums['IndicatorCode'] = 'TTLSUM', 'TJ', 'COALPW'

    intermediate_list = pd.concat([intermediate_data, sums])
    zipped_document_list = zip_intermediates(
        json.loads(str(intermediate_list.to_json(orient="records")),
                   parse_int=int, parse_float=float),
        "COALPW",
        ScoreFunction=lambda TLCOAL, TTLSUM: (TLCOAL)/(TTLSUM),
        ScoreBy="Values"
    )

    clean_document_list, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)

@compute_bp.route("/AIRPOL")
@login_required
def compute_airpol():
    if not sspi_raw_api_data.raw_data_available("AIRPOL"):
        return redirect(url_for("api_bp.collect_bp.AIRPOL"))
    raw_data = sspi_raw_api_data.fetch_raw_data("AIRPOL")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    flattened = flatten_nested_dictionary_airpol(intermediate_obs_dict)
    scored_list = score_single_indicator(flattened, "AIRPOL")
    cleaned, filtered = filter_incomplete_data(scored_list)
    sspi_clean_api_data.insert_many(cleaned)
    print(filtered)
    return parse_json(cleaned)

@compute_bp.route("/NRGINT", methods=['GET'])
# @login_required
def compute_nrgint():
    if not sspi_raw_api_data.raw_data_available("NRGINT"):
        return redirect(url_for("collect_bp.NRGINT"))
    nrgint_raw = sspi_raw_api_data.fetch_raw_data("NRGINT")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(
        nrgint_raw)
    flattened_lst = flatten_nested_dictionary_nrgint(intermediate_obs_dict)
    scored_list = score_single_indicator(flattened_lst, "NRGINT")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)


@compute_bp.route("/ALTNRG", methods=['GET'])
@login_required
def compute_altnrg():
    if not sspi_raw_api_data.raw_data_available("ALTNRG"):
        return redirect(url_for("collect_bp.ALTNRG"))
    raw_data = sspi_raw_api_data.fetch_raw_data("ALTNRG")

    # most of these intermediates used to compute sum
    product_codes = {
        "COAL": "Coal",
        "NATGAS": "Natural gas",
        "NUCLEAR": "Nuclear",
        "HYDRO": "Hydro",
        "GEOTHERM": "Wind, solar, etc.",
        "COMRENEW": "Biofuels and waste",
        "MTOTOIL": "Oil"
    }

    metadata_code_map = {
        "COAL": "TLCOAL",
        "NATGAS": "NATGAS",
        "NUCLEAR": "NCLEAR",
        "HYDRO": "HYDROP",
        "GEOTHERM": "GEOPWR",
        "COMRENEW": "BIOWAS",
        "MTOTOIL": "FSLOIL"
    }

    intermediate_data = pd.DataFrame(cleanIEAData_altnrg(raw_data, "ALTNRG"))
    intermediate_data.drop(intermediate_data[intermediate_data["CountryCode"].map(
        lambda s: len(s) != 3)].index, inplace=True)
    intermediate_data["IntermediateCode"] = intermediate_data["IntermediateCode"].map(
        lambda x: metadata_code_map[x])
    intermediate_data.astype({"Year": "int", "Value": "float"})
    # adding sum of available intermediates as an intermediate, in order to complete data
    sums = intermediate_data.groupby(['Year', 'CountryCode']).agg({
        'Value': 'sum'}).reset_index()
    sums['IntermediateCode'], sums['Unit'], sums['IndicatorCode'] = 'TTLSUM', 'TJ', 'ALTNRG'

    # running the samce operations for alternative energy sources
    inter_sums = intermediate_data[intermediate_data["IntermediateCode"].isin(
        ["HYDROP", "NCLEAR", "GEOPWR", "BIOWAS"])]
    alt_sums = inter_sums.groupby(['Year', 'CountryCode']).agg({
        'Value': 'sum'}).reset_index()
    alt_sums['IntermediateCode'], alt_sums['Unit'], alt_sums['IndicatorCode'] = 'ALTSUM', 'TJ', 'ALTNRG'

    intermediate_list = pd.concat(
        [pd.concat([intermediate_data, sums]), alt_sums])
    zipped_document_list = zip_intermediates(
        json.loads(str(intermediate_list.to_json(orient="records")),
                   parse_int=int, parse_float=float),
        "ALTNRG",
        ScoreFunction=lambda TTLSUM, ALTSUM, BIOWAS: (
            ALTSUM - 0.5 * BIOWAS)/(TTLSUM),
        ScoreBy="Values"
    )
    clean_document_list, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    print(incomplete_observations)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)


##################################
### Category: GREENHOUSE GASES ###
##################################



##################################
### Category: WORKER WELLBEING ###
##################################

@compute_bp.route("/SENIOR", methods=['GET'])
@login_required
def compute_senior():
    if not sspi_raw_api_data.raw_data_available("SENIOR"):
        return redirect(url_for("collect_bp.SENIOR"))
    raw_data = sspi_raw_api_data.fetch_raw_data("SENIOR")
    # metadata = raw_data[0]["Metadata"]
    # metadata_soup = bs.BeautifulSoup(metadata, "lxml")
    # to see the codes and their descriptions, uncomment and return the following line
    # jsonify([[tag.get("value"), tag.get_text()] for tag in metadata_soup.find_all("code")])
    metadata_codes = {
        "PEN20A": "Expected years in retirement, men",
        "PEN20B": "Expected years in retirement, women",
        "PEN24A": "Old age income poverty, 66+",
    }
    metadata_code_map = {
        "PEN20A": "YRSRTM",
        "PEN20B": "YRSRTW",
        "PEN24A": "POVNRT",
    }
    series = extractAllSeries(raw_data[0]["Raw"])
    document_list = []
    for code in metadata_codes.keys():
        document_list.extend(filterSeriesListSeniors(
            series, code, "PAG", "SENIOR"))
    long_senior_data = pd.DataFrame(document_list)
    long_senior_data.drop(long_senior_data[long_senior_data["CountryCode"].map(
        lambda s: len(s) != 3)].index, inplace=True)
    long_senior_data["IntermediateCode"] = long_senior_data["VariableCodeOECD"].map(
        lambda x: metadata_code_map[x])
    long_senior_data.astype({"Year": "int", "Value": "float"})
    zipped_document_list = zip_intermediates(
        json.loads(str(long_senior_data.to_json(orient="records")),
                   parse_int=int, parse_float=float),
        "SENIOR",
        ScoreFunction=lambda YRSRTM, YRSRTW, POVNRT: 0.25 *
        YRSRTM + 0.25*YRSRTW + 0.50*POVNRT,
        ScoreBy="Score"
    )
    clean_document_list, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)

#################################
## Category: WORKER ENGAGEMENT ##
#################################

@compute_bp.route("/LFPART", methods=['GET'])
@login_required
def compute_lfpart():
    if not sspi_raw_api_data.fetch_raw_data("LFPART"):
        return redirect(url_for("collect_bp.LFPART"))
    raw_data = sspi_raw_api_data.fetch_raw_data("LFPART")
    series_list = extractAllSeriesILO(raw_data[0]["Raw"])
    document_list = filterSeriesListlfpart(series_list)
    long_lfpart_data = pd.DataFrame(document_list)
    long_lfpart_data.drop(long_lfpart_data[long_lfpart_data["CountryCode"].map(lambda s: len(s) != 3)].index, inplace=True)
    long_lfpart_data.astype({"Year": "int", "Value": "float"})
    scored_document_list = score_single_indicator(json.loads(str(long_lfpart_data.to_json(orient="records")), parse_int=int, parse_float=float), 
                                                  IndicatorCode="LFPART")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored_document_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)
    # print(raw_data_soup.find_all('generic:series'))
    # return None


@compute_bp.route("/FDEPTH", methods=['GET'])
@login_required
def compute_fdepth():
    if not sspi_raw_api_data.raw_data_available("FDEPTH"):
        return redirect(url_for("collect_bp.FDEPTH"))
    credit_raw = sspi_raw_api_data.fetch_raw_data("FDEPTH", IntermediateCode = "CREDIT")
    credit_clean = cleaned_wb_current(credit_raw, "FDEPTH", unit = "Percent")
    deposit_raw = sspi_raw_api_data.fetch_raw_data("FDEPTH", IntermediateCode = "DPOSIT")
    deposit_clean = cleaned_wb_current(deposit_raw, "FDEPTH", unit = "Percent")
    combined_list = credit_clean + deposit_clean
    cleaned_list = zip_intermediates(combined_list, "FDEPTH",
                                     ScoreFunction= lambda CREDIT, DPOSIT: 0.5 * CREDIT + 0.5 * DPOSIT,
                                     ScoreBy= "Score")
    filtered_list, incomplete_data = filter_incomplete_data(cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


###########################################
# Compute Routes for Pillar: PUBLIC GOODS #
###########################################
@compute_bp.route("/ATBRTH")
@login_required
def compute_atbrth():
    if not sspi_raw_api_data.raw_data_available("ATBRTH"):
        return redirect(url_for("api_bp.collect_bp.ATBRTH"))
    raw_data = sspi_raw_api_data.fetch_raw_data("ATBRTH")
    cleaned = cleanWHOdata(raw_data, "ATBRTH", "Percent",
                           "The proportion of births attended by trained and/or skilled health personnel")
    scored = score_single_indicator(cleaned, "ATBRTH")
    filtered_list, incomplete_data = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/DPTCOV")
@login_required
def compute_dptcov():
    if not sspi_raw_api_data.raw_data_available("DPTCOV"):
        return redirect(url_for("api_bp.collect_bp.DPTCOV"))
    raw_data = sspi_raw_api_data.fetch_raw_data("DPTCOV")
    cleaned = cleanWHOdata(raw_data, "DPTCOV", "Percent",
                           "DTP3 immunization coverage among one-year-olds (%)")
    scored = score_single_indicator(cleaned, "DPTCOV")
    filtered_list, incomplete_data = filter_incomplete_data(scored)
    # sspi_clean_api_data.insert_many(filtered_list)
    # print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/PHYSPC")
@login_required
def compute_physpc():
    if not sspi_raw_api_data.raw_data_available("PHYSPC"):
        return redirect(url_for("api_bp.collect_bp.PHYSPC"))
    raw_data = sspi_raw_api_data.fetch_raw_data("PHYSPC")
    cleaned = cleanWHOdata(raw_data, "PHYSPC", "Doctors/10000",
                           "Number of medical doctors (physicians), both generalists and specialists, expressed per 10,000 people.")
    scored = score_single_indicator(cleaned, "PHYSPC")
    filtered_list, incomplete_data = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/FAMPLN")
@login_required
def compute_fampln():
    if not sspi_raw_api_data.raw_data_available("FAMPLN"):
        return redirect(url_for("api_bp.collect_bp.FAMPLN"))
    raw_data = sspi_raw_api_data.fetch_raw_data("FAMPLN")
    inter = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    final = flatten_nested_dictionary_fampln(inter)
    computed_list = score_single_indicator(final, "FAMPLN")
    filtered_list, incomplete_data = filter_incomplete_data(computed_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(len(incomplete_data))
    return parse_json(filtered_list)

##################################
### Category: PUBLIC SAFETY ###
##################################

@compute_bp.route("/PRISON", methods=['GET'])
@login_required
def compute_prison():
    clean_data_list, missing_data_list = scrape_stored_pages_for_data()
    final_list, incomplete_observations = compute_prison_rate(clean_data_list)
    # print(f"Missing from World Prison Brief: {missing_data_list}")
    # print(f"Missing from UN population: {incomplete_observations}")
    return final_list

@compute_bp.route("/DRKWAT")
@login_required
def compute_drkwat():
    if not sspi_raw_api_data.raw_data_available("DRKWAT"):
        return redirect(url_for("api_bp.collect_bp.DRKWAT"))
    raw_data = sspi_raw_api_data.fetch_raw_data("DRKWAT")
    cleaned = cleaned_wb_current(raw_data, "DRKWAT", "Percent")
    scored = score_single_indicator(cleaned, "DRKWAT")
    filtered_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)

@compute_bp.route("/SANSRV")
@login_required
def compute_sansrv():
    if not sspi_raw_api_data.raw_data_available("SANSRV"):
        return redirect(url_for("api_bp.collect_bp.SANSRV"))
    raw_data = sspi_raw_api_data.fetch_raw_data("SANSRV")
    cleaned = cleaned_wb_current(raw_data, "SANSRV", "Percent")
    scored = score_single_indicator(cleaned, "SANSRV")
    filtered_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)

##################################
### Category: INFRASTRUCTURE ###
##################################

@compute_bp.route("/INTRNT", methods=['GET'])
@login_required
def compute_intrnt():
    if not sspi_raw_api_data.raw_data_available("INTRNT"):
        return redirect(url_for("collect_bp.INTRNT"))
    # worldbank #
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="AVINTR")
    wb_clean = cleaned_wb_current(wb_raw, "INTRNT", unit="Percent")
    # sdg #
    sdg_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="QLMBPS")
    sdg_clean = extract_sdg_pivot_data_to_nested_dictionary(sdg_raw)
    sdg_clean = flatten_nested_dictionary_intrnt(sdg_clean)
    combined_list = wb_clean + sdg_clean
    cleaned_list = zip_intermediates(combined_list, "INTRNT",
                                     ScoreFunction=lambda AVINTR, QUINTR: 0.5 * AVINTR + 0.5 * QUINTR,
                                     ScoreBy="Score")
    filtered_list, incomplete_observations = filter_incomplete_data(
        cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)


@compute_bp.route("/FDEPTH", methods=['GET'])
@login_required
def compute_fdepth():
    if not sspi_raw_api_data.raw_data_available("FDEPTH"):
        return redirect(url_for("collect_bp.FDEPTH"))
    credit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="CREDIT")
    credit_clean = cleaned_wb_current(credit_raw, "FDEPTH", unit="Percent")
    deposit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="DPOSIT")
    deposit_clean = cleaned_wb_current(deposit_raw, "FDEPTH", unit="Percent")
    combined_list = credit_clean + deposit_clean
    cleaned_list = zip_intermediates(combined_list, "FDEPTH",
                                     ScoreFunction=lambda CREDIT, DPOSIT: 0.5 * CREDIT + 0.5 * DPOSIT,
                                     ScoreBy="Score")
    filtered_list, incomplete_data = filter_incomplete_data(cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/COLBAR", methods=['GET'])
@login_required
def compute_colbar():
    if not sspi_raw_api_data.raw_data_available("COLBAR"):
        return redirect(url_for("collect_bp.COLBAR"))
    raw_data = sspi_raw_api_data.fetch_raw_data("COLBAR")
    csv_virtual_file = StringIO(raw_data[0]["Raw"]["csv"])
    colbar_raw = pd.read_csv(csv_virtual_file)
    colbar_raw = colbar_raw[['REF_AREA',
                             'TIME_PERIOD', 'UNIT_MEASURE', 'OBS_VALUE']]
    colbar_raw = colbar_raw.rename(columns={'REF_AREA': 'CountryCode',
                                            'TIME_PERIOD': 'Year',
                                            'OBS_VALUE': 'Value',
                                            'UNIT_MEASURE': 'Unit'})
    colbar_raw['IndicatorCode'] = 'COLBAR'
    colbar_raw['Unit'] = 'Proportion'
    colbar_raw['Value'] = colbar_raw['Value']
    obs_list = json.loads(colbar_raw.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "COLBAR")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


##################################
### Category: WORKER WELLBEING ###
##################################
@compute_bp.route("/FATINJ", methods=['GET'])
@login_required
def compute_fatinj():
    if not sspi_raw_api_data.raw_data_available("FATINJ"):
        return redirect(url_for("collect_bp.FATINJ"))
    raw_data = sspi_raw_api_data.fetch_raw_data("FATINJ")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    fatinj_raw = pd.read_csv(csv_virtual_file)
    fatinj_raw = fatinj_raw[fatinj_raw["SEX"] == "SEX_T"]
    fatinj_raw = fatinj_raw[['REF_AREA',
                             'TIME_PERIOD',
                             'UNIT_MEASURE',
                             'OBS_VALUE']]
    fatinj_raw = fatinj_raw.rename(columns={'REF_AREA': 'CountryCode',
                                            'TIME_PERIOD': 'Year',
                                            'OBS_VALUE': 'Value',
                                            'UNIT_MEASURE': 'Unit'})
    fatinj_raw['IndicatorCode'] = 'FATINJ'
    fatinj_raw['Unit'] = 'Rate per 100,000'
    fatinj_raw.dropna(subset=['Value'], inplace=True)
    obs_list = json.loads(str(fatinj_raw.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "FATINJ")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


##################################
### Category: Worker Wellbeing ###
##################################


@compute_bp.route("/UNEMPL", methods=['GET'])
@login_required
def compute_unempl():
    if not sspi_raw_api_data.raw_data_available("UNEMPL"):
        return redirect(url_for("collect_bp.UNEMPL"))
    raw_data = sspi_raw_api_data.fetch_raw_data("UNEMPL")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    colbar_raw = pd.read_csv(csv_virtual_file)
    colbar_raw_f = colbar_raw[colbar_raw['SOC'] == 'SOC_CONTIG_UNE']
    colbar_raw_f = colbar_raw_f[['REF_AREA', 'TIME_PERIOD', 'UNIT_MEASURE','OBS_VALUE']]
    colbar_raw_f = colbar_raw_f.rename(columns={'REF_AREA': 'CountryCode',
                                            'TIME_PERIOD': 'Year',
                                            'OBS_VALUE': 'Value',
                                            'UNIT_MEASURE': 'Unit'})
    colbar_raw_f['IndicatorCode'] = 'UNEMPL'
    colbar_raw_f['Unit'] = 'Rate'
    obs_list = json.loads(colbar_raw_f.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "UNEMPL")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)

############################
### Category: Healthcare ###
############################


@compute_bp.route("/CSTUNT", methods=['GET'])
@login_required
def compute_cstunt():
    raw_data = sspi_raw_api_data.fetch_raw_data("CSTUNT")[0]["Raw"]["fact"]
    # Slice out the relevant data and identifiers (in Dim array)
    first_slice = '.[] | {IndicatorCode: "CSTUNT", Value: .value.numeric, Dim }'
    first_slice_filter = jq.compile(first_slice)
    dim_list = first_slice_filter.input(raw_data).all()
    # Reduce/Flatten the Dim array
    map_reduce = '.[] |  reduce .Dim[] as $d (.; .[$d.category] = $d.code)'
    map_reduce_filter = jq.compile(map_reduce)
    reduced_list = map_reduce_filter.input(dim_list).all()
    # Remap the keys to the correct names
    rename_keys = '.[] | { IndicatorCode, CountryCode: .COUNTRY, Year: .YEAR, Value, Unit: "Percentage" }'
    rename_keys_filter = jq.compile(rename_keys)
    value_list = rename_keys_filter.input(reduced_list).all()
    # Score the indicator data
    scored_list = score_single_indicator(value_list, "CSTUNT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


##################################
###      Outcome Variables     ###
##################################


@compute_bp.route("/outcome/GDPMER", methods=['GET'])
@login_required
def compute_gdpmer():
    if not sspi_raw_outcome_data.raw_data_available("GDPMER"):
        return "No Data for GDPMER found in raw database! Try running collect."
    gdpmer_raw = sspi_raw_outcome_data.fetch_raw_data("GDPMER")
    extracted_data = []
    for obs in gdpmer_raw:
        value = obs["Raw"]["value"]
        if not value or value == "None" or value == "null":
            continue
        if not len(obs["Raw"]["countryiso3code"]) == 3:
            continue
        extracted_data.append({
            "CountryCode": obs["Raw"]["countryiso3code"],
            "IndicatorCode": "GDPMER",
            "Year": int(obs["Raw"]["date"]),
            "Value": float(obs["Raw"]["value"]),
            "Unit": obs["Raw"]["indicator"]["value"],
            "Score": float(obs["Raw"]["value"])
        })
    sspi_clean_outcome_data.insert_many(extracted_data)
    return parse_json(extracted_data)


@compute_bp.route("/outcome/GDPPPP", methods=['GET'])
@login_required
def compute_gdpppp():
    if not sspi_raw_outcome_data.raw_data_available("GDPPPP"):
        return "No Data for GDPPPP found in raw database! Try running collect."
    gdpppp_raw = sspi_raw_outcome_data.fetch_raw_data("GDPPPP")
    extracted_data = []
    for obs in gdpppp_raw:
        value = obs["Raw"]["value"]
        if not value or value == "None" or value == "null":
            continue
        if not len(obs["Raw"]["countryiso3code"]) == 3:
            continue
        extracted_data.append({
            "CountryCode": obs["Raw"]["countryiso3code"],
            "IndicatorCode": "GDPPPP",
            "Year": int(obs["Raw"]["date"]),
            "Value": float(obs["Raw"]["value"]),
            "Unit": obs["Raw"]["indicator"]["value"],
            "Score": float(obs["Raw"]["value"])
        })
    sspi_clean_outcome_data.insert_many(extracted_data)
    return parse_json(extracted_data)
