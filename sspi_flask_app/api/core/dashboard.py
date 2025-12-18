from sspi_flask_app.api.resources.utilities import (
    parse_json,
    lookup_database,
    country_code_to_name,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    generate_series_levels,
    generate_series_groups,
    jsonify_df
)
import pycountry
import json
from flask import (
    Blueprint,
    Response,
    jsonify,
    request,
    render_template,
    current_app as app,
)
from sspi_flask_app.models.sspi import SSPI, FastSSPI
from sspi_flask_app.models.coverage import DataCoverage
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_static_data_2018,
    sspi_item_data,
    sspi_metadata,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_panel_data,
    sspi_static_rank_data,
    sspi_static_metadata,
    sspi_static_radar_data,
    sspi_static_stack_data,
    sspi_indicator_dynamic_line_data,
    sspi_item_dynamic_line_data,
    sspi_dynamic_matrix_data,
    sspi_globe_data,
    sspi_dynamic_radar_data,
    sspi_clean_api_data,
    sspi_dynamic_rank_data
)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app import csrf
from datetime import datetime
import hashlib
import logging
import re
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

dashboard_bp = Blueprint(
    "dashboard_bp", __name__, template_folder="templates", static_folder="static"
)


@dashboard_bp.route("/status/database/<database>")
@admin_required
def get_database_status(database):
    ndocs = lookup_database(database).count_documents({})
    return render_template("database-status.html", database=database, ndocs=ndocs)


@dashboard_bp.route("/static/indicator/<IndicatorCode>")
def get_static_indicator_data(IndicatorCode):
    """
    Get the static data for the given indicator code
    """
    static_data = parse_json(
        sspi_static_data_2018.find({"IndicatorCode": IndicatorCode}, {"_id": 0})
    )
    data_series = [
        {
            "Year": document["Year"],
            "CountryCode": document["CountryCode"],
            "Rank": document["Rank"],
            "Score": document["Score"],
            "Value": document["Value"],
        }
        for document in static_data
    ]
    labels = [document["CountryCode"] for document in static_data]
    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": "Score",
                "data": data_series,
                "parsing": {"xAxisKey": "Rank", "yAxisKey": "Score"},
            }
        ],
    }
    return jsonify(chart_data)


@dashboard_bp.route("/panel/indicator/<indicator_code>", methods=["GET"])
def get_dynamic_indicator_line_data(indicator_code):
    """
    Get the dynamic indicator data for a given indicator code for a line chart
    This is distinguished from retrieving item data, which also returns the
    indicator data, in that this endpoint handles passing the underlying datasets
    to IndicatorPanelChart, which can render them in addition to the indicator score
    data.
    """
    indicator_details = sspi_metadata.indicator_details()
    name_map = {detail["ItemCode"]: detail["ItemName"] for detail in indicator_details}
    active_schema = sspi_item_data.active_schema(name_map=name_map)
    detail = sspi_metadata.get_item_detail(indicator_code)
    doc_type = detail.get("ItemType", "No Item Type")
    print("Document Type:", doc_type)
    if not doc_type == "Indicator":
        return jsonify({"error": "Invalid Item Type for dynamic indicator data"}), 400
    item_options = sspi_metadata.indicator_options()
    name = detail.get("ItemName")
    tree_path = detail.get("TreePath", "")
    tree_path_parts = tree_path.split("/")
    # Build enriched treepath with itemCodes and itemNames
    enriched_treepath = []
    for itemCode in tree_path_parts:
        if itemCode:  # Skip empty strings from split
            if itemCode.lower() == "sspi":
                # Handle SSPI root case specially
                enriched_treepath.append(
                    {
                        "itemCode": itemCode.lower(),
                        "itemName": "Sustainable and Shared-Prosperity Policy Index",
                    }
                )
            else:
                # Query metadata for other items
                try:
                    item_detail = sspi_metadata.get_item_detail(itemCode)
                    item_name = item_detail.get("ItemName", itemCode.upper())
                    enriched_treepath.append(
                        {"itemCode": itemCode.lower(), "itemName": item_name}
                    )
                except Exception as e:
                    # Fallback to itemCode if metadata lookup fails
                    print(
                        f"Warning: Could not get metadata for itemCode {itemCode}: {e}"
                    )
                    enriched_treepath.append(
                        {"itemCode": itemCode.lower(), "itemName": itemCode.upper()}
                    )
    description = detail.get("Description", "")
    country_query = request.args.getlist("CountryCode")
    query = {"ICode": indicator_code}
    if country_query:
        query["CCode"] = {"$in": country_query}

    # Convert cursor to list and check if data exists
    dynamic_score_data = list(sspi_indicator_dynamic_line_data.find(query))

    if not dynamic_score_data:
        # No chart data available for this indicator
        print(f"Warning: No dynamic chart data found for indicator {indicator_code}")
        year_labels = list(range(2000, datetime.now().year + 1))
        return jsonify({
            "error": f"No chart data available for indicator {indicator_code}",
            "data": [],
            "title": f"{name} Score" if name else indicator_code,
            "labels": year_labels,
            "description": description,
            "groupOptions": sspi_metadata.country_groups(),
            "countryGroupMap": sspi_metadata.country_group_map(),
            "itemOptions": item_options,
            "itemType": doc_type,
            "itemCode": indicator_code,
            "datasetOptions": [],
            "tree": active_schema,
            "treepath": enriched_treepath,
        }), 200

    available_datasets = list(dynamic_score_data[0].get("Datasets", {}).keys())
    dataset_options = []
    for dscode in available_datasets:
        detail = sspi_metadata.get_dataset_detail(dscode)
        ds_range = detail.get("Range", {})
        # Always include datasetName, use datasetCode as fallback
        dataset_options.append(
            {
                "datasetName": detail.get("DatasetName", dscode),
                "datasetCode": dscode,
                "datasetDescription": detail.get("Description", ""),
                "unit": detail.get("Unit", ""),
                "yMin": ds_range.get("yMin", 0) if ds_range else 0,
                "yMax": ds_range.get("yMax", 1) if ds_range else 1,
            }
        )
    year_labels = list(range(2000, datetime.now().year + 1))  # Default to 2000-present
    chart_title = f"{name} Score"
    group_options = sspi_metadata.country_groups()
    country_group_map = sspi_metadata.country_group_map()
    return jsonify(
        {
            "data": dynamic_score_data,
            "title": chart_title,
            "labels": year_labels,
            "description": description,
            "groupOptions": group_options,
            "countryGroupMap": country_group_map,
            "itemOptions": item_options,
            "itemType": doc_type,
            "itemCode": indicator_code,
            "datasetOptions": dataset_options,
            "tree": active_schema,
            "treepath": enriched_treepath,
        }
    )


@dashboard_bp.route("/panel/score/<item_code>", methods=["GET"])
def get_dynamic_score_line_data(item_code):
    """
    Get the dynamic data for the given category code for a line chart
    """
    indicator_details = sspi_metadata.indicator_details()
    name_map = {detail["ItemCode"]: detail["ItemName"] for detail in indicator_details}
    active_schema = sspi_item_data.active_schema(name_map=name_map)
    detail = sspi_metadata.get_item_detail(item_code)
    doc_type = detail.get("ItemType", "No Item Type")
    if doc_type == "Indicator":
        item_options = sspi_metadata.indicator_options()
    elif doc_type == "Category":
        item_options = sspi_metadata.category_options()
    elif doc_type == "Pillar":
        item_options = sspi_metadata.pillar_options()
    else:
        item_options = []
    name = detail["ItemName"]
    tree_path = detail.get("TreePath", "")
    tree_path_parts = tree_path.split("/")
    # Build enriched treepath with itemCodes and itemNames for pillars and categories
    enriched_treepath = []
    for itemCode in tree_path_parts:
        if itemCode:  # Skip empty strings from split
            if itemCode.lower() == "sspi":
                # Handle SSPI root case specially
                enriched_treepath.append(
                    {
                        "itemCode": itemCode.lower(),
                        "itemName": "Sustainable and Shared-Prosperity Policy Index",
                    }
                )
            else:
                # Query metadata for other items
                try:
                    item_detail = sspi_metadata.get_item_detail(itemCode)
                    item_name = item_detail.get("ItemName", itemCode.upper())
                    enriched_treepath.append(
                        {"itemCode": itemCode.lower(), "itemName": item_name}
                    )
                except Exception as e:
                    # Fallback to itemCode if metadata lookup fails
                    print(
                        f"Warning: Could not get metadata for itemCode {itemCode}: {e}"
                    )
                    enriched_treepath.append(
                        {"itemCode": itemCode.lower(), "itemName": itemCode.upper()}
                    )
    description = detail.get("Description", "")
    # Get children information for pillars and categories
    children_info = []
    child_type_title = None
    if detail.get("Children"):
        # Determine formal child type title based on parent item type
        if doc_type == "Pillar":
            child_type_title = "Categories"
        elif doc_type == "Category":
            child_type_title = "Indicators"
        elif doc_type.lower() == "sspi":
            child_type_title = "Pillars"
        else:
            child_type_title = "Child Elements"

        for child_code in detail["Children"]:
            try:
                child_detail = sspi_metadata.get_item_detail(child_code)
                children_info.append(
                    {
                        "itemCode": child_code,
                        "itemName": child_detail.get("ItemName", child_code),
                        "itemType": child_detail.get("ItemType", "Unknown"),
                    }
                )
            except Exception as e:
                print(f"Warning: Could not get child metadata for {child_code}: {e}")
                children_info.append(
                    {
                        "itemCode": child_code,
                        "itemName": child_code,
                        "itemType": "Unknown",
                    }
                )

    country_query = request.args.getlist("CountryCode")
    query = {"ICode": item_code}
    if country_query:
        query["CCode"] = {"$in": country_query}
    dynamic_score_data = parse_json(sspi_item_dynamic_line_data.find(query))
    year_labels = list(range(2000, datetime.now().year + 1))  # Default to 2000-present
    chart_title = f"{name} Score"
    group_options = sspi_metadata.country_groups()
    country_group_map = sspi_metadata.country_group_map()
    return jsonify(
        {
            "data": dynamic_score_data,
            "title": chart_title,
            "labels": year_labels,
            "description": description,
            "groupOptions": group_options,
            "countryGroupMap": country_group_map,
            "itemOptions": item_options,
            "itemType": doc_type,
            "itemCode": item_code,
            "itemName": name,
            "tree": active_schema,
            "treepath": enriched_treepath,
            "children": children_info,
            "childTypeTitle": child_type_title,
        }
    )


