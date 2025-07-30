import json
from typing import Callable
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
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
    sspi_score_data,
    sspi_metadata,
    sspi_static_metadata,
    sspi_country_characteristics,
    sspi_static_radar_data,
    sspi_dynamic_line_data,
    sspi_dynamic_matrix_data,
    sspi_static_rank_data,
    sspi_analysis,
    sspi_panel_data,
)
from sspi_flask_app.models.errors import InvalidDatabaseError
from copy import deepcopy
from sklearn.linear_model import LinearRegression


def format_m49_as_string(input):
    """
    Utility function ensuring that all M49 data is correctly formatted as a
    string of length 3 for use with the pycountry library
    """
    input = int(input)
    if input >= 100:
        return str(input)
    elif input >= 10:
        return "0" + str(input)
    else:
        return "00" + str(input)


def jsonify_df(df: pd.DataFrame):
    """
    Utility function for converting a dataframe to a JSON object
    """
    return jsonify(json.loads(str(df.to_json(orient="records"))))


def goalpost(value, lower, upper):
    """Implement the goalposting formula"""
    return max(0, min(1, (value - lower) / (upper - lower)))


def parse_json(data):
    return json.loads(json_util.dumps(data))


def lookup_database(database_name):
    """
    Utility function used for safe database lookup
    Throws an error otherwise
    """
    match database_name:
        case "sspi_metadata":
            return sspi_metadata
        case "sspi_static_metadata":
            return sspi_static_metadata
        case "sspi_main_data_v3":
            return sspi_main_data_v3
        case "sspi_raw_api_data":
            return sspi_raw_api_data
        case "sspi_clean_api_data":
            return sspi_clean_api_data
        case "sspi_indicator_data":
            return sspi_indicator_data
        case "sspi_incomplete_indicator_data":
            return sspi_incomplete_indicator_data
        case "sspi_imputed_data":
            return sspi_imputed_data
        case "sspi_analysis":
            return sspi_analysis
        case "sspi_score_data":
            return sspi_score_data
        case "sspi_country_characteristics":
            return sspi_country_characteristics
        case "sspi_static_rank_data":
            return sspi_static_rank_data
        case "sspi_static_radar_data":
            return sspi_static_radar_data
        case "sspi_dynamic_line_data":
            return sspi_dynamic_line_data
        case "sspi_dynamic_matrix_data":
            return sspi_dynamic_matrix_data
        case "sspi_panel_data":
            return sspi_panel_data
        case _:
            raise InvalidDatabaseError(database_name)


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


