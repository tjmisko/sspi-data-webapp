import json
import bs4 as bs
from bs4 import BeautifulSoup
from flask import Blueprint, redirect, url_for, jsonify
from flask_login import login_required
from ..resources.utilities import parse_json, goalpost
from ... import sspi_clean_api_data, sspi_raw_api_data, sspi_analysis
from ..datasource.sdg import flatten_nested_dictionary_biodiv, extract_sdg_pivot_data_to_nested_dictionary, flatten_nested_dictionary_redlst, flatten_nested_dictionary_intrnt
from ..datasource.worldbank import cleanedWorldBankData
from ..resources.adapters import raw_data_available, fetch_raw_data
from ..datasource.oecdstat import organizeOECDdata, OECD_country_list, extractAllSeries, filterSeriesList, filterSeriesListSeniors
import pandas as pd

compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/compute")

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
    if not raw_data_available("BIODIV"):
        return redirect(url_for("api_bp.collect_bp.BIODIV"))
    raw_data = fetch_raw_data("BIODIV")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    # implement a computation function as an argument which can be adapted to different contexts
    final_data_list = flatten_nested_dictionary_biodiv(intermediate_obs_dict)
    # store the cleaned data in the database
    sspi_clean_api_data.insert_many(final_data_list)
    return parse_json(final_data_list)

@compute_bp.route("/REDLST", methods = ['GET'])
@login_required
def compute_rdlst():
    if not raw_data_available("REDLST"):
        return redirect(url_for("api_bp.collect_bp.REDLST"))
    raw_data = fetch_raw_data("REDLST")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    final_list = flatten_nested_dictionary_redlst(intermediate_obs_dict)
    sspi_clean_api_data.insert_many(final_list)
    return parse_json(final_list)

@compute_bp.route("/COALPW")
@login_required
def compute_coalpw():
    if not raw_data_available("COALPW"):
        return redirect(url_for("api_bp.collect_bp.coalpw"))
    raw_data = fetch_raw_data("COALPW")
    observations = [entry["observation"] for entry in raw_data]
    observations = [entry["observation"] for entry in raw_data]
    df = pd.DataFrame(observations)
    return parse_json(df.head().to_json())

@compute_bp.route("/ALTNRG", methods=['GET'])
@login_required
def compute_altnrg():
    if not raw_data_available("ALTNRG"):
        return redirect(url_for("collect_bp.ALTNRG"))
    raw_data = fetch_raw_data("ALTNRG")
    observations = [entry["observation"] for entry in raw_data]
    df = pd.DataFrame(observations)
    print(df.head())
    df = df.pivot(columns="product", values="value", index=["year", "country", "short", "flow", "units"])
    print(df)
    return parse_json(df.head().to_json())
    # for row in raw_data:
        #lst.append(row["observation"])
    #return parse_json(lst)

@compute_bp.route("/GTRANS", methods = ['GET'])
@login_required
def compute_gtrans():
    if not raw_data_available("GTRANS"):
        return redirect(url_for("collect_bp.GTRANS"))
    
    #######    WORLDBANK compute    #########
    worldbank_raw = fetch_raw_data("GTRANS", IntermediateCode="TCO2EQ", Source="WorldBank")
    worldbank_clean_list = cleanedWorldBankData(worldbank_raw, "GTRANS")

    #######  IEA compute ######
    iea_raw_data = fetch_raw_data("GTRANS", IntermediateCode="TCO2EQ", Source="IEA")
    iea_clean_list = [entry["observation"] for entry in iea_raw_data]
   
    ### combining in pandas ####
    wb_df = pd.DataFrame(worldbank_clean_list)
    wb_df = wb_df[wb_df["RAW"].notna()].astype(str)
    iea_df = pd.DataFrame(iea_clean_list)
    iea_df = iea_df[iea_df['seriesLabel'] == "Transport"][['year', 'value', 'country']].rename(columns={'year':'YEAR', 'value':'RAW', 'country':'CountryCode'})
    # iea_df = iea_df[iea_df["RAW"].notna()].astype(str)
    
    merged = wb_df.drop(columns=["Source", "CountryName"]).merge(iea_df, how="outer", on=["CountryCode", "YEAR"]) 
    merged['RAW'] = (merged['RAW_x'].astype(float) + merged['RAW_y'].astype(float))/2
    df = merged.dropna()[['IndicatorCode', 'CountryCode', 'YEAR', 'RAW']]
    document_list = json.loads(str(df.to_json('records')))
    count = sspi_clean_api_data.insert_many(document_list)
    return f"Inserted {count} documents into SSPI Clean Database from OECD"
    
