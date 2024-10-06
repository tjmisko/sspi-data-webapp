import json
import pycountry
from bson import json_util
from flask import jsonify
import pandas as pd
import inspect
import math
from ... import sspi_main_data_v3, sspi_bulk_data, sspi_raw_api_data, sspi_clean_api_data, sspi_imputed_data, sspi_metadata, sspi_production_data, sspi_country_characteristics
from sspi_flask_app.models.errors import InvalidDatabaseError

def format_m49_as_string(input):
    """
    Utility function ensuring that all M49 data is correctly formatted as a
    string of length 3 for use with the pycountry library
    """
    input = int(input)
    if input >= 100:
        return str(input) 
    elif input >= 10:
        return '0' + str(input)
    else: 
        return '00' + str(input)

def jsonify_df(df:pd.DataFrame):
    """
    Utility function for converting a dataframe to a JSON object
    """
    return jsonify(json.loads(str(df.to_json(orient='records'))))

def goalpost(value, lower, upper):
    """ Implement the goalposting formula"""
    return max(0, min(1, (value - lower)/(upper - lower)))

def parse_json(data):
    return json.loads(json_util.dumps(data))

def lookup_database(database_name):
    """
    Utility function used for safe database lookup

    Throws an error otherwise
    """
    if database_name == "sspi_main_data_v3":
        return sspi_main_data_v3
    elif database_name == "sspi_bulk_data":
        return sspi_bulk_data
    elif database_name == "sspi_raw_api_data":
        return sspi_raw_api_data
    elif database_name == "sspi_clean_api_data":
        return sspi_clean_api_data
    elif database_name == "sspi_imputed_data":
        return sspi_imputed_data
    elif database_name == "sspi_metadata":
        return sspi_metadata
    elif database_name == "sspi_production_data":
        return sspi_production_data
    elif database_name == "sspi_country_characteristics":
        return sspi_country_characteristics
    raise InvalidDatabaseError(database_name)

def string_to_float(string):
    """
    Passes back string 'NaN' instead of float NaN
    """
    if string is None:
        return "NaN"
    if string == "N":
        return "NaN"
    if math.isnan(float(string)):
        return "NaN"
    return float(string)

def string_to_int(string):
    return int(string)

def missing_countries(sspi_country_list, source_country_list):
    missing_countries = []
    for country in sspi_country_list:
        if country not in source_country_list:
            missing_countries.append(country)
    return missing_countries

def added_countries(sspi_country_list, source_country_list):
    additional_countries = []
    for other_country in source_country_list:
        if other_country not in sspi_country_list:
            additional_countries.append(other_country)
    return additional_countries

def zip_intermediates(intermediate_document_list, IndicatorCode, ScoreFunction, ScoreBy="Value"):
    """
    Utility function for zipping together intermediate documents into indicator documents
    """
    intermediate_document_list = convert_data_types(intermediate_document_list)
    sspi_clean_api_data.validate_intermediates_list(intermediate_document_list)
    gp_intermediate_list = append_goalpost_info(intermediate_document_list, ScoreBy)
    indicator_document_list = group_by_indicator(gp_intermediate_list, IndicatorCode)
    scored_indicator_document_list = score_indicator_documents(indicator_document_list, ScoreFunction, ScoreBy)
    return scored_indicator_document_list

def convert_data_types(intermediate_document_list):
    """
    Utility function for converting data types in intermediate documents
    """
    for document in intermediate_document_list:
        document["Year"] = int(document["Year"])
        document["Value"] = float(document["Value"])
    return intermediate_document_list
    
def append_goalpost_info(intermediate_document_list, ScoreBy):
    """
    Utility function for appending goalpost information to a document
    """
    if ScoreBy == "Values":
        return intermediate_document_list
    intermediate_codes = set([doc["IntermediateCode"] for doc in intermediate_document_list])
    intermediate_details = sspi_metadata.find({"DocumentType": "IntermediateDetail", "Metadata.IntermediateCode": {"$in": list(intermediate_codes)}})
    print(intermediate_details)
    for document in intermediate_document_list:
        for detail in intermediate_details:
            if document["IntermediateCode"] == detail["Metadata"]["IntermediateCode"]:
                document["LowerGoalpost"] = detail["Metadata"]["LowerGoalpost"]
                document["UpperGoalpost"] = detail["Metadata"]["UpperGoalpost"]
                document["Score"] = goalpost(document["Value"], detail["Metadata"]["LowerGoalpost"], detail["Metadata"]["UpperGoalpost"])
    return intermediate_document_list