@dashboard_bp.route("/panel/dataset/<dataset_code>")
def get_dataset_panel_data(dataset_code):
    dataset_details = sspi_metadata.dataset_details();
    dataset_options = []
    for d in dataset_details:
        dataset_options.append({"datasetCode": d.get("DatasetCode"), "datasetName": d.get("DatasetName")})
    dataset_detail = sspi_metadata.get_dataset_detail(dataset_code)
    panel_data_datasets = sspi_panel_data.find({"DatasetCode": dataset_code})
    year_labels = list(range(2000, datetime.now().year + 1))
    group_options = sspi_metadata.country_groups()
    country_group_map = sspi_metadata.country_group_map()
    return jsonify({
        "data": panel_data_datasets,
        "title": f"{dataset_detail["DatasetName"]} ({dataset_detail["DatasetCode"]})",
        "labels": year_labels,
        "description": dataset_detail["Description"],
        "groupOptions": group_options,
        "countryGroupMap": country_group_map,
        "datasetName": dataset_detail["DatasetName"],
        "datasetOptions": dataset_options,
        "yMin": dataset_detail.get("Range", {}).get("yMin"),
        "yMax": dataset_detail.get("Range", {}).get("yMax")
    })


@dashboard_bp.route("/static/radar/<CountryCode>")
def get_static_radar_data(CountryCode):
    radar_data = sspi_static_radar_data.find_one({"CCode": CountryCode})
    return jsonify(radar_data)


@dashboard_bp.route("/dynamic/radar/<CountryCode>")
def get_dynamic_radar_data(CountryCode):
    """
    Get all years of radar data for a country in a single request.
    Uses MongoDB aggregation pipeline for optimal performance.

    Returns:
        {
            "CCode": "USA",
            "minYear": 2000,
            "maxYear": 2023,
            "metadata": {
                "labels": [...],      # Category codes (same for all years)
                "labelMap": {...}     # Category names (same for all years)
            },
            "years": {
                "2000": {
                    "title": "United States (2000)",
                    "datasets": [...],
                    "legendItems": [...],
                    "ranks": [...]
                },
                "2001": {...},
                ...
            }
        }
    """
    # MongoDB aggregation pipeline for efficient data processing
    pipeline = [
        # Match documents for this country
        {"$match": {"CCode": CountryCode}},
        # Sort by year
        {"$sort": {"Year": 1}},
        # Group all documents together
        {
            "$group": {
                "_id": "$CCode",
                "minYear": {"$min": "$Year"},
                "maxYear": {"$max": "$Year"},
                "firstDoc": {"$first": "$$ROOT"},
                "allDocs": {"$push": "$$ROOT"},
            }
        },
        # Project to final shape
        {
            "$project": {
                "_id": 0,
                "CCode": "$_id",
                "minYear": 1,
                "maxYear": 1,
                "metadata": {
                    "labels": "$firstDoc.labels",
                    "labelMap": "$firstDoc.labelMap",
                },
                "years": {
                    "$arrayToObject": {
                        "$map": {
                            "input": "$allDocs",
                            "as": "doc",
                            "in": {
                                "k": {"$toString": "$$doc.Year"},
                                "v": {
                                    "title": "$$doc.title",
                                    "datasets": "$$doc.datasets",
                                    "legendItems": "$$doc.legendItems",
                                    "ranks": {"$ifNull": ["$$doc.ranks", []]},
                                },
                            },
                        }
                    }
                },
            }
        },
    ]

    # Execute aggregation pipeline
    result = list(sspi_dynamic_radar_data.aggregate(pipeline))

    if not result:
        return jsonify({"error": f"No radar data found for country {CountryCode}"}), 404

    return jsonify(result[0])


@dashboard_bp.route("/dynamic/matrix/<country_group>")
def get_dynamic_matrix_data(country_group):
    countries = sspi_metadata.country_group(country_group)
    data = sspi_dynamic_matrix_data.find({"y": {"$in": countries}}, {"_id": 0})
    return jsonify(
        {"data": data, "icodes": sspi_metadata.indicator_codes(), "ccodes": countries}
    )


@dashboard_bp.route("/static/differential/pillar/<pillar_code>")
def get_static_pillar_differential(pillar_code):
    """
    Get the static category data
    """
    base_country = request.args.get("BaseCountry")
    comparison_country = request.args.get("ComparisonCountry")
    if not (base_country and comparison_country):
        return jsonify(
            {"error": "BaseCountry and ComparisonCountry are required URL parameters."}
        ), 400
    if base_country == "undefined" or comparison_country == "undefined":
        return jsonify(
            {"error": "BaseCountry and ComparisonCountry must not be undefined"}
        ), 400
    item_details = sspi_static_metadata.item_details()
    base_country_data = parse_json(
        sspi_static_data_2018.find({"CountryCode": base_country}, {"_id": 0})
    )
    base_sspi = SSPI(item_details, base_country_data, strict_year=False)
    base_pillar = base_sspi.get_item(pillar_code)
    comparison_country_data = parse_json(
        sspi_static_data_2018.find({"CountryCode": comparison_country}, {"_id": 0})
    )
    comparison_sspi = SSPI(item_details, comparison_country_data, strict_year=False)
    comparison_pillar = comparison_sspi.get_item(pillar_code)
    by_category = []
    by_indicator = []
    assert base_pillar is not None
    assert comparison_pillar is not None
    for category_code in base_pillar.category_codes:
        category = base_sspi.get_item(category_code)
        comparison_category = comparison_sspi.get_item(category_code)
        base_score = category.score
        comparison_score = comparison_category.score
        for indicator_code in category.indicator_codes:
            indicator = base_sspi.get_item(indicator_code)
            base_indicator_score = indicator.score
            comparison_indicator = comparison_sspi.get_item(indicator.code)
            comparison_indicator_score = comparison_indicator.score
            by_indicator.append(
                {
                    "IndicatorCode": indicator_code,
                    "BaseScore": base_indicator_score,
                    "ComparisonScore": comparison_indicator_score,
                    "Diff": comparison_indicator_score - base_indicator_score,
                }
            )
        by_category.append(
            {
                "label": category_code,
                "CategoryCode": category_code,
                "CategoryName": category.name,
                "baseScore": base_score,
                "comparisonScore": comparison_score,
                "Diff": comparison_score - base_score,
            }
        )
    by_category.sort(key=lambda x: x["Diff"])
    by_indicator.sort(key=lambda x: x["Diff"])
    base_country_obj = pycountry.countries.get(alpha_3=base_country)
    comparison_country_obj = pycountry.countries.get(alpha_3=comparison_country)
    assert base_country_obj is not None, "Base country not found"
    assert comparison_country_obj is not None, "Comparison country not found"
    return jsonify(
        {
            "labels": [c["CategoryCode"] for c in by_category],
            "datasets": [
                {"label": "Category Differential", "data": by_category},
                {
                    "label": "Indicator Differential",
                    "data": by_indicator,
                    "hidden": True,
                },
            ],
            "title": f"Category Score Difference ({comparison_country} - {base_country})",
            "baseCCode": base_country,
            "baseCName": base_country_obj.name,
            "comparisonCCode": comparison_country,
            "comparisonCName": comparison_country_obj.name,
        }
    )


@dashboard_bp.route("/static/stacked/pillar/<pillar_code>")
def get_static_pillar_stack(pillar_code):
    country_codes = request.args.getlist("CountryCode")
    if not (country_codes):
        return jsonify({"error": "CountryCode URL Parameter not provided"}), 400
    if "undefined" in country_codes:
        return jsonify(
            {"error": "CountryCode URL Parameter must not be undefined"}
        ), 400
    item_details = sspi_static_metadata.item_details()
    datasets = []
    labels = []
    code_map = {}
    pillar_name = ""
    for i, cou in enumerate(country_codes):
        cou_data = sspi_static_data_2018.find({"CountryCode": cou}, {"_id": 0})
        cou_sspi = SSPI(item_details, cou_data, strict_year=False)
        pillar = cou_sspi.get_item(pillar_code)
        assert pillar is not None, f"Pillar {pillar_code} not found for country {cou}"
        if i == 0:
            pillar_name = pillar.name
        country_lookup = pycountry.countries.get(alpha_3=cou)
        assert country_lookup is not None, "Country not found"
        country_name = country_lookup.name
        country_flag = country_lookup.flag
        code_map[cou] = {"name": country_name, "flag": country_flag}
        for j, cat_code in enumerate(pillar.category_codes):
            category = cou_sspi.get_item(cat_code)
            if i == 0:
                labels.append(category.name)
            for ind_code in category.indicator_codes:
                indicator = cou_sspi.get_item(ind_code)
                dataset = {}
                indicator_rank = sspi_static_rank_data.find_one(
                    {"ICode": indicator.code, "CCode": cou}, {"_id": 0}
                )["Rank"]
                data = [None] * len(pillar.category_codes)
                n_indicators = len(category.indicator_codes)
                dataset["CatCode"] = category.code
                dataset["CatName"] = category.name
                dataset["CName"] = category.name
                dataset["stack"] = cou + "-" + category.code
                dataset["CCode"] = cou
                dataset["CName"] = country_name
                dataset["NIndicators"] = n_indicators
                dataset["flag"] = country_flag
                dataset["CCode"] = cou
                dataset["CatCode"] = category.code
                dataset["ICode"] = indicator.code
                dataset["IName"] = indicator.name
                dataset["IRank"] = indicator_rank
                dataset["IScore"] = indicator.score
                dataset["Year"] = indicator.year
                dataset["IScoreScaled"] = indicator.score / n_indicators
                data[j] = indicator.score / n_indicators
                dataset["data"] = data
                datasets.append(dataset)
    return jsonify(
        {
            "labels": labels,
            "datasets": datasets,
            "title": f"{pillar_name} Score Breakdown by Category and Indicator",
            "codeMap": code_map,
        }
    )