@compute_bp.route("/SENIOR", methods=['GET'])
@login_required
def compute_senior():
    if not raw_data_available("SENIOR"):
        return redirect(url_for("collect_bp.SENIOR"))
    raw_data = fetch_raw_data("SENIOR")
    # metadata = raw_data[0]["Metadata"]
    # metadata_soup = bs.BeautifulSoup(metadata, "lxml")
    # to see the codes and their descriptions, uncomment and return the following line
    # jsonify([[tag.get("value"), tag.get_text()] for tag in metadata_soup.find_all("code")])
    metadata_codes = {
        "PEN20A": "Expected years in retirement, men",
        "PEN20B": "Expected years in retirement, women",
        "PEN24A": "Old age income poverty, 66+",
        "PEN24B": "Old age income poverty, 66-75",
        "PEN24C": "Old age income poverty, 76+",
        "PEN24D": "Old age income poverty, 66+, Men",
        "PEN24E": "Old age income poverty, 66+, Women",
    }
    series = extractAllSeries(raw_data[0]["Raw"])
    document_list = []
    for code in metadata_codes.keys():
        document_list.extend(filterSeriesListSeniors(series, code, "PAG", "SENIOR"))
    long_senior_data = pd.DataFrame(document_list)
    wide_senior_data = long_senior_data.pivot(index=["CountryCode", "IndicatorCode", "Year"], columns="VariableCodeOECD", values="Raw").reset_index()
    astype_dict = {
        "PEN20A": "float",
        "PEN20B": "float",
        "PEN24A": "float",
    }
    wide_senior_data = wide_senior_data.astype(astype_dict)
    wide_senior_data["PEN20A_normalized"] = wide_senior_data["PEN20A"].map(lambda x: goalpost(x, 0, 20))
    wide_senior_data["PEN20B_normalized"] = wide_senior_data["PEN20B"].map(lambda x: goalpost(x, 0, 20))
    wide_senior_data["PEN24A_normalized"] = wide_senior_data["PEN24A"].map(lambda x: goalpost(x, 100, 0))
    wide_senior_data["Score"] = 0.25*wide_senior_data["PEN20A_normalized"] + 0.25*wide_senior_data["PEN20B_normalized"] + 0.5*wide_senior_data["PEN24A_normalized"]
    wide_senior_data["Score"] = wide_senior_data["Score"].map(lambda x: round(x, 3))
    wide_senior_data["IndicatorCode"] = "SENIOR"
    wide_senior_data.drop(wide_senior_data[wide_senior_data["PEN20A"].isna() & wide_senior_data["PEN20B"].isna() & wide_senior_data["PEN24A"].isna()].index, inplace=True)
    wide_senior_data["Intermediates"] = [{
        "PEN20A": wide_senior_data["PEN20A"].iloc[i],
        "PEN20B": wide_senior_data["PEN20B"].iloc[i],
        "PEN24A": wide_senior_data["PEN24A"].iloc[i],
    } for i in wide_senior_data.index]
    return jsonify(str(wide_senior_data.to_json(orient='records')))

@compute_bp.route("/PRISON", methods=['GET'])
@login_required
def compute_prison():
    raw_data_observation_list = parse_json(sspi_raw_api_data.find({"collection-info.IndicatorCode": "PRISON"}))
    for obs in raw_data_observation_list:
        table = BeautifulSoup(obs["observation"], 'html.parser').find("table", attrs={"id": "views-aggregator-datatable",
                                                                                               "summary": "Prison population rate"})
    print(table)
    return "string"

@compute_bp.route("/INTRNT", methods=['GET'])
# @login_required
def compute_intrnt():
    if not raw_data_available("INTRNT"):
        return redirect(url_for("collect_bp.INTRNT"))
    # worldbank #
    wbQuery = {"collection-info.IndicatorCode":"GTRANS", "collection-info.Source":"WORLDBANK"}
    worldbank_raw = parse_json(sspi_raw_api_data.find(wbQuery))
    worldbank_clean_list = cleanedWorldBankData(worldbank_raw, "GTRANS")
    wb_df = pd.DataFrame(worldbank_clean_list)
    # sdg #
    sdgQuery = {"collection-info.IndicatorCode":"GTRANS", "collection-info.IntermediateCodeCode":"QLMBPS"}
    sdg_raw = parse_json(sspi_raw_api_data.find(sdgQuery))
    intermediate_sdg = extract_sdg_pivot_data_to_nested_dictionary(sdg_raw)
    sdg_cleaned_list = flatten_nested_dictionary_intrnt(intermediate_sdg)
    sdg_df = pd.DataFrame(sdg_cleaned_list)

