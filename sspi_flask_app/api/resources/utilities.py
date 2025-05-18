import json
import pycountry
from bson import json_util
from flask import jsonify
import pandas as pd
import inspect
import math
from sspi_flask_app.models.database import (
    sspi_main_data_v3,
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data,
    sspi_imputed_data,
    sspi_metadata,
    sspi_static_metadata,
    sspi_country_characteristics,
    sspi_static_radar_data,
    sspi_dynamic_line_data,
    sspi_dynamic_matrix_data,
    sspi_static_rank_data,
    sspi_analysis,
    sspi_partial_api_data,
    sspi_clean_outcome_data,
    sspi_raw_outcome_data,
    sspi_panel_data
)
from sspi_flask_app.models.errors import InvalidDatabaseError
from copy import deepcopy


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


def jsonify_df(df: pd.DataFrame):
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
    match database_name:
        case "sspi_metadata": return sspi_metadata
        case "sspi_static_metadata": return sspi_static_metadata
        case "sspi_main_data_v3": return sspi_main_data_v3
        case "sspi_raw_api_data": return sspi_raw_api_data
        case "sspi_clean_api_data": return sspi_clean_api_data
        case "sspi_incomplete_api_data": return sspi_incomplete_api_data
        case "sspi_imputed_data": return sspi_imputed_data
        case "sspi_analysis": return sspi_analysis
        case "sspi_production_data": return sspi_partial_api_data
        case "sspi_country_characteristics": return sspi_country_characteristics
        case "sspi_static_rank_data": return sspi_static_rank_data
        case "sspi_static_radar_data": return sspi_static_radar_data
        case "sspi_dynamic_line_data": return sspi_dynamic_line_data
        case "sspi_dynamic_matrix_data": return sspi_dynamic_matrix_data
        case "sspi_raw_outcome_data": return sspi_raw_outcome_data
        case "sspi_clean_outcome_data": return sspi_clean_outcome_data
        case "sspi_panel_data": return sspi_panel_data
        case _: raise InvalidDatabaseError(database_name)


def string_to_float(string) -> str | float:
    """
    Attempts conversion to float, otherwise returns "NaN" string.

    To filter any non-numeric observations, simply check whether the return
    value is a string or a float.
    """
    if not string:
        return "NaN"
    try:
        return float(string)
    except ValueError:
        return "NaN"


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


def zip_intermediates(document_list, IndicatorCode, ScoreFunction, ValueFunction=None, UnitFunction=None, ScoreBy="Value"):
    """
    Utility function for zipping together intermediate documents into indicator documents
    """
    document_list = convert_data_types(document_list)
    intermediates_list, items_list = filter_intermediates(document_list)
    sspi_clean_api_data.validate_intermediates_list(intermediates_list)
    sspi_clean_api_data.validate_items_list(items_list)
    intermediates_list, noneish_list = drop_none_or_na(intermediates_list)
    print((
        f"There were {len(noneish_list)} none/na documents found"
        "in intermediates_list"
    ))
    gp_intermediates_list = append_goalpost_info(
        intermediates_list, ScoreBy
    )
    indicator_list = group_by_indicator(
        gp_intermediates_list, items_list, IndicatorCode
    )
    print(indicator_list)
    scored_indicator_document_list = score_indicator_documents(
        indicator_list, ScoreFunction, ValueFunction, UnitFunction, ScoreBy
    )
    return filter_incomplete_data(scored_indicator_document_list)


def convert_data_types(document_list):
    """
    Utility function for converting data types in clean documents
    """
    for document in document_list:
        document["Year"] = int(document["Year"])
        document["Value"] = float(document["Value"])
    return document_list


def filter_intermediates(document_list):
    """
    Utility function for filtering out intermediate documents from other items
    to be included inside of Items
    """
    filtered_list = []
    items_list = []
    for document in document_list:
        if "IntermediateCode" in document.keys():
            filtered_list.append(document)
        elif "ItemCode" in document.keys():
            items_list.append(document)
    return filtered_list, items_list


def drop_none_or_na(intermediate_document_list):
    """
    Utility function for dropping documents with None or NaN values
    """
    noneish_list = []
    for document in intermediate_document_list:
        if document["Value"] is None or math.isnan(document["Value"]):
            noneish_list.append(document)
    intermediate_document_list = [
        document for document in intermediate_document_list if document not in noneish_list]
    return intermediate_document_list, noneish_list


