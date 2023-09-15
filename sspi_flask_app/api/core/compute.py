from flask import Blueprint, redirect, url_for
from ..api import raw_data_available, parse_json
from ... import sspi_clean_api_data, sspi_raw_api_data
from ..datasource.sdg import flatten_nested_dictionary_biodiv, extract_sdg_pivot_data_to_nested_dictionary, flatten_nested_dictionary_redlst
from ..datasource.worldbank import cleanedWorldBankData
from ..api import fetch_raw_data, missing_countries, added_countries
from ..datasource.oecdstat import organizeOECDdata, OECD_country_list
import xml.etree.ElementTree as ET
import pandas as pd


compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/compute")

@compute_bp.route("/BIODIV", methods=['GET'])
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
def compute_rdlst():
    if not raw_data_available("REDLST"):
        return redirect(url_for("api_bp.collect_bp.REDLST"))
    raw_data = fetch_raw_data("REDLST")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    final_list = flatten_nested_dictionary_redlst(intermediate_obs_dict)
    sspi_clean_api_data.insert_many(final_list)
    return parse_json(final_list)

@compute_bp.route("/COALPW")
def compute_coalpw():
    if not raw_data_available("COALPW"):
        return redirect(url_for("api_bp.collect_bp.coalpw"))
    raw_data = fetch_raw_data("COALPW")
    observations = [entry["observation"] for entry in raw_data]
    observations = [entry["observation"] for entry in raw_data]
    df = pd.DataFrame(observations)
    return parse_json(df.head().to_json())

@compute_bp.route("/ALTNRG", methods=['GET'])
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
def compute_gtrans():
    #worldbank compute
    # if not raw_data_available("GTRANS"):
    #     return "Data unavailable. Try running collect."
    # raw_data = fetch_raw_data("GTRANS")
    # world_bank_data = []
    # for element in raw_data:
    #     if element["collection-info"]["Source"] == "WORLDBANK":
    #         world_bank_data.append(element)
    # final_list = cleanedWorldBankData(raw_data, "GTRANS")
    # sspi_clean_api_data.insert_many(final_list)


   
    



    # return parse_json(final_list)


    #oecd compute
    oecd_raw_data = fetch_raw_data("GTRANS")[0]["observation"]
    oecd_raw_data = oecd_raw_data[14:]
    oecd_raw_data = oecd_raw_data[:-1]
    xml_file_root = ET.fromstring(oecd_raw_data)
    series_list = xml_file_root.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}DataSet/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Series")
    final_list = organizeOECDdata(series_list)
    return parse_json(final_list)
    # sspi_clean_api_data.insert_many(final_list)
    # Merging files: combined_data = wb_df.merge(oecd_df, how="outer", on=["CountryCode", "YEAR"])
    # Overwrite all NaN values with String "NaN"
    # Parse that back into the right list format between 
    sspi_country_list = ["ARG","AUS","AUT","BEL","BRA","CAN","CHL","CHN","COL","CZE","DNK","EST","FIN","FRA","DEU","GRC","HUN","ISL","IND","IDN","IRL","ISR","ITA","JPN","KOR","KWT","LVA","LTU","LUX","MEX","NLD","NZL","NOR","POL","PRT","RUS","SAU","SGP","SVK","SVN","ZAF","ESP","SWE","CHE","TUR","ARE","GBR","USA","URY"]
    missing = missing_countries(sspi_country_list, OECD_country_list(series_list))
    added = added_countries(sspi_country_list, OECD_country_list(series_list))
    print ("these are the missing countries:" + str(missing))
    print ("these are the additonal countries:" + str(added))

    # return parse_json(final_list)