def score_indicator(
    dataset_document_list: list[dict],
    indicator_code: str,
    score_function: Callable,
    unit: str | Callable,
):
    """
    Utility function for computing indicator scores documents into indicator documents
    """
    dataset_document_list = convert_data_types(dataset_document_list)
    sspi_clean_api_data.validate_dataset_list(dataset_document_list)
    dataset_document_list, noneish_list = drop_none_or_na(dataset_document_list)
    indicator_list = group_by_indicator(dataset_document_list, indicator_code)
    scored_indicator_document_list = score_indicator_documents(
        indicator_list, score_function, unit
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


def drop_none_or_na(intermediate_document_list):
    """
    Utility function for dropping documents with None or NaN values
    """
    noneish_list = []
    for document in intermediate_document_list:
        if document["Value"] is None or math.isnan(document["Value"]):
            noneish_list.append(document)
    intermediate_document_list = [
        document
        for document in intermediate_document_list
        if document not in noneish_list
    ]
    return intermediate_document_list, noneish_list


def group_by_indicator(dataset_document_list, indicator_code) -> list:
    """
    Utility function for grouping documents by indicator
    """
    indicator_document_hashmap = dict()
    for document in dataset_document_list:
        document_id = f"{document['CountryCode']}_{document['Year']}"
        if document_id not in indicator_document_hashmap.keys():
            indicator_document_hashmap[document_id] = {
                "IndicatorCode": indicator_code,
                "CountryCode": document["CountryCode"],
                "Year": document["Year"],
                "Datasets": [],
            }
        indicator_document_hashmap[document_id]["Datasets"].append(document)
    return list(indicator_document_hashmap.values())


def score_indicator_documents(
    indicator_document_list: list[dict], 
    score_function: Callable,
    unit: str | Callable
):
    """
    Utility function for scoring indicator documents

    :param indicator_document_list: List of indicator documents to score.
    :param score_function: Function to compute the score for each document. The
        function must take DatasetCodes as arguments and return a float.
    :param unit: Function to compute the unit for each document, or a string
        representing the unit. If a function is provided, it must take the same
        arguments as the score_function and return a string.
    """
    arg_name_list = list(inspect.signature(score_function).parameters.keys())
    for i, document in enumerate(indicator_document_list):
        arg_value_dict = {
            dataset["DatasetCode"]: dataset.get("Value", None)
            for dataset in document["Datasets"]
        }
        if any((type(v) not in [int, float]) for v in arg_value_dict.values()):
            continue
        try:
            arg_value_list = [arg_value_dict[arg] for arg in arg_name_list]
        except KeyError:
            print(f"KeyError: {arg_name_list} for {arg_value_dict}")
            continue
        score = score_function(*arg_value_list)
        if isinstance(unit, str):
            document["Unit"] = unit
        elif isinstance(unit, Callable):
            document["Unit"] = unit(*arg_value_list)
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
        required_keys = [
            "IndicatorCode",
            "CountryCode",
            "Year",
            "Unit",
            "Score",
        ]
        if all([key in key_list for key in required_keys]):
            filtered_list.append(document)
        else:
            partial_observation_list.append(document)
    return filtered_list, partial_observation_list


def country_code_to_name(CountryCode):
    try:
        guess = pycountry.countries.get(alpha_3=CountryCode)
        if not guess:
            raise AttributeError
        return guess.name
    except AttributeError:
        return CountryCode


def get_country_code(CountryName):
    """
    Handles edge cases of country fuzzy matching
    """
    if "kosovo" in str.lower(CountryName):
        return "XKX"
    if "korea" in str.lower(CountryName) and "democratic" not in str.lower(CountryName):
        return "KOR"
    if "korea" in str.lower(CountryName) and "democratic" in str.lower(CountryName):
        return "PRK"
    if "niger" in str.lower(CountryName) and "nigeria" not in str.lower(CountryName):
        return "NER"
    if "democratic republic" in str.lower(CountryName) or "dr" in str.lower(CountryName) and "congo" in str.lower(CountryName):
        return "COD"
    if "congo republic" in str.lower(CountryName):
        return "COG"
    if "guinea bissau" in str.lower(CountryName):
        return "GNB"
    if "laos" in str.lower(CountryName):
        return "LAO"
    if "kiye" in str.lower(CountryName):
        return "TUR"
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
        try:
            guess = pycountry.countries.lookup(CountryName)
            return guess.alpha_3
        except LookupError:
            # If the country name is not found, return the name as is
            return CountryName


def colormap(PillarCode, alpha: str = "ff"):
    if PillarCode == "SUS":
        return f"#28a745{alpha}"
    if PillarCode == "MS":
        return f"#ff851b{alpha}"
    if PillarCode == "PG":
        return f"#007bff{alpha}"


def find_population(country_code, year):
    """
    Fetches population data from sspi_country_characteristics for a country in a given year
    country_code: str of alpha-3 code
    year: int of year
    """
    population_data = sspi_country_characteristics.fetch_population_data(
        "POPULN", country_code, year
    )
    return population_data


def extrapolate_backward(
    doc_list: list[dict],
    year: int,
    series_id=["CountryCode", "IndicatorCode"],
    impute_only=False,
):
    """
    Extrapolate backward from the earliest available data point to a target year.

    :param doc_list: list of dicts with keys including 'Year' and series identifiers
    :param year: earliest year to extrapolate to
    :param series_id: keys identifying a unique series (default: CountryCode, IndicatorCode)
    :param impute_only: if True, only return imputed values, excluding original data
    """
    grouped_series = {}
    imputations = []
    copied_doc_list = deepcopy(doc_list)
    for document in copied_doc_list:
        series_key = tuple(document[id_key] for id_key in series_id)
        grouped_series.setdefault(series_key, []).append(document)
    for series_key, documents in grouped_series.items():
        documents.sort(key=lambda x: x["Year"])
        ref_doc = documents[0]
        first_year = ref_doc["Year"]
        for missing_year in range(year, first_year):
            new_document = deepcopy(documents[0])
            new_document.update(
                {
                    "Year": missing_year,
                    "Imputed": True,
                    "ImputationMethod": "Backward Extrapolation",
                    "ImputationDistance": first_year - missing_year,
                }
            )
            copied_doc_list.append(new_document)
            imputations.append(new_document)
    if impute_only:
        return imputations
    return copied_doc_list


def extrapolate_forward(
    doc_list: list[dict],
    year: int,
    series_id=["CountryCode", "IndicatorCode"],
    impute_only=False,
):
    """
    Extrapolate forward from the latest available data point to a target year.

    :param doc_list: list of dicts with keys including 'Year' and series identifiers
    :param year: latest year to extrapolate to
    :param series_id: keys identifying a unique series (default: CountryCode, IndicatorCode)
    :param impute_only: if True, only return imputed values, excluding original data
    """
    copied_doc_list = deepcopy(doc_list)
    grouped_series = {}
    imputations = []
    for document in copied_doc_list:
        series_key = tuple(document[id_key] for id_key in series_id)
        grouped_series.setdefault(series_key, []).append(document)
    for series_key, documents in grouped_series.items():
        documents.sort(key=lambda x: x["Year"])
        ref_doc = documents[-1]
        last_year = ref_doc["Year"]
        for missing_year in range(last_year + 1, year + 1):
            new_document = deepcopy(ref_doc)
            new_document.update(
                {
                    "Year": missing_year,
                    "Imputed": True,
                    "ImputationMethod": "Forward Extrapolation",
                    "ImputationDistance": missing_year - last_year,
                }
            )
            copied_doc_list.append(new_document)
            imputations.append(new_document)
    if impute_only:
        return imputations
    return copied_doc_list


def interpolate_linear(
    doc_list: list[dict], series_id=["CountryCode", "IndicatorCode"], impute_only=False
):
    """
    Fill missing years in a time series using linear interpolation.

    :param doc_list: list of dicts with keys including 'Year' and series identifiers
    :param series_id: keys identifying a unique series (default: CountryCode, IndicatorCode)
    :param impute_only: if True, only return imputed values, excluding original data
    """
    grouped_series = {}
    imputations = []
    copied_doc_list = deepcopy(doc_list)
    for document in copied_doc_list:
        series_key = tuple(document[id_key] for id_key in series_id)
        grouped_series.setdefault(series_key, []).append(document)
    for series_key, documents in grouped_series.items():
        documents.sort(key=lambda x: x["Year"])
        existing_years = {doc["Year"]: doc for doc in documents}
        all_years = range(documents[0]["Year"], documents[-1]["Year"] + 1)
        for y in all_years:
            if y not in existing_years:
                # Find surrounding known values for interpolation
                prev = next((d for d in reversed(documents) if d["Year"] < y), None)
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
                new_doc.update(
                    {
                        "Year": y,
                        "Value": interpolated_value,
                        "Imputed": True,
                        "ImputationMethod": "Linear Interpolation",
                        "ImputationDistance": min(y - prev["Year"], next_["Year"] - y),
                    }
                )
                copied_doc_list.append(new_doc)
                imputations.append(new_doc)
    if impute_only:
        return imputations
    return copied_doc_list


def generate_item_levels(
    data: list[dict],
    entity_id="",
    value_id="",
    time_id="",
    score_id="",
    exclude_fields: list[str] = [],
):
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


def generate_item_groups(
    data: list[dict],
    entity_id="",
    value_id="",
    time_id="",
    score_id="",
    exclude_fields: list[str] = [],
):
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
        datasets.setdefault(obs[entity_id], []).append(
            {
                "entity_id": obs[entity_id],
                "time_id": obs[time_id],
                "value_id": obs[value_id],
                "score_id": obs.get(score_id, None),
            }
        )
    return list(item_levels.values())


def slice_dataset(doc_list, dataset_codes: list[str] | str):
    """
    Utility taking for extracting datasets from the output of
    score_indicator

    :param doc_list: List of documents to extract datasets from, in the
    format of the output of score_indicator.
    :param dataset_codes: List of dataset codes to filter by, or a single
    dataset code as a string.
    """
    datasets = []
    if not isinstance(dataset_codes, list):
        dataset_codes = [dataset_codes]
    for doc in doc_list:
        print(doc)
        for dataset in doc.get("Datasets", []):
            if dataset.get("DatasetCode") in dataset_codes:
                datasets.append(dataset)
    return datasets


def filter_imputations(doc_list):
    """
    Utility taking for extracting imputations from the output of
    score_indicator

    :param doc_list: List of documents to extract intermediates from, in the
    format of the output of score_indicator.
    """
    imputations = []
    for doc in doc_list:
        if any([i.get("Imputed", False) for i in doc.get("Intermediates", [])]):
            imputations.append(doc)
    return imputations


def impute_global_average(
    country_code: str, start_year: int, end_year: int, item_type: str, item_code: str, ref_data: list[dict]
):
    """
    Impute the global average for a given country and year range.

    :param country_code: The country code to impute.
    :param start_year: The starting year for the imputation.
    :param end_year: The ending year for the imputation.
    :param item_type: The type of item being imputed. Valid values are "Intermediate" or "Indicator".
    :param item_code: The code of the item being imputed (e.g., "GINIPT").
    :param ref_data: The reference data to calculate the global average.
    """
    if not all([x["Unit"] == ref_data[0]["Unit"] for x in ref_data]):
        raise ValueError("Units are not consistent across reference data.")
    if item_type not in ["Intermediate", "Indicator"]:
        raise ValueError("item_type must be either 'Intermediate' or 'Indicator'.")
    mean_value = sum([x["Value"] for x in ref_data]) / len(ref_data)
    mean_score = sum([x["Score"] for x in ref_data]) / len(ref_data)
    imputation_list = []
    for year in range(start_year, end_year + 1):
        imputed_document = {
            "CountryCode": country_code,
            "Value": mean_value,
            "Score": mean_score,
            "Year": year,
            "Unit": ref_data[0]["Unit"],
            "Imputed": True,
            "ImputationMethod": "ImputeGlobalAverage",
        }
        if item_type == "Intermediate":
            imputed_document["IntermediateCode"] = item_code
        elif item_type == "Indicator":
            imputed_document["IndicatorCode"] = item_code
        imputation_list.append(imputed_document)
    return imputation_list


def regression_imputation(
    feature_list: list[dict],
    outcome_list: list[dict],
    predictor_list: list[dict],
    target_indicator: str,
    unit: str,
    model_string: str,
    details: str,
    lg: float | int = 0,
    ug: float | int = 1,
) -> list[dict]:
    """
    Perform regression imputation for a target indicator using features.

    :param feature_list: List of feature documents with 'FeatureCode', 'CountryCode', 'Year', and 'Score'
    used to train the model. Must have the same dimension as the predictor_list.
    :param outcome_list: List of outcome documents with 'IndicatorCode', 'CountryCode', 'Year', and 'Score' used to train the model.
    :param predictor_list: List of prediction documents with 'FeatureCode', 'CountryCode', 'Year', and 'Score'
    to as the predictors for missing documents. Must have the same dimensions as the feature_list.
    :param target_indicator: The indicator code for the target variable to be imputed.
    :param model_string: A string representation of the regression model, e.g., "GINIPT ~ ISHRAT + y_0 + e".
    :param details: a short paragraph describing the imputation method and its rationale.
    :return: List of imputed documents with imputed values for the target indicator.
    """
    # ---------- 1. reshape features ----------
    X = (
        pd.DataFrame.from_records(feature_list)
        .pivot_table(
            index=["CountryCode", "Year"], columns="FeatureCode", values="Score"
        )
        .sort_index()
    )
    # ---------- 2. reshape outcomes ----------
    y = (
        pd.DataFrame.from_records(outcome_list)
        .pivot_table(
            index=["CountryCode", "Year"], columns="IndicatorCode", values="Score"
        )
        .sort_index()
        .rename(columns={target_indicator: "target"})
    )
    # ---------- 3. reshape predictions ----------
    P = (
        pd.DataFrame.from_records(predictor_list)
        .pivot_table(
            index=["CountryCode", "Year"], columns="FeatureCode", values="Score"
        )
        .sort_index()
    )
    # ---------- 5. train ----------
    train = X.join(y, how="inner").dropna()
    X_train, y_train = train.drop(columns="target"), train["target"]
    model = LinearRegression(fit_intercept=True).fit(X_train, y_train)
    # ---------- 4. predict ----------
    P_aligned = P.reindex(columns=X_train.columns)
    panel = P_aligned.join(y, how="left")          # attach any known targets
    missing = panel["target"].isna()
    panel.loc[missing, "target"] = model.predict(P_aligned.loc[missing])
    panel["target"] = panel["target"].clip(0, 1)
    # ---------- 6. tidy & return ----------
    document_list = (
        panel.reset_index()
        .rename(columns={"target": "Score"})[["CountryCode", "Year", "Score"]]
        .to_dict(orient="records")
    )
    for doc in document_list:
        doc["IndicatorCode"] = target_indicator
        doc["Imputed"] = True
        doc["ImputationMethod"] = "RegressionImputation"
        doc["ImputationRegessionModel"] = model_string
        doc["ImputationDetails"] = details
        doc["ImputationDistance"] = 0
        doc["LowerGoalpost"] = lg
        doc["UpperGoalpost"] = ug
        doc["Unit"] = unit
        doc["Value"] = (ug - lg) * doc["Score"] + lg
    return document_list


def check_raw_document_set_coverage(dataset_list: list[str]) -> tuple[list[str], list[str]]:
    """
    Checks the coverage of the raw API data for the given dataset list.
    Returns a tuple of lists: uncollected datasets and collected datasets.
    If a dataset is not collected, it is added to the uncollected list.
    If a dataset is collected, it is added to the collected list.
    :param dataset_list: List of dataset codes to check.
    :return: Tuple of lists (uncollected_datasets, collected_datasets)
    """

    collected_datasets = []
    uncollected_datasets = []
    for ds_code in dataset_list:
        source_info = sspi_metadata.get_source_info(ds_code)
        if sspi_raw_api_data.raw_data_available(source_info):
            collected_datasets.append(ds_code)
        else:
            uncollected_datasets.append(ds_code)
    return uncollected_datasets, collected_datasets


def deduplicate_dictionary_list(dicts: list[dict]) -> list:
    seen = set()
    unique = []
    for d in dicts:
        key = tuple(sorted(d.items()))
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique

def reduce_dataset_list(dataset_list: list[str]) -> list[str]:
    """
    Reduce the dataset list by removing datasets with duplicate
    source information. Each RawDocumentSet/Source may contain 
    the information for multiple datasets. This function takes 
    a list of dataset codes which may not be an injective mapping
    onto RawDocumentSets and returns sublist of dataset codes
    which is bijective onto RawDocumentSets.
    :param dataset_list: List of dataset codes to reduce.
    :return: List of dataset codes with unique source information.
    """
    source_info = [sspi_metadata.get_source_info(ds) for ds in dataset_list]
    source_info_dedup = deduplicate_dictionary_list(source_info)
    dataset_list_reduced = []
    for uniq_source in source_info_dedup:
        i = 0
        found = False
        while i < len(dataset_list) and not found:
            if uniq_source == source_info[i]:
                dataset_list_reduced.append(dataset_list[i])
                found = True
            i += 1
    return dataset_list_reduced