def append_goalpost_info(intermediate_document_list, ScoreBy):
    """
    Utility function for appending goalpost information to a document
    """
    if ScoreBy == "Value":
        return intermediate_document_list
    intermediate_codes = set([doc["IntermediateCode"]
                             for doc in intermediate_document_list])
    intermediate_details = sspi_metadata.find({
        "DocumentType": "IntermediateDetail",
        "Metadata.IntermediateCode": {"$in": list(intermediate_codes)}
    })
    # print(intermediate_details)
    for document in intermediate_document_list:
        for detail in intermediate_details:
            if document["IntermediateCode"] == detail["Metadata"]["IntermediateCode"]:
                document["LowerGoalpost"] = detail["Metadata"]["LowerGoalpost"]
                document["UpperGoalpost"] = detail["Metadata"]["UpperGoalpost"]
                document["Score"] = goalpost(
                    document["Value"],
                    detail["Metadata"]["LowerGoalpost"],
                    detail["Metadata"]["UpperGoalpost"]
                )
    return intermediate_document_list


def group_by_indicator(intermediates_list, items_list, IndicatorCode) -> list:
    """
    Utility function for grouping documents by indicator
    """
    indicator_document_hashmap = dict()
    for document in intermediates_list:
        document_id = f"{document['CountryCode']}_{document['Year']}"
        if document_id not in indicator_document_hashmap.keys():
            indicator_document_hashmap[document_id] = {
                "IndicatorCode": IndicatorCode,
                "CountryCode": document["CountryCode"],
                "Year": document["Year"],
                "Intermediates": [],
                "Items": []
            }
        indicator_document_hashmap[document_id]["Intermediates"].append(
            document)
    for document in items_list:
        document_id = f"{document['CountryCode']}_{document['Year']}"
        if document_id in indicator_document_hashmap.keys():
            indicator_document_hashmap[document_id]["Items"].append(document)
    return list(indicator_document_hashmap.values())


def score_indicator_documents(indicator_document_list, ScoreFunction, ValueFunction, UnitFunction, ScoreBy):
    """
    Utility function for scoring indicator documents
    """
    arg_name_list = list(inspect.signature(ScoreFunction).parameters.keys())
    if ValueFunction is None:
        ValueFunction = ScoreFunction
    for i, document in enumerate(indicator_document_list):
        if ScoreBy == "Value":
            arg_value_dict = {intermediate["IntermediateCode"]: intermediate.get(
                "Value", None) for intermediate in document["Intermediates"]}
        elif ScoreBy == "Score":
            arg_value_dict = {
                intermediate["IntermediateCode"]: intermediate.get(
                    "Score", None) for intermediate in document["Intermediates"]
            }
        else:
            raise ValueError(f"Invalid ScoreBy value: {
                             ScoreBy}; must be one of 'Value' or 'Score'")
        if any((type(v) not in [int, float]) for v in arg_value_dict.values()):
            continue
        try:
            arg_value_list = [arg_value_dict[arg] for arg in arg_name_list]
        except KeyError:
            print(f"KeyError: {arg_name_list} for {arg_value_dict}")
            continue
        score = ScoreFunction(*arg_value_list)
        value = ValueFunction(*arg_value_list)
        document["Value"] = value
        document["Unit"] = UnitFunction(
            *arg_value_list) if UnitFunction else "Aggregate"
        document["Score"] = score
    return indicator_document_list


def filter_incomplete_data(indicator_document_list):
    """
    Utility function for filtering incomplete observations resulting
    from missing data.
    """
    filtered_list = []
    partial_observation_list = []
    for document in indicator_document_list:
        key_list = list(document.keys())
        required_keys = ["IndicatorCode", "CountryCode",
                         "Year", "Value", "Unit", "Score"]
        if all([key in key_list for key in required_keys]):
            filtered_list.append(document)
        else:
            partial_observation_list.append(document)
    return filtered_list, partial_observation_list


def score_single_indicator(document_list, IndicatorCode):
    """
    Utility function for scoring an indicator which does not
    contain intermediates; does not require score function
    """
    document_list = convert_data_types(document_list)
    final = append_goalpost_single(document_list, IndicatorCode)
    for doc in document_list:
        doc["IndicatorCode"] = IndicatorCode
        sspi_clean_api_data.validate_document_format(doc)
    return final


def append_goalpost_single(document_list, IndicatorCode):
    details = sspi_metadata.find(
        {"DocumentType": "IndicatorDetail", "Metadata.IndicatorCode": IndicatorCode})[0]
    for document in document_list:
        document["LowerGoalpost"] = details["Metadata"]["LowerGoalpost"]
        document["UpperGoalpost"] = details["Metadata"]["UpperGoalpost"]
        document["Score"] = goalpost(
            document["Value"],
            details["Metadata"]["LowerGoalpost"],
            details["Metadata"]["UpperGoalpost"]
        )
    return document_list