def group_by_indicator(intermediate_document_list, IndicatorCode) -> list:
    """
    Utility function for grouping documents by indicator
    """
    indicator_document_hashmap = dict() 
    for document in intermediate_document_list:
        document_id = f"{document['CountryCode']}_{document['Year']}"
        if document_id not in indicator_document_hashmap.keys():
            indicator_document_hashmap[document_id] = {
                "IndicatorCode": IndicatorCode,
                "CountryCode": document["CountryCode"],
                "Year": document["Year"],
                "Intermediates": [],
            }
        indicator_document_hashmap[document_id]["Intermediates"].append(document)
    return list(indicator_document_hashmap.values())

def score_indicator_documents(indicator_document_list, ScoreFunction, ScoreBy):
    """
    Utility function for scoring indicator documents
    """
    arg_name_list = list(inspect.signature(ScoreFunction).parameters.keys())
    for i, document in enumerate(indicator_document_list):
        if ScoreBy == "Values":
            arg_value_dict = {intermediate["IntermediateCode"]: intermediate.get("Value", None) for intermediate in document["Intermediates"]}
        elif ScoreBy == "Score":
            arg_value_dict = {intermediate["IntermediateCode"]: intermediate.get("Score", None) for intermediate in document["Intermediates"]}
        else:
            raise ValueError(f"Invalid ScoreBy value: {ScoreBy}; must be one of 'Values' or 'Score'")
        if any(arg_value is None for arg_value in arg_value_dict.values()):
            continue
        try:
            arg_value_list = [arg_value_dict[arg_name] for arg_name in arg_name_list]
        except KeyError:
            continue
        score = ScoreFunction(*arg_value_list)
        if score is not None:
            document["Value"] = score
            document["Unit"] = "Aggregate"
            document["Score"] = score
    return indicator_document_list

def filter_incomplete_data(indicator_document_list):
    """
    Utility function for filtering incomplete observations resulting
    from missing data.
    
    Call on the result of `zip_intermediates` before inserting into the
    clean database.
    """
    filtered_list = []
    partial_observation_list = []
    for document in indicator_document_list:
        key_list = list(document.keys())
        required_keys = ["IndicatorCode", "CountryCode", "Year", "Value", "Unit", "Score"]
        if all([key in key_list for key in required_keys]):
            filtered_list.append(document)
        else:
            partial_observation_list.append(document)
    return filtered_list, partial_observation_list

def score_single_indicator(document_list, IndicatorCode):
   """
    Utility function for scoring an indicator which does not contain intermediates; does not require score function
    """
   document_list = convert_data_types(document_list)
   final = append_goalpost_single(document_list, IndicatorCode)
   [sspi_clean_api_data.validate_document_format(document) for document in document_list]
   return final
   
def append_goalpost_single(document_list, IndicatorCode):
    details = sspi_metadata.find({"DocumentType": "IndicatorDetail", "Metadata.IndicatorCode": IndicatorCode})[0]
    for document in document_list:
        document["LowerGoalpost"] = details["Metadata"]["LowerGoalpost"]
        document["UpperGoalpost"] = details["Metadata"]["UpperGoalpost"]
        document["Score"] = goalpost(document["Value"], details["Metadata"]["LowerGoalpost"], details["Metadata"]["UpperGoalpost"])
    return document_list

def country_code_to_name(CountryCode):
    try:
        return pycountry.countries.get(alpha_3=CountryCode).name
    except AttributeError:
        return CountryCode

def colormap(PillarCode, alpha:str="ff"):
    if PillarCode == "SUS":
        return f"#28a745{alpha}"
    if PillarCode == "MS":
        return f"#ff851b{alpha}"
    if PillarCode == "PG":
        return f"#007bff{alpha}"