@dashboard_bp.route("/static/bar/score/<item_code>")
def get_static_score_item(item_code):
    score_data = sspi_static_rank_data.find({"ICode": item_code})
    item_name = score_data[0]["IName"]
    score_data_formatted = {
        "label": item_name,
        "data": [document["Score"] for document in score_data],
        "info": score_data,
    }
    return jsonify(
        {
            "itemCode": item_code,
            "data": {
                "labels": [
                    document["CName"] + " " + document["CFlag"]
                    for document in score_data
                ],
                "datasets": [score_data_formatted],
            },
            "title": f"{item_name} Score by Country",
            "xTitle": f"{item_name} Score",
        }
    )


@dashboard_bp.route("/static/stacked/sspi")
def get_static_stacked_sspi():
    score_data = sspi_static_stack_data.find_one({}, {"_id": 0})
    return jsonify(
        {"title": "SSPI 2018 Score Breakdown by Pillar", "data": score_data["data"]}
    )


@dashboard_bp.route("/utilities/extrapolate/backward/<int:year>", methods=["POST"])
@csrf.exempt  # API endpoint accessed programmatically (CLI/scripts), not browser forms
def do_backward_extrapolate(year: int):
    """
    Extrapolate backward missing data for a given indicator
    """
    series_id = request.args.getlist("SeriesID")
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed or missing JSON data"}), 400
    if not isinstance(data, list):
        return jsonify({"error": "Data must be a list"}), 400
    if not all(isinstance(item, dict) for item in data):
        return jsonify({"error": "All items in data must be dictionaries"}), 400
    if series_id:
        return parse_json(extrapolate_backward(data, year, series_id=series_id))
    return parse_json(extrapolate_backward(data, year))


@dashboard_bp.route("/utilities/extrapolate/forward/<int:year>", methods=["POST"])
@csrf.exempt  # API endpoint accessed programmatically (CLI/scripts), not browser forms
def do_forward_extrapolate(year: int):
    """
    Extrapolate backward missing data for a given indicator
    """
    series_id = request.args.getlist("SeriesID")
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed or missing JSON data"}), 400
    if not isinstance(data, list):
        return jsonify({"error": "Data must be a list"}), 400
    if not all(isinstance(item, dict) for item in data):
        return jsonify({"error": "All items in data must be dictionaries"}), 400
    if series_id:
        return parse_json(extrapolate_forward(data, year, series_id=series_id))
    return parse_json(extrapolate_forward(data, year))