def country_code_to_name(CountryCode):
    try:
        return pycountry.countries.get(alpha_3=CountryCode).name
    except AttributeError:
        return CountryCode


def get_country_code(CountryName):
    '''
    Handles edge cases of country fuzzy matching
    '''
    if "kosovo" in str.lower(CountryName):
        return "XKX"
    if "korea" in str.lower(CountryName) and "democratic" not in str.lower(CountryName):
        return "KOR"
    if "korea" in str.lower(CountryName) and "democratic" in str.lower(CountryName):
        return "PRK"
    if "niger" in str.lower(CountryName) and "nigeria" not in str.lower(CountryName):
        return "NER"
    if "democratic republic" in str.lower(CountryName) and "congo" in str.lower(CountryName):
        return "COD"
    if "congo republic" in str.lower(CountryName):
        return "COG"
    if "guinea bissau" in str.lower(CountryName):
        return "GNB"
    if "laos" in str.lower(CountryName):
        return "LAO"
    if "turkiye" in str.lower(CountryName) or "turkey" in str.lower(CountryName):
        return "TUR"
    if "cape verde" in str.lower(CountryName):
        return "CPV"
    if "swaziland" in str.lower(CountryName):
        return "SWZ"
    if "israel and west bank" in str.lower(CountryName):
        return "ISR"
    if "gambia the" in str.lower(CountryName):
        return "GMB"
    if "timor leste" in str.lower(CountryName):
        return "TLS"
    else:
        return pycountry.countries.search_fuzzy(CountryName)[0].alpha_3


def colormap(PillarCode, alpha: str = "ff"):
    if PillarCode == "SUS":
        return f"#28a745{alpha}"
    if PillarCode == "MS":
        return f"#ff851b{alpha}"
    if PillarCode == "PG":
        return f"#007bff{alpha}"


def find_population(country_code, year):
    '''
    Fetches population data from sspi_country_characteristics for a country in a given year
    country_code: str of alpha-3 code
    year: int of year
    '''
    population_data = sspi_country_characteristics.fetch_population_data(
        "UNPOPL", country_code, year)
    return population_data


def extrapolate_backward(doc_list: list[dict], year: int, series_id=["CountryCode", "IndicatorCode"], impute_only=False):
    """
    Extrapolate backward from the earliest available data point to a target year.

    :param doc_list: list of dicts with keys including 'Year' and series identifiers
    :param year: earliest year to extrapolate to
    :param series_id: keys identifying a unique series (default: CountryCode, IndicatorCode)
    :param impute_only: if True, only return imputed values, excluding original data
    """
    grouped_series = {}
    imputations = []
    for document in doc_list:
        series_key = tuple(document[id_key] for id_key in series_id)
        grouped_series.setdefault(series_key, []).append(document)
    for series_key, documents in grouped_series.items():
        documents.sort(key=lambda x: x['Year'])
        ref_doc = documents[0]
        first_year = ref_doc['Year']
        for missing_year in range(year, first_year):
            new_document = deepcopy(documents[0])
            new_document.update({
                "Year": missing_year,
                "Imputed": True,
                "ImputationMethod": "Backward Extrapolation",
                "ImputationDistance": first_year - missing_year,
            })
            doc_list.append(new_document)
            imputations.append(new_document)
    if impute_only:
        return imputations
    return doc_list


def extrapolate_forward(doc_list: list[dict], year: int, series_id=["CountryCode", "IndicatorCode"], impute_only=False):
    """
    Extrapolate forward from the latest available data point to a target year.

    :param doc_list: list of dicts with keys including 'Year' and series identifiers
    :param year: latest year to extrapolate to
    :param series_id: keys identifying a unique series (default: CountryCode, IndicatorCode)
    :param impute_only: if True, only return imputed values, excluding original data
    """
    grouped_series = {}
    imputations = []
    for document in doc_list:
        series_key = tuple(document[id_key] for id_key in series_id)
        grouped_series.setdefault(series_key, []).append(document)
    for series_key, documents in grouped_series.items():
        documents.sort(key=lambda x: x['Year'])
        ref_doc = documents[-1]
        last_year = ref_doc['Year']
        for missing_year in range(last_year + 1, year + 1):
            new_document = deepcopy(ref_doc)
            new_document.update({
                "Year": missing_year,
                "Imputed": True,
                "ImputationMethod": "Forward Extrapolation",
                "ImputationDistance": missing_year - last_year,
            })
            doc_list.append(new_document)
            imputations.append(new_document)
    if impute_only:
        return imputations
    return doc_list


def interpolate_linear(doc_list: list[dict], series_id=["CountryCode", "IndicatorCode"], impute_only=False):
    """
    Fill missing years in a time series using linear interpolation.

    :param doc_list: list of dicts with keys including 'Year' and series identifiers
    :param series_id: keys identifying a unique series (default: CountryCode, IndicatorCode)
    :param impute_only: if True, only return imputed values, excluding original data
    """
    grouped_series = {}
    imputations = []
    for document in doc_list:
        series_key = tuple(document[id_key] for id_key in series_id)
        grouped_series.setdefault(series_key, []).append(document)
    for series_key, documents in grouped_series.items():
        documents.sort(key=lambda x: x["Year"])
        existing_years = {doc["Year"]: doc for doc in documents}
        all_years = range(documents[0]["Year"], documents[-1]["Year"] + 1)
        for y in all_years:
            if y not in existing_years:
                # Find surrounding known values for interpolation
                prev = next((d for d in reversed(
                    documents) if d["Year"] < y), None)
                next_ = next((d for d in documents if d["Year"] > y), None)
                if prev is None or next_ is None:
                    continue  # can't interpolate without both bounds
                year_span = next_["Year"] - prev["Year"]
                if "Value" not in prev or "Value" not in next_:
                    continue  # skip if values are missing
                value_span = next_["Value"] - prev["Value"]
                slope = value_span / year_span
                interpolated_value = prev["Value"] + slope * (y - prev["Year"])
                new_doc = deepcopy(prev)
                new_doc.update({
                    "Year": y,
                    "Value": interpolated_value,
                    "Imputed": True,
                    "ImputationMethod": "Linear Interpolation",
                    "ImputationDistance": min(y - prev["Year"], next_["Year"] - y)
                })
                doc_list.append(new_doc)
                imputations.append(new_doc)
    if impute_only:
        return imputations
    return doc_list


def generate_item_levels(data: list[dict], entity_id="", value_id="", time_id="", score_id="", exclude_fields: list[str] = []):
    entity_id = entity_id if entity_id else "CountryCode"
    value_id = value_id if value_id else "Value"
    time_id = time_id if time_id else "Year"
    score_id = score_id if score_id else "Score"
    item_levels = {}
    exclude = [entity_id, value_id, time_id, score_id, "_id"]
    exclude.extend(exclude_fields)
    for obs in data:
        level = {}
        level_id = ""
        for k, v in sorted(obs.items()):
            if k in exclude:
                continue
            if isinstance(v, list):
                continue
            level_id += f"{str(k)}:{str(v)};"
            level[k] = v
        if item_levels.get(level_id, None) is not None:
            continue
        else:
            item_levels[level_id] = level
    return list(item_levels.values())


def generate_item_groups(data: list[dict], entity_id="", value_id="", time_id="", score_id="", exclude_fields: list[str] = []):
    entity_id = entity_id if entity_id else "CountryCode"
    value_id = value_id if value_id else "Value"
    time_id = time_id if time_id else "Year"
    score_id = score_id if score_id else "Score"
    item_levels = {}
    exclude = [entity_id, value_id, time_id, score_id, "_id"]
    exclude.extend(exclude_fields)
    for obs in data:
        level = {}
        level_id = ""
        for k, v in sorted(obs.items()):
            if k in exclude:
                continue
            if isinstance(v, list):
                continue
            else:
                level_id += f"{str(k)}:{str(v)};"
                level[k] = v
        structure = {
            "Datasets": {},
            "Identifier": level,
        }
        datasets = item_levels.setdefault(level_id, structure)["Datasets"]
        datasets.setdefault(obs[entity_id], []).append({
            "entity_id": obs[entity_id],
            "time_id": obs[time_id],
            "value_id": obs[value_id],
            "score_id": obs.get(score_id, None),
        })
    return list(item_levels.values())


def slice_intermediate(doc_list, intermediate_code):
    """
    Utility taking for extracting intermediates from the output of
    zip_intermediates

    :param doc_list: List of documents to extract intermediates from, in the
    format of the output of zip_intermediates.
    :param intermediate_code: The code of the intermediate to extract.
    """
    intermediates = []
    for doc in doc_list:
        for intermediate in doc.get('Intermediates', []):
            if intermediate.get('IntermediateCode') == intermediate_code:
                intermediates.append(intermediate)
    return intermediates


def filter_imputations(doc_list):
    """
    Utility taking for extracting imputations from the output of
    zip_intermediates

    :param doc_list: List of documents to extract intermediates from, in the
    format of the output of zip_intermediates.
    """
    imputations = []
    for doc in doc_list:
        if any([i.get('Imputed', False) for i in doc.get('Intermediates', [])]):
            imputations.append(doc)
    return imputations