@dashboard_bp.route("/utilities/interpolate/linear", methods=["POST"])
@csrf.exempt  # API endpoint accessed programmatically (CLI/scripts), not browser forms
def do_linear_interpolate():
    """
    Extrapolate backward missing data for a given indicator
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed or missing JSON data"}), 400
    if not isinstance(data, list):
        return jsonify({"error": "Data must be a list"}), 400
    if not all(isinstance(item, dict) for item in data):
        return jsonify({"error": "All items in data must be dictionaries"}), 400
    return parse_json(interpolate_linear(data))


@dashboard_bp.route("/utilities/panel/levels", methods=["POST"])
@csrf.exempt  # API endpoint accessed programmatically (CLI/scripts), not browser forms
def find_panel_levels():
    """
    Prepare panel data for plotting
    """
    exclude_fields = request.args.getlist("exclude")
    entity_id = request.args.get("country", "")
    time_id = request.args.get("year", "")
    value_id = request.args.get("value", "")
    score_id = request.args.get("score", "")
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed or missing JSON data"}), 400
    if not isinstance(data, list):
        return jsonify({"error": "Data must be a list"}), 400
    if not all(isinstance(item, dict) for item in data):
        return jsonify({"error": "All items in data must be dictionaries"}), 400
    item_level_dict = generate_series_levels(
        data,
        exclude_fields=exclude_fields,
        entity_id=entity_id,
        time_id=time_id,
        value_id=value_id,
        score_id=score_id,
    )
    return parse_json(item_level_dict)


@dashboard_bp.route("/utilities/panel/plot", methods=["POST"])
@csrf.exempt  # API endpoint accessed programmatically (CLI/scripts), not browser forms
def prepare_panel_data():
    """
    Prepare panel data for plotting
    """
    exclude_fields = request.args.getlist("exclude")
    entity_id = request.args.get("country")
    time_id = request.args.get("year")
    value_id = request.args.get("value")
    score_id = request.args.get("score")
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Malformed or missing JSON data"}), 400
    if not isinstance(data, list):
        return jsonify({"error": "Data must be a list"}), 400
    if not all(isinstance(series, dict) for series in data):
        return jsonify({"error": "All series in data must be dictionaries"}), 400

    def prepare_panel_data_iterator(
        data, exclude_fields, entity_id, time_id, value_id, score_id
    ):
        sspi_panel_data.delete_many({})
        # First, validate data consistency
        # Determine which field we're using based on actual data presence
        field_type = None  # Will be 'score', 'value', or None
        # Use the actual field names (with defaults if not specified)
        actual_value_id = value_id if value_id else "Value"
        actual_score_id = score_id if score_id else "Score"

        for obs in data:
            obs_has_score = actual_score_id in obs and obs[actual_score_id] is not None
            obs_has_value = actual_value_id in obs and obs[actual_value_id] is not None

            if obs_has_score and obs_has_value:
                # Single observation has both - this is definitely mixed
                yield "error: Mixed data detected! Some observations have both score and value fields.\n"
                yield "Panel plots require consistent data: use either scores OR values, not both.\n"
                yield "Consider filtering your data to include only one type of measurement.\n"
                return

            if obs_has_score:
                if field_type == "value":
                    # We previously saw values, now seeing scores - mixed data
                    yield "error: Inconsistent data detected! Some observations have scores while others have values.\n"
                    yield "Panel plots require all observations to use the same field type.\n"
                    yield "Filter your data to include only scores or only values.\n"
                    return
                field_type = "score"
            elif obs_has_value:
                if field_type == "score":
                    # We previously saw scores, now seeing values - mixed data
                    yield "error: Inconsistent data detected! Some observations have scores while others have values.\n"
                    yield "Panel plots require all observations to use the same field type.\n"
                    yield "Filter your data to include only scores or only values.\n"
                    return
                field_type = "value"

        series_group_list = generate_series_groups(
            data,
            exclude_fields=exclude_fields,
            entity_id=entity_id,
            time_id=time_id,
            value_id=value_id,
            score_id=score_id,
        )
        if len(series_group_list) > 30:
            yield "error: Too many levels (>30) to display! Run `sspi panel levels` to find levels to filter.\n"
            return jsonify({"error": "Too many series levels to display"})
        yield "================\n"
        count = 1
        for series in series_group_list:
            min_year = 2000
            max_year = datetime.now().year
            label_list = list(range(min_year, max_year + 1))
            identifiers = series["Identifier"]
            identifier_string = json.dumps(identifiers).encode("utf-8")
            id_hash = hashlib.sha1(identifier_string).hexdigest()
            yield "Identifier Hash: " + id_hash + "\n\n"
            for k, v in identifiers.items():
                yield f"{k}: {v}\n"
            yield "================\n"
            for cou, document in series["Datasets"].items():
                document = sorted(document, key=lambda x: x["time_id"])
                group_list = sspi_metadata.get_country_groups(cou)
                year = [None] * len(label_list)
                value = [None] * len(label_list)
                data = [None] * len(label_list)
                score = [None] * len(label_list)
                for doc in document:
                    try:
                        year_index = label_list.index(doc["time_id"])
                    except ValueError:
                        continue
                    year[year_index] = doc["time_id"]
                    value[year_index] = (
                        doc.get("value_id", None) if "value_id" in doc else None
                    )
                    score[year_index] = (
                        doc.get("score_id", None) if "score_id" in doc else None
                    )
                    # Use score if available, otherwise use value
                    if "score_id" in doc and doc.get("score_id") is not None:
                        data[year_index] = doc.get("score_id")
                    elif "value_id" in doc and doc.get("value_id") is not None:
                        data[year_index] = doc.get("value_id")
                    else:
                        data[year_index] = None
                document = {
                    "SeriesIdentifier": id_hash,
                    "SeriesOrder": count,
                    "CCode": cou,
                    "CName": country_code_to_name(cou),
                    "CGroup": group_list,
                    "pinned": False,
                    "hidden": "SSPI67" not in group_list,
                    "label": f"{cou} - {country_code_to_name(cou)}",
                    "year": year,
                    "minYear": min_year,
                    "maxYear": max_year,
                    "data": data,
                    "value": value,
                }
                if any([s is not None for s in score]):
                    document["score"] = score
                # Skip if both value and score arrays are all None
                if all([v is None for v in value]) and all([s is None for s in score]):
                    yield f"Skipping {cou} as no data available.\n"
                    continue
                document["Identifiers"] = identifiers
                sspi_panel_data.insert_one(document)
            count += 1

    return Response(
        prepare_panel_data_iterator(
            data, exclude_fields, entity_id, time_id, value_id, score_id
        ),
        mimetype="text/event-stream",
    )


@dashboard_bp.route("/view/panel")
def view_panel_plots():
    panel_data = sspi_panel_data.distinct("SeriesIdentifier")
    return render_template("panel-utility.html", series_id_list=panel_data)


@dashboard_bp.route("/panel/series/<series_id>")
def get_series_panel_plot(series_id):
    """
    Get the panel plot for a given panel id
    """

    def make_title(identifiers, series_id):
        if "SeriesCode" in identifiers.keys():
            return f"{identifiers['ItemCode']} (Series Hash: {series_id})"
        if "DatasetCode" in identifiers.keys():
            return f"{identifiers['DatasetCode']} (Series Hash: {series_id})"
        if "IndicatorCode" in identifiers.keys():
            return f"{identifiers['IndicatorCode']} (Series Hash: {series_id})"
        return f"Panel Plot (Series Hash: {series_id})"

    panel_data = sspi_panel_data.find({"SeriesIdentifier": series_id}, {"_id": 0})
    min_year = panel_data[0]["minYear"]
    max_year = panel_data[0]["maxYear"]
    has_score = panel_data[0].get("score", None) is not None
    identifiers = panel_data[0]["Identifiers"]
    year_labels = [year for year in range(min_year, max_year + 1)]
    group_options = sspi_metadata.country_groups()
    yMin = 0
    yMax = 1
    print("Panel Data:", panel_data)
    for doc in panel_data:
        values = [d for d in doc.get("value", []) if d is not None]
        if values:
            yMin = min(yMin, min(values))
            yMax = max(yMax, max(values))
    return jsonify(
        {
            "data": panel_data,
            "title": {
                "display": True,
                "text": make_title(identifiers, series_id),
                "font": {"size": 18},
                "color": "#ccc",
                "align": "start",
            },
            "labels": year_labels,
            "description": identifiers,
            "groupOptions": group_options,
            "hasScore": has_score,
            "yMin": yMin,
            "yMax": yMax,
        }
    )


@dashboard_bp.route("/utilities/coverage", methods=["GET"])
def coverage():
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).combined_coverage
    return parse_json(coverage)


@dashboard_bp.route("/utilities/coverage/complete", methods=["GET"])
def coverage_complete():
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).complete()
    return parse_json(coverage)


@dashboard_bp.route("/utilities/coverage/incomplete", methods=["GET"])
def coverage_incomplete():
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).incomplete()
    return parse_json(coverage)


@dashboard_bp.route("/utilities/coverage/unimplemented", methods=["GET"])
def coverage_unimplemented():
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).unimplemented()
    return parse_json(coverage)


@dashboard_bp.route(
    "/utilities/coverage/report/indicator/<IndicatorCode>", methods=["GET"]
)
def coverage_indicator(IndicatorCode):
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).indicator_report(IndicatorCode)
    return coverage


@dashboard_bp.route("/utilities/coverage/report/country/<CountryCode>", methods=["GET"])
def coverage_country(CountryCode):
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).country_report(CountryCode)
    return coverage


@dashboard_bp.route("/country/coverage/matrix/<country_code>")
def country_coverage_matrix_data(country_code):
    """
    Get coverage matrix data for a single country showing observed vs imputed vs missing.
    Returns data suitable for rendering a matrix chart with indicators on y-axis and years on x-axis.
    Only includes indicators from the active schema (those with complete coverage used in SSPI computation).

    Query parameters:
        view: 'indicator' (default) or 'dataset'
    """
    min_year = 2000
    max_year = 2023
    years = list(range(min_year, max_year + 1))
    country_code = country_code.upper()
    view = request.args.get("view", "indicator")

    # Get only indicators with complete coverage (the active schema)
    coverage = DataCoverage(min_year, max_year, "SSPI67")
    indicator_codes = coverage.complete()

    # Get indicator details for name mapping
    indicator_details = sspi_metadata.indicator_details()
    indicator_name_map = {d["ItemCode"]: d["ItemName"] for d in indicator_details}

    # Get dataset dependencies for active schema
    dataset_deps = sspi_metadata.get_active_schema_dataset_dependencies(indicator_codes)
    indicator_to_datasets = dataset_deps["indicatorToDatasets"]

    # Get dataset details for name mapping
    dataset_details = sspi_metadata.dataset_details()
    dataset_name_map = {d["DatasetCode"]: d["DatasetName"] for d in dataset_details}

    # Build indicator hierarchy for pillar/category grouping
    item_details = sspi_metadata.item_details()
    indicator_hierarchy = {}
    for item in item_details:
        if item.get("ItemType") == "Indicator":
            indicator_hierarchy[item["ItemCode"]] = {
                "pillarCode": item.get("PillarCode", ""),
                "categoryCode": item.get("CategoryCode", "")
            }

    # Query observed data for this country (indicator-level)
    observed_pipeline = [
        {"$match": {
            "CountryCode": country_code,
            "IndicatorCode": {"$in": indicator_codes},
            "Year": {"$gte": min_year, "$lte": max_year}
        }},
        {"$group": {
            "_id": {"IndicatorCode": "$IndicatorCode", "Year": "$Year"},
            "score": {"$first": "$Score"}
        }},
        {"$project": {
            "_id": 0,
            "IndicatorCode": "$_id.IndicatorCode",
            "Year": "$_id.Year",
            "score": 1
        }}
    ]
    observed_results = sspi_indicator_data.aggregate(observed_pipeline)
    observed_set = {(r["IndicatorCode"], r["Year"]): r["score"] for r in observed_results}

    # Query imputed data with dataset-level breakdown
    imputed_pipeline = [
        {"$match": {
            "CountryCode": country_code,
            "IndicatorCode": {"$in": indicator_codes},
            "Year": {"$gte": min_year, "$lte": max_year}
        }},
        {"$project": {
            "_id": 0,
            "IndicatorCode": 1,
            "Year": 1,
            "Score": 1,
            "Datasets": 1
        }}
    ]
    imputed_results = list(sspi_imputed_data.aggregate(imputed_pipeline))

    # Build lookup for imputed data: (indicator, year) -> {score, datasets}
    imputed_set = {}
    for r in imputed_results:
        key = (r["IndicatorCode"], r["Year"])
        datasets_info = {}
        observed_ds_count = 0
        imputed_ds_count = 0

        for ds in r.get("Datasets", []):
            ds_code = ds.get("DatasetCode")
            if not ds_code:
                continue
            is_imputed = ds.get("Imputed", False)
            ds_info = {
                "status": "imputed" if is_imputed else "observed",
                "value": ds.get("Value")
            }
            # Include imputation method if present
            if is_imputed and ds.get("ImputationMethod"):
                ds_info["imputationMethod"] = ds.get("ImputationMethod")
            datasets_info[ds_code] = ds_info
            if is_imputed:
                imputed_ds_count += 1
            else:
                observed_ds_count += 1

        imputed_set[key] = {
            "score": r.get("Score"),
            "datasetBreakdown": datasets_info,
            "observedDatasets": observed_ds_count,
            "imputedDatasets": imputed_ds_count,
            "totalDatasets": observed_ds_count + imputed_ds_count
        }

    # Get country details
    country_detail = sspi_metadata.get_country_detail(country_code)

    if view == "dataset":
        return _build_dataset_view_response(
            country_code, years, indicator_codes, indicator_name_map,
            dataset_name_map, indicator_to_datasets, indicator_hierarchy,
            observed_set, imputed_set, country_detail
        )
    else:
        return _build_indicator_view_response(
            country_code, years, indicator_codes, indicator_name_map,
            indicator_to_datasets, indicator_hierarchy,
            observed_set, imputed_set, country_detail
        )


def _build_indicator_view_response(
    country_code, years, indicator_codes, indicator_name_map,
    indicator_to_datasets, indicator_hierarchy,
    observed_set, imputed_set, country_detail
):
    """Build indicator-level coverage matrix response with dataset breakdown."""
    data = []
    observed_count = 0
    imputed_count = 0

    for indicator_code in indicator_codes:
        hierarchy = indicator_hierarchy.get(indicator_code, {})
        expected_datasets = indicator_to_datasets.get(indicator_code, [])

        for year in years:
            key = (indicator_code, year)
            cell = {
                "x": year,
                "y": indicator_code,
                "yName": indicator_name_map.get(indicator_code, indicator_code),
                "pillarCode": hierarchy.get("pillarCode", ""),
                "categoryCode": hierarchy.get("categoryCode", ""),
                "totalDatasets": len(expected_datasets)
            }

            if key in observed_set:
                # All observed (from sspi_indicator_data means no imputation)
                cell["v"] = "observed"
                cell["score"] = observed_set[key]
                cell["observedDatasets"] = len(expected_datasets)
                cell["imputedDatasets"] = 0
                cell["datasetBreakdown"] = {
                    ds: {"status": "observed"} for ds in expected_datasets
                }
                observed_count += 1
            elif key in imputed_set:
                imputed_info = imputed_set[key]
                cell["score"] = imputed_info["score"]
                cell["datasetBreakdown"] = imputed_info["datasetBreakdown"]
                cell["observedDatasets"] = imputed_info["observedDatasets"]
                cell["imputedDatasets"] = imputed_info["imputedDatasets"]

                # If any dataset is imputed, show as imputed
                if imputed_info["imputedDatasets"] > 0:
                    cell["v"] = "imputed"
                    imputed_count += 1
                else:
                    cell["v"] = "observed"
                    observed_count += 1
            else:
                # Data should never be missing - all indicator/year combinations
                # should exist in either observed or imputed data
                raise AssertionError(
                    f"Missing data for {indicator_code} in {year} for {country_code}. "
                    "All data should be present in sspi_indicator_data or sspi_imputed_data."
                )

            data.append(cell)

    total_cells = len(indicator_codes) * len(years)

    return jsonify({
        "view": "indicator",
        "data": data,
        "summary": {
            "totalCells": total_cells,
            "observedCount": observed_count,
            "imputedCount": imputed_count,
            "observedPercent": round(observed_count / total_cells * 100, 1) if total_cells > 0 else 0,
            "imputedPercent": round(imputed_count / total_cells * 100, 1) if total_cells > 0 else 0
        },
        "indicators": indicator_codes,
        "indicatorNames": indicator_name_map,
        "years": years,
        "countryCode": country_code,
        "countryName": country_detail.get("Country", country_code) if country_detail else country_code,
        "countryFlag": country_detail.get("Flag", "") if country_detail else ""
    })


def _build_dataset_view_response(
    country_code, years, indicator_codes, indicator_name_map,
    dataset_name_map, indicator_to_datasets, indicator_hierarchy,
    observed_set, imputed_set, country_detail
):
    """Build dataset-level coverage matrix response with grouped structure."""
    data = []
    observed_count = 0
    imputed_count = 0

    # Build y-axis labels with indicator headers and datasets
    y_labels = []
    dataset_list = []  # flat list for y-axis of chart

    for indicator_code in indicator_codes:
        # Add indicator as group header
        y_labels.append({
            "type": "indicator",
            "code": indicator_code,
            "name": indicator_name_map.get(indicator_code, indicator_code)
        })

        # Add datasets under this indicator
        datasets = indicator_to_datasets.get(indicator_code, [])
        for ds_code in datasets:
            compound_key = f"{indicator_code}/{ds_code}"
            dataset_list.append(compound_key)
            y_labels.append({
                "type": "dataset",
                "code": ds_code,
                "name": dataset_name_map.get(ds_code, ds_code),
                "parent": indicator_code,
                "compoundKey": compound_key
            })

    # Build data cells for each dataset-year combination
    for indicator_code in indicator_codes:
        hierarchy = indicator_hierarchy.get(indicator_code, {})
        datasets = indicator_to_datasets.get(indicator_code, [])

        for ds_code in datasets:
            compound_key = f"{indicator_code}/{ds_code}"

            for year in years:
                key = (indicator_code, year)
                cell = {
                    "x": year,
                    "y": compound_key,
                    "yIndicator": indicator_code,
                    "yIndicatorName": indicator_name_map.get(indicator_code, indicator_code),
                    "yDataset": ds_code,
                    "yDatasetName": dataset_name_map.get(ds_code, ds_code),
                    "pillarCode": hierarchy.get("pillarCode", ""),
                    "categoryCode": hierarchy.get("categoryCode", "")
                }

                if key in observed_set:
                    # From sspi_indicator_data - all datasets observed
                    cell["v"] = "observed"
                    cell["value"] = None  # No per-dataset value in observed case
                    observed_count += 1
                elif key in imputed_set:
                    imputed_info = imputed_set[key]
                    ds_breakdown = imputed_info.get("datasetBreakdown", {})
                    ds_info = ds_breakdown.get(ds_code, {})

                    if ds_info:
                        status = ds_info.get("status")
                        # Data should only be 'observed' or 'imputed', never missing
                        assert status in ("observed", "imputed"), (
                            f"Invalid status '{status}' for dataset {ds_code} in {indicator_code} "
                            f"for year {year}, country {country_code}. Status must be 'observed' or 'imputed'."
                        )
                        cell["v"] = status
                        cell["value"] = ds_info.get("value")
                        # Include imputation method if present
                        if ds_info.get("imputationMethod"):
                            cell["imputationMethod"] = ds_info.get("imputationMethod")
                        if status == "observed":
                            observed_count += 1
                        else:
                            imputed_count += 1
                    else:
                        # Dataset info should always be present in imputed data
                        raise AssertionError(
                            f"Missing dataset info for {ds_code} in {indicator_code} "
                            f"for year {year}, country {country_code}. "
                            "All datasets should have info in sspi_imputed_data."
                        )
                else:
                    # Data should never be missing - all indicator/year combinations
                    # should exist in either observed or imputed data
                    raise AssertionError(
                        f"Missing data for {indicator_code}/{ds_code} in {year} for {country_code}. "
                        "All data should be present in sspi_indicator_data or sspi_imputed_data."
                    )

                data.append(cell)

    total_cells = len(dataset_list) * len(years)

    return jsonify({
        "view": "dataset",
        "data": data,
        "summary": {
            "totalCells": total_cells,
            "observedCount": observed_count,
            "imputedCount": imputed_count,
            "observedPercent": round(observed_count / total_cells * 100, 1) if total_cells > 0 else 0,
            "imputedPercent": round(imputed_count / total_cells * 100, 1) if total_cells > 0 else 0
        },
        "indicators": indicator_codes,
        "indicatorNames": indicator_name_map,
        "indicatorToDatasets": indicator_to_datasets,
        "datasets": dataset_list,
        "datasetNames": dataset_name_map,
        "yLabels": y_labels,
        "years": years,
        "countryCode": country_code,
        "countryName": country_detail.get("Country", country_code) if country_detail else country_code,
        "countryFlag": country_detail.get("Flag", "") if country_detail else ""
    })


@dashboard_bp.route("/utilities/coverage/schema", methods=["GET"])
def active_schema():
    group = request.args.get("CountryGroup", "SSPI67")
    sample_country = sspi_metadata.country_group(group)[0]
    indicator_details = sspi_metadata.indicator_details()
    name_map = {
        detail["IndicatorCode"]: detail["Indicator"] for detail in indicator_details
    }
    active_schema = sspi_item_data.active_schema(
        sample_country=sample_country, name_map=name_map
    )
    return jsonify(active_schema)


@dashboard_bp.route("/country/dynamic/stack/<country_code>/<root_item_code>")
def dynamic_stack_data(country_code, root_item_code):
    """
    Get the dynamic data for the given country code and root item code
    """
    root_item_detail = sspi_metadata.get_item_detail(root_item_code)
    child_items = sspi_metadata.get_child_details(root_item_code)
    country_detail = sspi_metadata.get_country_detail(country_code)
    child_codes = [child["Metadata"]["ItemCode"] for child in child_items]
    stack_div = len(child_codes)
    mongo_query = {
        "CCode": country_code,
        "ICode": {"$in": child_codes + [root_item_code]},
    }
    data = sspi_item_dynamic_line_data.find(mongo_query)

    # Define explicit pillar order for consistent stacking
    # In stacked charts, last dataset appears at TOP of stack
    # So we reverse: PG (bottom), MS (middle), SUS (top)
    pillar_order = {"PG": 0, "MS": 1, "SUS": 2}

    def sort_key(doc):
        item_code = doc["Detail"]["ItemCode"]
        # Root item (SSPI) should be first (hidden anyway)
        if item_code == root_item_code:
            return -1
        # Use pillar order if available, otherwise use position in child_codes
        return pillar_order.get(item_code, child_codes.index(item_code) + 100)

    data.sort(key=sort_key)
    year_labels = list(range(2000, datetime.now().year + 1))
    for document in data:
        if document["ICode"] == root_item_code:
            document["hidden"] = True
        else:
            document["divisor"] = stack_div
            document["data"] = [s / stack_div for s in document["score"]]
            document["fill"] = "stack"
    return parse_json(
        {
            "data": data,
            "title": f"{country_detail['Flag']} {country_detail['Country']} {root_item_detail['ItemType']} Score Breakdown",
            "labels": year_labels,
            "itemType": root_item_detail["DocumentType"][0:-6].lower(),
            "hasScore": True,
            "yMin": 0,
            "yMax": 1,
        }
    )


def build_indicators_data():
    """
    Build a complete hierarchical data structure for the indicators table page.

    Returns a structured representation of pillars -> categories -> indicators -> datasets
    suitable for frontend display.

    Returns:
        dict: Organized data structure with pillars, categories, indicators, and datasets
    """
    try:
        all_items = sspi_metadata.item_details()
        source_organization_lookup = {
            source["OrganizationCode"]: source
            for source in sspi_metadata.organization_details()
        }
        if not all_items:
            return {"pillars": [], "error": "No metadata items found"}
        all_datasets = sspi_metadata.dataset_details()
        datasets_by_code = {dataset["DatasetCode"]: dataset for dataset in all_datasets}
        items_by_type = {"SSPI": [], "Pillar": [], "Category": [], "Indicator": []}
        items_by_code = {}
        for item in all_items:
            item_type = item.get("ItemType", "Unknown")
            item_code = item.get("ItemCode", "")
            if item_type in items_by_type:
                items_by_type[item_type].append(item)
            if item_code:
                items_by_code[item_code] = item
        pillars = []
        sorted_pillars = sorted(
            items_by_type["Pillar"],
            key=lambda x: (x.get("ItemOrder", 999), x.get("ItemCode", "")),
        )
        for pillar_item in sorted_pillars:
            pillar_code = pillar_item.get("ItemCode", "")
            pillar_data = {
                "pillar_code": pillar_code,
                "pillar_name": pillar_item.get("ItemName", pillar_code),
                "pillar_description": pillar_item.get("Description", ""),
                "categories": [],
            }
            category_codes = pillar_item.get("CategoryCodes", [])
            for category_code in category_codes:
                category_item = items_by_code.get(category_code)
                if not category_item:
                    continue
                category_data = {
                    "category_code": category_code,
                    "category_name": category_item.get("ItemName", category_code),
                    "category_description": category_item.get("Description", ""),
                    "indicators": [],
                }
                indicator_codes = category_item.get("IndicatorCodes", [])
                for indicator_code in indicator_codes:
                    indicator_item = items_by_code.get(indicator_code)
                    if not indicator_item:
                        continue
                    dataset_codes = indicator_item.get("DatasetCodes", [])
                    datasets = []
                    for dataset_code in dataset_codes:
                        dataset = datasets_by_code.get(dataset_code)
                        if dataset:
                            org_code = dataset.get("Source", {}).get("OrganizationCode", "")
                            print(org_code)
                            org_detail = source_organization_lookup.get(org_code)
                            print(org_detail)
                            datasets.append(
                                {
                                    "dataset_code": dataset_code,
                                    "dataset_name": dataset.get(
                                        "DatasetName", dataset_code
                                    ),
                                    "description": dataset.get("Description", ""),
                                    "source": dataset.get("Source", {}),
                                    "organization_detail": org_detail,
                                    "organization_code": dataset.get("Source", {}).get(
                                        "OrganizationCode", ""
                                    ),
                                    "organization_name": dataset.get("Source", {}).get(
                                        "OrganizationName", ""
                                    ),
                                }
                            )
                    indicator_data = {
                        "indicator_code": indicator_code,
                        "indicator_name": indicator_item.get(
                            "ItemName", indicator_code
                        ),
                        "description": indicator_item.get("Description", ""),
                        "datasets": datasets,
                        "dataset_codes": dataset_codes,
                        "policy": indicator_item.get("Policy", ""),
                        "score_function": indicator_item.get("ScoreFunction", ""),
                        "lower_goalpost": indicator_item.get("LowerGoalpost"),
                        "upper_goalpost": indicator_item.get("UpperGoalpost"),
                        "inverted": indicator_item.get("Inverted", False),
                    }
                    category_data["indicators"].append(indicator_data)
                pillar_data["categories"].append(category_data)
            pillars.append(pillar_data)
        return {
            "pillars": pillars,
            "stats": {
                "total_pillars": len(pillars),
                "total_categories": sum(len(p["categories"]) for p in pillars),
                "total_indicators": sum(
                    len(c["indicators"]) for p in pillars for c in p["categories"]
                ),
                "total_datasets": len(datasets_by_code),
            },
        }
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error building indicators data: {str(e)}")
        return {"pillars": [], "error": f"Error building indicators data: {str(e)}"}


def build_download_tree_structure():
    """
    Build hierarchical tree structure for download form indicator selector.
    Similar to build_indicators_data() but simplified for form use.

    Returns:
        dict: Tree structure with SSPI -> Pillars -> Categories -> Indicators
    """
    try:
        all_items = sspi_metadata.item_details()
        if not all_items:
            return {"error": "No metadata items found"}
        items_by_type = {"SSPI": [], "Pillar": [], "Category": [], "Indicator": []}
        items_by_code = {}
        for item in all_items:
            item_type = item.get("ItemType", "Unknown")
            item_code = item.get("ItemCode", "")
            if item_type in items_by_type:
                items_by_type[item_type].append(item)
            if item_code:
                items_by_code[item_code] = item
        sspi_items = items_by_type.get("SSPI", [])
        if not sspi_items:
            return {"error": "No SSPI root item found"}
        sspi_item = sspi_items[0]  # Should only be one SSPI item

        def build_node(item, level=0):
            node = {
                "itemCode": item.get("ItemCode", ""),
                "itemName": item.get("ItemName", item.get("ItemCode", "")),
                "itemType": item.get("ItemType", "Unknown"),
                "level": level,
                "children": [],
            }
            children_codes = item.get("Children", [])
            for child_code in children_codes:
                child_item = items_by_code.get(child_code)
                if child_item:
                    child_node = build_node(child_item, level + 1)
                    node["children"].append(child_node)
            node["children"].sort(
                key=lambda x: (
                    items_by_code.get(x["itemCode"], {}).get("ItemOrder", 999),
                    x["itemName"],
                )
            )
            return node

        tree_structure = build_node(sspi_item)
        return tree_structure

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error building download tree structure: {str(e)}")
        return {"error": f"Error building tree structure: {str(e)}"}


def build_indicators_data_static():
    """
    Build a complete hierarchical data structure for the indicators table page.

    Returns a structured representation of pillars -> categories -> indicators -> datasets
    suitable for frontend display.

    Returns:
        dict: Organized data structure with pillars, categories, indicators, and datasets
    """
    try:
        all_items = sspi_static_metadata.item_details()
        if not all_items:
            return {"pillars": [], "error": "No metadata items found"}
        items_by_type = {"SSPI": [], "Pillar": [], "Category": [], "Indicator": []}
        items_by_code = {}
        for item in all_items:
            item_type = item.get("ItemType", "Unknown")
            item_code = item.get("ItemCode", "")
            if item_type in items_by_type:
                items_by_type[item_type].append(item)
            if item_code:
                items_by_code[item_code] = item
        pillars = []

        def pillar_order(pillar_doc):
            pillar_code = pillar_doc.get("ItemCode")
            match pillar_code:
                case "SUS":
                    return 0
                case "MS":
                    return 1
                case "PG":
                    return 2
                case _:
                    return -1

        def category_order(category_code):
            match category_code:
                case "ECO":
                    return 0
                case "LND":
                    return 1
                case "NRG":
                    return 2
                case "GHG":
                    return 3
                case "WST":
                    return 4
                case "WEN":
                    return 5
                case "WWB":
                    return 6
                case "TAX":
                    return 7
                case "FIN":
                    return 8
                case "NEQ":
                    return 9
                case "EDU":
                    return 10
                case "HLC":
                    return 11
                case "INF":
                    return 12
                case "RTS":
                    return 13
                case "SAF":
                    return 14
                case "GLB":
                    return 15
                case _:
                    return -1

        sorted_pillars = sorted(items_by_type["Pillar"], key=pillar_order)
        for pillar_item in sorted_pillars:
            pillar_code = pillar_item.get("ItemCode", "")
            pillar_data = {
                "pillar_code": pillar_code,
                "pillar_name": pillar_item.get("ItemName", pillar_code),
                "pillar_description": pillar_item.get("Description", ""),
                "categories": [],
            }
            category_codes = pillar_item.get("CategoryCodes", [])
            sorted_categories = sorted(category_codes, key=category_order)
            for category_code in sorted_categories:
                category_item = items_by_code.get(category_code)
                if not category_item:
                    continue
                category_data = {
                    "category_code": category_code,
                    "category_name": category_item.get("ItemName", category_code),
                    "category_description": category_item.get("Description", ""),
                    "indicators": [],
                }
                indicator_codes = category_item.get("IndicatorCodes", [])
                for indicator_code in indicator_codes:
                    indicator_item = items_by_code.get(indicator_code)
                    if not indicator_item:
                        continue
                    indicator_data = {
                        "indicator_code": indicator_code,
                        "indicator_name": indicator_item.get(
                            "ItemName", indicator_code
                        ),
                        "goalpost_string": indicator_item.get("GoalpostString", ""),
                        "description": indicator_item.get("Description", ""),
                        "lower_goalpost": indicator_item.get("LowerGoalpost"),
                        "upper_goalpost": indicator_item.get("UpperGoalpost"),
                        "policy": indicator_item.get("Policy", ""),
                        "self": indicator_item,
                        "inverted": indicator_item.get("Inverted", False),
                        "requires_inversion_message": False
                    }
                    if not indicator_data["lower_goalpost"] or not indicator_data["upper_goalpost"]:
                        gp_string = indicator_data["goalpost_string"]
                        result = re.match(r"^\s*\(([0-9]+),\s?([0-9]+)\)\s*$", gp_string)
                        if result:
                            lg = result.group(1)
                            ug = result.group(2) 
                            if "V" in gp_string:
                                swap_var = lg
                                lg = ug
                                ug = swap_var 
                            if lg:
                                indicator_data["lower_goalpost"] = lg
                            if ug:
                                indicator_data["upper_goalpost"] = ug
                        elif "V" in gp_string:
                            indicator_data["requires_inversion_message"] = True
                    category_data["indicators"].append(indicator_data)
                pillar_data["categories"].append(category_data)
            pillars.append(pillar_data)
        return {
            "pillars": pillars,
            "stats": {
                "total_pillars": len(pillars),
                "total_categories": sum(len(p["categories"]) for p in pillars),
                "total_indicators": sum(
                    len(c["indicators"]) for p in pillars for c in p["categories"]
                ),
            },
        }
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error building indicators data: {str(e)}")
        return {"pillars": [], "error": f"Error building indicators data: {str(e)}"}


@dashboard_bp.route("/item/coverage/matrix/<ItemCode>/<CountryGroup>")
def item_coverage_data(ItemCode, CountryGroup):
    coverage = DataCoverage(2000, 2023, CountryGroup)
    n_squares = (coverage.max_year - coverage.min_year) * len(coverage.country_codes)
    data = coverage.item_coverage_data(ItemCode)
    complete_coverage = len([d for d in data if d["v"] == d["vComplete"]])
    one_missing = len([d for d in data if d["v"] == d["vComplete"] - 1])
    two_or_more_missing = len([d for d in data if d["v"] < d["vComplete"] - 1])
    no_observations = n_squares - complete_coverage - one_missing - two_or_more_missing
    return {
        "summary": [
            f"Complete Coverage: {complete_coverage} / {n_squares} observations ({complete_coverage / n_squares:.2%})",
            f"1+ Observation Missing: {one_missing} / {n_squares} observations ({one_missing / n_squares:.2%})",
            f"2+ Observations Missing: {two_or_more_missing} observations ({two_or_more_missing / n_squares:.2%})",
            f"No Observations: {no_observations} observations ({no_observations / n_squares:.2%})",
        ],
        "data": data,
        "title": f"Coverage for {ItemCode}",
        "labels": sorted(list(set(d["y"] for d in data))),
        "itemCode": ItemCode,
        "years": list(range(2000, 2024)),
        "ccodes": sorted(list(set(d["y"] for d in data))),
    }


@dashboard_bp.route("/globe")
def globe_data():
    return sspi_globe_data.find({})[0]


def fetch_series(series_code):
    """
    Determine series type and fetch from appropriate collection.

    Args:
        series_code (str): Code for indicator, item (pillar/category/SSPI), or dataset

    Returns:
        tuple: (data, metadata) where:
            - data: list of country documents with years/scores/values
            - metadata: dict with series info (code, name, type, field)

    Raises:
        ValueError: If series_code not found in any collection
    """
    # Check if it's an item (indicator, pillar, category, SSPI)
    try:
        item_detail = sspi_metadata.get_item_detail(series_code)
        if item_detail:
            item_type = item_detail.get("ItemType")

            if item_type == "Indicator":
                # Fetch from indicator collection
                data = parse_json(
                    sspi_indicator_dynamic_line_data.find({"ICode": series_code})
                )
                return data, {
                    "code": series_code,
                    "name": item_detail.get("ItemName", series_code),
                    "type": "Indicator",
                    "field": "score"
                }

            elif item_type in ["Pillar", "Category", "SSPI"]:
                # Fetch from item collection
                data = parse_json(
                    sspi_item_dynamic_line_data.find({"ICode": series_code})
                )
                return data, {
                    "code": series_code,
                    "name": item_detail.get("ItemName", series_code),
                    "type": item_type,
                    "field": "score"
                }
    except Exception:
        pass  # Try dataset next

    # Check if it's a dataset
    try:
        dataset_detail = sspi_metadata.get_dataset_detail(series_code)
        if dataset_detail:
            # Fetch from panel data
            data = parse_json(
                sspi_panel_data.find({"DatasetCode": series_code})
            )
            return data, {
                "code": series_code,
                "name": dataset_detail.get("DatasetName", series_code),
                "type": "Dataset",
                "field": "value"
            }
    except Exception:
        pass

    # Not found
    raise ValueError(f"Series '{series_code}' not found in metadata or dataset collections")


def merge_series_data(data_x, data_y):
    """
    Merge two series datasets by country code.

    Args:
        data_x: List of country documents for series X
        data_y: List of country documents for series Y

    Returns:
        List of merged country documents with both xValues and yValues
    """
    # Build lookup for series Y
    y_lookup = {doc["CCode"]: doc for doc in data_y}

    merged = []
    for x_doc in data_x:
        country_code = x_doc["CCode"]

        # Skip if no matching Y data
        if country_code not in y_lookup:
            continue

        y_doc = y_lookup[country_code]

        # Extract values from appropriate field (score or value or data)
        x_values = x_doc.get("score") or x_doc.get("value") or x_doc.get("data", [])
        y_values = y_doc.get("score") or y_doc.get("value") or y_doc.get("data", [])

        # Merge into single document
        merged.append({
            "CCode": country_code,
            "CName": x_doc.get("CName", country_code),
            "CFlag": x_doc.get("CFlag", ""),
            "CGroup": x_doc.get("CGroup", []),
            "years": x_doc.get("years", []),
            "xValues": x_values,
            "yValues": y_values
        })

    return merged


@dashboard_bp.route("/correlation/<series_x>/<series_y>", methods=["GET"])
def get_series_correlation_data(series_x, series_y):
    """
    Fetch correlation data for two series using pre-finalized collections.

    Series can be:
    - Indicators (from sspi_indicator_dynamic_line_data)
    - Items (Pillars/Categories/SSPI from sspi_item_dynamic_line_data)
    - Datasets (from sspi_panel_data)

    Args:
        series_x (str): First series code
        series_y (str): Second series code

    Returns:
        JSON with complete time series for both variables across all countries
    """
    try:
        series_x_data, series_x_meta = fetch_series(series_x)
        series_y_data, series_y_meta = fetch_series(series_y)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    # Merge by country code
    merged_data = merge_series_data(series_x_data, series_y_data)

    if not merged_data:
        return jsonify({
            "error": f"No common countries between {series_x} and {series_y}"
        }), 400

    # Get metadata
    group_options = sspi_metadata.country_groups()
    country_group_map = sspi_metadata.country_group_map()

    return jsonify({
        "seriesX": series_x_meta,
        "seriesY": series_y_meta,
        "data": merged_data,
        "years": list(range(2000, datetime.now().year + 1)),
        "groupOptions": group_options,
        "countryGroupMap": country_group_map
    })


@dashboard_bp.route("/series-options")
def get_series_options():
    """
    Get all available series for correlation analysis.

    Returns:
        JSON with series grouped by type (Index, Pillars, Categories, Indicators, Datasets)
    """
    series_options = {
        'Pillars': [],
        'Categories': [],
        'Indicators': [],
        'Datasets': []
    }

    # Get all items (pillars, categories, indicators)
    items = sspi_metadata.item_details()
    for item in items:
        item_type = item.get('ItemType')
        item_code = item.get('ItemCode')
        item_name = item.get('ItemName')

        if item_type == 'Pillar':
            series_options['Pillars'].append({
                'code': item_code,
                'name': item_name,
                'type': item_type
            })
        elif item_type == 'Category':
            series_options['Categories'].append({
                'code': item_code,
                'name': item_name,
                'type': item_type
            })
        elif item_type == 'Indicator':
            series_options['Indicators'].append({
                'code': item_code,
                'name': item_name,
                'type': item_type
            })

    # Get all datasets
    datasets = sspi_metadata.dataset_details()
    for dataset in datasets:
        series_options['Datasets'].append({
            'code': dataset.get('DatasetCode'),
            'name': dataset.get('DatasetName'),
            'type': 'Dataset'
        })

    # Add SSPI to the options (it's the root item)
    series_options['Index'] = [
        {
            'code': 'SSPI',
            'name': 'Sustainable and Shared-Prosperity Policy Index',
            'type': 'SSPI'
        }
    ]

    return jsonify(series_options)


@dashboard_bp.route("/fast_score")
def fast_score():
    items = sspi_metadata.item_details()
    country_codes = sspi_metadata.country_group("SSPI67")
    country_codes.sort()
    coverage = DataCoverage(2000, 2023, "SSPI67", countries=country_codes)
    complete_indicators = coverage.complete()
    details_for_scoring = sspi_metadata.item_details(indicator_filter=complete_indicators)
    print(details_for_scoring)
    indicator_order_map = {d["ItemCode"]: d["ItemOrder"] for d in details_for_scoring if d["ItemType"] == "Indicator"}
    order_map_literal = {"$literal": indicator_order_map}
    min_year = 2000
    max_year = 2023
    order_map_literal = {"$literal": indicator_order_map}
    pipeline = [
        {
            "$match": {
                "CountryCode": {"$in": country_codes},
                "IndicatorCode": {"$in": complete_indicators},
                "Year": {"$gte": min_year, "$lte": max_year}
            }
        },
        {
            "$unionWith": {
                "coll": "sspi_imputed_data",
                "pipeline": [
                    {
                        "$match": {
                            "CountryCode": {"$in": country_codes},
                            "IndicatorCode": {"$in": complete_indicators},
                            "Year": {"$gte": min_year, "$lte": max_year}
                        }
                    }
                ]
            }
        },
        {
            "$group": {
                "_id": {
                    "CountryCode": "$CountryCode",
                    "Year": "$Year"
                },
                "Data": {
                    "$push": {
                        "IndicatorCode": "$IndicatorCode",
                        "Score": "$Score"
                    }
                }
            }
        },
        {
            "$set": {
                "CountryCode": "$_id.CountryCode",
                "Year": "$_id.Year"
            }
        },
        { "$unset": "_id" },
        {
            "$set": {
                "Data": {
                    "$map": {
                        "input": "$Data",
                        "as": "d",
                        "in": {
                            "$mergeObjects": [
                                "$$d",
                                {
                                    "sortKey": {
                                        "$let": {
                                            "vars": {
                                                "pair": {
                                                    "$first": {
                                                        "$filter": {
                                                            "input": {"$objectToArray": order_map_literal},
                                                            "as": "kv",
                                                            "cond": { "$eq": ["$$kv.k", "$$d.IndicatorCode"] }
                                                        }
                                                    }
                                                }
                                            },
                                            "in": { "$ifNull": ["$$pair.v", 999999] }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        },
        {
            "$set": {
                "Data": {
                    "$sortArray": { "input": "$Data", "sortBy": {"sortKey": 1} }
                }
            }
        },
        {
            "$project": {
                "CountryCode": 1,
                "Year": 1,
                "ScoreArray": {
                    "$map": { "input": "$Data", "as": "d", "in": "$$d.Score" }
                }
            }
        },
        {
            "$sort": {"CountryCode": 1, "Year": 1}
        }
    ]
    cursor = sspi_indicator_data.aggregate(pipeline)
    n_countries = len(country_codes)
    n_years = max_year - min_year + 1
    indicator_score_matrix = np.zeros((n_countries * n_years, ), dtype=object)  # placeholders for lists
    row_idx = 0
    for doc in cursor:
        # minimal retention: only save score vectors
        indicator_score_matrix[row_idx] = doc["ScoreArray"]
        row_idx += 1
    indicator_score_matrix = np.vstack(indicator_score_matrix).astype(float)  # shape: (rows, k_indicators)
    fast_sspi = FastSSPI(item_details=details_for_scoring)
    sspi_score_matrix = fast_sspi.score_matrix  # shape: (k_indicators, k_items)
    item_codes = fast_sspi.item_list
    n_items = len(item_codes)
    scores = indicator_score_matrix @ sspi_score_matrix    # shape: (rows, k_items)
    score_cube = scores.reshape(n_countries, n_years, n_items)
    score_cube_T = np.transpose(score_cube, (2, 0, 1))
    score_list = score_cube_T.reshape(n_items * n_countries, n_years)
    multi_index = pd.MultiIndex.from_tuples(
        [(i, c) for i in item_codes for c in country_codes],  # item outer, country inner
        names=["ItemCode", "CountryCode"]
    )
    df = pd.DataFrame(
        score_list,
        index=multi_index,
        columns=np.arange(min_year, max_year + 1)
    )
    return parse_json(score_list)


@dashboard_bp.route("/country/rankings/<country_code>/<item_level>")
def get_country_rankings(country_code, item_level):
    """
    Get all ranking data for a country at a specific item level across all time periods.

    Args:
        country_code: ISO 3-letter country code
        item_level: One of "indicator", "category", "pillar", or "sspi"

    Returns:
        JSON response with:
        - data: All ranking documents for the country/item_level combination
        - metadata: Item names and time period information
    """
    # Validate item_level
    valid_levels = ["indicator", "category", "pillar", "sspi"]
    if item_level.lower() not in valid_levels:
        return jsonify({
            "error": f"Invalid item_level. Must be one of: {', '.join(valid_levels)}"
        }), 400
    # Query all ranking data for this country and item level
    query = {"CountryCode": country_code}
    # Get all ranking documents
    ranking_data = parse_json(sspi_dynamic_rank_data.find(query, {"_id": 0}))
    if not ranking_data:
        return jsonify({
            "error": f"No ranking data found for country {country_code}"
        }), 404
    # Get item metadata to include item names
    item_details = sspi_metadata.item_details()
    item_name_map = {item["ItemCode"]: item["ItemName"] for item in item_details}
    # Filter by item level and enrich with item names
    filtered_data = []
    for doc in ranking_data:
        item_code = doc.get("ItemCode")
        if not item_code:
            continue
        # Get item detail to check item type
        item_detail = next((item for item in item_details if item["ItemCode"] == item_code), None)
        if not item_detail:
            continue
        item_type = item_detail.get("ItemType", "").lower()
        # Filter by requested item level
        if item_level.lower() == "sspi" and item_code.lower() == "sspi":
            doc["ItemName"] = "Social Policy and Progress Index"
            filtered_data.append(doc)
        elif item_level.lower() == item_type:
            doc["ItemName"] = item_name_map.get(item_code, item_code)
            filtered_data.append(doc)
    # Build time period structure organized by type
    time_periods_by_type = {}
    for doc in filtered_data:
        period_type = doc.get("TimePeriodType")
        period_label = doc.get("TimePeriod")
        if period_type and period_label:
            if period_type not in time_periods_by_type:
                time_periods_by_type[period_type] = set()
            time_periods_by_type[period_type].add(period_label)

    # Convert sets to sorted lists
    time_periods = {}
    for period_type, periods in time_periods_by_type.items():
        time_periods[period_type] = sorted(list(periods))

    # Get total number of countries in SSPI67 for rank context
    total_countries = len(sspi_metadata.country_group("SSPI67"))

    return jsonify({
        "countryCode": country_code,
        "itemLevel": item_level,
        "data": filtered_data,
        "timePeriods": time_periods,
        "itemCount": len(set(doc.get("ItemCode") for doc in filtered_data)),
        "totalCountries": total_countries
    })

            
@dashboard_bp.route("/country/characteristics/<country_code>")
def get_country_characteristics(country_code):
    """
    Get key country characteristics (population, GDP per capita, total GDP)
    for the most recent available year.

    Returns extensible array structure to allow easy addition of new
    characteristics (e.g., land area, landlocked status) in the future.
    """
    country_code = country_code.upper()

    # Get country details
    country_detail = sspi_metadata.get_country_detail(country_code)
    if not country_detail:
        return jsonify({"error": f"Country {country_code} not found"}), 404

    characteristics = []

    # Helper function to format large numbers
    def format_number(value, num_type="number"):
        """Format large numbers with appropriate units"""
        if value is None:
            return "N/A"

        abs_val = abs(value)

        if num_type == "currency":
            # Format currency
            if abs_val >= 1_000_000_000_000:  # Trillions
                return f"${value / 1_000_000_000_000:.1f} trillion"
            elif abs_val >= 1_000_000_000:  # Billions
                return f"${value / 1_000_000_000:.1f} billion"
            elif abs_val >= 1_000_000:  # Millions
                return f"${value / 1_000_000:.1f} million"
            else:
                return f"${value:,.0f}"
        else:
            # Format population or other numbers
            if abs_val >= 1_000_000_000:  # Billions
                return f"{value / 1_000_000_000:.1f} billion"
            elif abs_val >= 1_000_000:  # Millions
                return f"{value / 1_000_000:.1f} million"
            elif abs_val >= 1_000:  # Thousands
                return f"{value / 1_000:.1f} thousand"
            else:
                return f"{value:,.0f}"

    # Query population data (most recent year)
    population_results = sspi_clean_api_data.find({
        "CountryCode": country_code,
        "DatasetCode": "WB_POPULN"
    })
    # Sort by year and get most recent
    population_data = None
    if population_results:
        population_results_sorted = sorted(population_results, key=lambda x: x.get("Year", 0), reverse=True)
        population_data = population_results_sorted[0] if population_results_sorted else None

    if population_data:
        pop_value = population_data.get("Value")
        characteristics.append({
            "key": "population",
            "label": "Population",
            "value": pop_value,
            "year": population_data.get("Year"),
            "unit": "people",
            "formatted": format_number(pop_value),
            "source": "World Bank",
            "available": True
        })
    else:
        characteristics.append({
            "key": "population",
            "label": "Population",
            "value": None,
            "year": None,
            "unit": "people",
            "formatted": "Data not available",
            "source": "World Bank",
            "available": False
        })

    # Query land area data (most recent year)
    land_area_results = sspi_clean_api_data.find({
        "CountryCode": country_code,
        "DatasetCode": "WB_LANDAR"
    })
    # Sort by year and get most recent
    land_area_data = None
    if land_area_results:
        land_area_results_sorted = sorted(land_area_results, key=lambda x: x.get("Year", 0), reverse=True)
        land_area_data = land_area_results_sorted[0] if land_area_results_sorted else None

    if land_area_data:
        land_area_value = land_area_data.get("Value")
        characteristics.append({
            "key": "landArea",
            "label": "Land Area",
            "value": land_area_value,
            "year": land_area_data.get("Year"),
            "unit": "Square Kilometers",
            "formatted": f"{land_area_value:,.0f} km²" if land_area_value else "N/A",
            "source": "World Bank",
            "available": True
        })
    else:
        characteristics.append({
            "key": "landArea",
            "label": "Land Area",
            "value": None,
            "year": None,
            "unit": "Square Kilometers",
            "formatted": "Data not available",
            "source": "World Bank",
            "available": False
        })

    # Query GDP per capita data (most recent year)
    gdp_per_capita_results = sspi_clean_api_data.find({
        "CountryCode": country_code,
        "DatasetCode": "WB_GDP_PERCAP_CURPRICE_USD"
    })
    # Sort by year and get most recent
    gdp_per_capita_data = None
    if gdp_per_capita_results:
        gdp_per_capita_results_sorted = sorted(gdp_per_capita_results, key=lambda x: x.get("Year", 0), reverse=True)
        gdp_per_capita_data = gdp_per_capita_results_sorted[0] if gdp_per_capita_results_sorted else None

    if gdp_per_capita_data:
        gdp_pc_value = gdp_per_capita_data.get("Value")
        characteristics.append({
            "key": "gdpPerCapita",
            "label": "GDP per Capita",
            "value": gdp_pc_value,
            "year": gdp_per_capita_data.get("Year"),
            "unit": "USD (current)",
            "formatted": format_number(gdp_pc_value, "currency"),
            "source": "World Bank",
            "available": True
        })
    else:
        characteristics.append({
            "key": "gdpPerCapita",
            "label": "GDP per Capita",
            "value": None,
            "year": None,
            "unit": "USD (current)",
            "formatted": "Data not available",
            "source": "World Bank",
            "available": False
        })

    # Query SSPI rank and score (most recent year)
    sspi_rank_results = sspi_dynamic_rank_data.find({
        "CountryCode": country_code,
        "ItemCode": "SSPI",
        "TimePeriodType": "Single Year"
    })
    # Sort by TimePeriod (year) and get most recent
    sspi_rank_data = None
    if sspi_rank_results:
        sspi_rank_results_sorted = sorted(sspi_rank_results, key=lambda x: x.get("TimePeriod", "0"), reverse=True)
        sspi_rank_data = sspi_rank_results_sorted[0] if sspi_rank_results_sorted else None

    if sspi_rank_data:
        rank = sspi_rank_data.get("Rank")
        score = sspi_rank_data.get("Score")
        year = sspi_rank_data.get("TimePeriod")

        # Get total number of countries for this year
        total_countries_results = sspi_dynamic_rank_data.find({
            "ItemCode": "SSPI",
            "TimePeriod": year,
            "TimePeriodType": "Single Year"
        })
        total_countries = len(list(total_countries_results)) if total_countries_results else None

        # Format rank with ordinal suffix
        def ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return f"{n}{suffix}"

        # Insert SSPI characteristics at the beginning
        characteristics.insert(0, {
            "key": "sspiScore",
            "label": "SSPI Score",
            "value": score,
            "year": year,
            "rank": rank,
            "totalCountries": total_countries,
            "unit": "score (0-1)",
            "formatted": f"{score:.3f}",
            "source": "SSPI",
            "available": True
        })
    else:
        # Insert unavailable SSPI at the beginning
        characteristics.insert(0, {
            "key": "sspiScore",
            "label": "SSPI Score",
            "value": None,
            "year": None,
            "rank": None,
            "totalCountries": None,
            "unit": "score (0-1)",
            "formatted": "Data not available",
            "source": "SSPI",
            "available": False
        })


    return jsonify({
        "CountryCode": country_code,
        "CountryName": country_detail.get("Country"),
        "Flag": country_detail.get("Flag"),
        "characteristics": characteristics
    })
