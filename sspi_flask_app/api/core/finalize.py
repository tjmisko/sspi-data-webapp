from flask import Blueprint, Response, stream_with_context, request
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_item_data,
    sspi_metadata,
    sspi_static_metadata,
    sspi_main_data_v3,
    sspi_static_rank_data,
    sspi_static_radar_data,
    sspi_static_stack_data,
    sspi_item_dynamic_line_data,
    sspi_indicator_dynamic_line_data,
    sspi_dynamic_matrix_data,
    sspi_globe_data,
    sspi_dynamic_radar_data
)
from sspi_flask_app.api.resources.utilities import (
    country_code_to_name,
    colormap,
    parse_json
)
from sspi_flask_app.models.coverage import DataCoverage
from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app.models.rank import SSPIRankingTable
import re
import os
import json
import pycountry
from datetime import datetime


finalize_bp = Blueprint(
    'finalize_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


def finalize_iterator(local_path, endpoints):
    # Defaults for country_list and indicator_list
    try:
        coverage = DataCoverage(2000, 2023, "SSPI67")
        indicator_list = coverage.complete()
        country_list = list(coverage.country_codes)
        yield "Finalizing Static Rank Data\n"
        finalize_sspi_static_rank_data()
        yield "Finalizing Static Radar Data\n"
        finalize_sspi_static_radar_data()
        yield "Finalizing Dynamic Radar Data\n"
        finalize_sspi_dynamic_radar_data()
        yield "Finalizing Static Stack Data\n"
        finalize_static_overall_stack_data()
        yield "Finalizing Dynamic Matrix Data\n"
        yield from finalize_matrix_iterator(local_path, endpoints)
        yield "Scoring Dynamic Data\n"
        yield from finalize_sspi_dynamic_score_iterator(indicator_list, country_list)
        yield "Finalizing Dynamic Line Data\n"
        sspi_indicator_dynamic_line_data.delete_many({})
        yield from finalize_dynamic_line_indicator_datasets()
        sspi_item_dynamic_line_data.delete_many({})
        yield from finalize_dynamic_line_score_datasets()
        yield "Finalizing Globe Data\n"
        finalize_globe_data()
        yield "Finalization Complete\n"
    except Exception as e:
        yield f"error: Finalization failed with exception: {str(e)}\n"
        yield f"error: Exception type: {type(e).__name__}\n"
        import traceback
        yield f"error: Traceback: {traceback.format_exc()}\n"


@finalize_bp.route("/production/finalize")
@login_required
def finalize_all_production_data():
    local_path = os.path.join(os.path.dirname(app.instance_path), "local")
    endpoints = [str(r) for r in app.url_map.iter_rules()]
    return Response(
        stream_with_context(finalize_iterator(local_path, endpoints)),
        mimetype='text/event-stream'
    )


@finalize_bp.route("/finalize/static/rank")
@login_required
def finalize_sspi_static_rank_data():
    """
    Computes the SSPI scores at all levels and stores them in a database
    ItemCode is the PillarCode, CategoryCode, or IndicatorCode
    """
    sspi_static_rank_data.delete_many({})
    country_codes = sspi_static_metadata.country_group("SSPI49")
    item_details = sspi_static_metadata.item_details()
    sspi_item_codes = ["SSPI"] + sspi_static_metadata.pillar_codes() + \
        sspi_static_metadata.category_codes() + \
        sspi_static_metadata.indicator_codes()
    score_group_dictionary = {
        item_code: [
            {"CCode": "", "Score": 0, "Rank": 0,
                "IName": "", "ICode": "", "Year": 0}
            for _ in country_codes]
        for item_code in sspi_item_codes}
    for i, cou in enumerate(country_codes):
        country_data = sspi_main_data_v3.find({"CountryCode": cou}, {"_id": 0})
        sspi_scores = SSPI(item_details, country_data, strict_year=False)
        rank_dict = sspi_scores.to_rank_dict(cou, 2018)
        for item_code, rank_dict in rank_dict.items():
            if item_code in score_group_dictionary:
                score_group_dictionary[item_code][i].update(rank_dict)
    for item_code in sspi_item_codes:
        SSPIRankingTable(score_group_dictionary[item_code])
        score_group_dictionary[item_code] = sorted(
            score_group_dictionary[item_code], key=lambda x: x["Rank"]
        )
    for item_code, score_list in score_group_dictionary.items():
        for score in score_list:
            doc = {
                "ICode": item_code,
                "IName": score["IName"],
                "CCode": score["CCode"],
                "CName": country_code_to_name(score["CCode"]),
                "Year": score["Year"],
                "Tie": score["Tie"],
                "Score": score["Score"],
                "Rank": score["Rank"]
            }
            cou = pycountry.countries.get(alpha_3=score["CCode"])
            if cou is not None:
                doc["CFlag"] = cou.flag
            sspi_static_rank_data.insert_one(doc)
    return "Successfully finalized rank data!"


@finalize_bp.route("/finalize/static/stack")
@login_required
def finalize_static_overall_stack_data():
    sspi_static_stack_data.delete_many({})
    overall_scores = sspi_static_rank_data.find({"ICode": "SSPI"}, {"_id": 0})
    # Create lookup dictionary for performance
    overall_lookup = {score["CCode"]: score for score in overall_scores}
    def fetch_overall(observation: dict, field="Rank") -> float:
        if observation["CCode"] in overall_lookup:
            return overall_lookup[observation["CCode"]][field]
        return float('inf')

    sus_scores = sspi_static_rank_data.find({"ICode": "SUS"}, {"_id": 0})
    sus_scores.sort(key=fetch_overall)
    for score in sus_scores:
        score["SSPIScore"] = fetch_overall(score, "Score")
        score["SSPIRank"] = fetch_overall(score)
    sus_dataset = {
        "label": "SUS",
        "data": [c["Score"] / 3 for c in sus_scores],
        "info": sus_scores,
        "borderWidth": 2
    }
    ms_scores = sspi_static_rank_data.find({"ICode": "MS"}, {"_id": 0})
    ms_scores.sort(key=fetch_overall)
    for score in ms_scores:
        score["SSPIScore"] = fetch_overall(score, "Score")
        score["SSPIRank"] = fetch_overall(score)
    ms_dataset = {
        "label": "MS",
        "data": [c["Score"] / 3 for c in ms_scores],
        "info": ms_scores,
        "borderWidth": 2
    }
    pg_scores = sspi_static_rank_data.find({"ICode": "PG"}, {"_id": 0})
    pg_scores.sort(key=fetch_overall)
    for score in pg_scores:
        score["SSPIScore"] = fetch_overall(score, "Score")
        score["SSPIRank"] = fetch_overall(score)
    pg_dataset = {
        "label": "PG",
        "data": [c["Score"] / 3 for c in pg_scores],
        "info": pg_scores,
        "borderWidth": 2
    }
    sspi_static_stack_data.insert_one({
        "data": {
            "labels": [c["CName"] + " " + c["CFlag"] for c in overall_scores],
            "datasets": [
                sus_dataset,
                ms_dataset,
                pg_dataset
            ]
        }
    })
    return "Successfully finalized stack data!"


@finalize_bp.route("/finalize/static/radar")
@login_required
def finalize_sspi_static_radar_data():
    sspi_static_radar_data.delete_many({})

    def make_country_lookup(main_data):
        country_lookup = {}
        for document in main_data:
            country_code = document["CountryCode"]
            if country_code not in country_lookup.keys():
                country_lookup[country_code] = {"Data": []}
            country_lookup[country_code]["Data"].append(document)
        return country_lookup

    main_data = sspi_main_data_v3.find({}, {"_id": 0})
    item_details = sspi_static_metadata.item_details()
    country_lookup = make_country_lookup(main_data)
    radar_data = []
    for country_code, _ in country_lookup.items():
        output_dict = {
            "CCode": country_code,
            "Year": 2018
        }
        output_dict["legendItems"] = []
        output_dict["title"] = country_code_to_name(country_code)
        sspi = SSPI(item_details, country_lookup[country_code]["Data"], strict_year=False)
        output_dict["labels"] = [c.code for c in sspi.categories]
        output_dict["labelMap"] = {c.code: c.name for c in sspi.categories}
        output_dict["datasets"] = []
        output_dict["ranks"] = []
        category_start_index = 0
        for pillar in sspi.pillars:
            data = [None] * len(sspi.categories)
            output_dict["legendItems"].append({
                "Code": pillar.code,
                "Name": pillar.name,
                "Score": pillar.score
            })
            for i, category_code in enumerate(pillar.category_codes):
                category = sspi.get_item(category_code)
                data[category_start_index + i] = category.score
                output_dict["ranks"].append(sspi_static_rank_data.find_one(
                    {"ICode": category.code, "CCode": country_code},
                    {"_id": 0}
                ))
            category_start_index += len(pillar.category_codes)
            pillar_color = colormap(pillar.code, alpha="66")
            output_dict["datasets"].append({
                "label": pillar.name,
                "pillarCode": pillar.code,
                "data": data,
                "backgroundColor": pillar_color,
                "borderColor": pillar_color,
                "pointBackgroundColor": pillar_color,
                "pointBorderColor": '#fff',
                "pointHoverBackgroundColor": '#fff',
                "pointHoverBorderColor": pillar_color,
                "fill": True
            })
        radar_data.append(output_dict)
    sspi_static_radar_data.insert_many(radar_data)
    return "Successfully finalized radar data!"


@finalize_bp.route("/finalize/dynamic/radar")
@login_required
def finalize_sspi_dynamic_radar_data():
    sspi_dynamic_radar_data.delete_many({})
    pillar_codes = sspi_metadata.pillar_codes()
    category_codes = sspi_metadata.category_codes()

    # Pre-compute metadata structure for consistent positioning
    pillar_details = sspi_metadata.pillar_details()
    # Sort pillars by ItemOrder to ensure consistent ordering
    sorted_pillars = sorted(pillar_details, key=lambda p: p.get('ItemOrder', 999))

    # Build complete category list and position map
    all_categories = []
    pillar_positions = {}  # Maps pillar_code -> {start_index, category_codes}
    all_labels_map = {}    # Maps category_code -> category_name

    category_start_index = 0
    for pillar in sorted_pillars:
        pillar_code = pillar['ItemCode']
        cat_codes = pillar.get('Children', [])

        pillar_positions[pillar_code] = {
            'start_index': category_start_index,
            'category_codes': cat_codes
        }

        # Build labels in order
        for cat_code in cat_codes:
            all_categories.append(cat_code)
            # Get category name from metadata
            try:
                cat_detail = sspi_metadata.get_item_detail(cat_code)
                all_labels_map[cat_code] = cat_detail.get('ItemName', cat_code)
            except:
                all_labels_map[cat_code] = cat_code

        category_start_index += len(cat_codes)

    total_categories = len(all_categories)

    # Single aggregation to get all pillar and category data
    pipeline = [
        {"$match": {
            "Year": {"$gte": 2000, "$lte": 2023},
            "ItemCode": {"$in": pillar_codes + category_codes}
        }},
        {"$sort": {"CountryCode": 1, "Year": 1, "ItemCode": 1}},
        {"$group": {
            "_id": {"CCode": "$CountryCode", "Year": "$Year"},
            "items": {"$push": {
                "ICode": "$ItemCode",
                "IName": "$ItemName",
                "Score": "$Score",
                "ItemType": "$ItemType",
                "Children": "$Children"
            }}
        }},
        {"$project": {"_id": 0, "CCode": "$_id.CCode", "Year": "$_id.Year", "items": 1}}
    ]
    aggregated_data = sspi_item_data.aggregate(pipeline)
    radar_documents = []

    for doc in aggregated_data:
        country_code, year = doc["CCode"], doc["Year"]
        item_map = {item["ICode"]: item for item in doc["items"]}

        output_dict = {
            "CCode": country_code,
            "Year": year,
            "title": f"{country_code_to_name(country_code)} ({year})",
            "labels": all_categories,      # Use pre-built complete list
            "labelMap": all_labels_map,    # Use pre-built map
            "datasets": [],
            "legendItems": []
        }

        # Process pillars in sorted order
        for pillar_detail in sorted_pillars:
            pillar_code = pillar_detail['ItemCode']

            # Check if this pillar exists in the aggregated data
            pillar_item = next((item for item in doc["items"] if item["ICode"] == pillar_code), None)
            if not pillar_item:
                continue  # Skip if pillar not available for this country-year

            # Get position information
            position_info = pillar_positions[pillar_code]
            start_index = position_info['start_index']
            cat_codes = position_info['category_codes']

            # Initialize full-length array with nulls
            data = [None] * total_categories

            # Fill only this pillar's category positions
            for i, cat_code in enumerate(cat_codes):
                if cat_code in item_map:
                    data[start_index + i] = item_map[cat_code]["Score"]
                # else: leave as None

            # Add legend item
            output_dict["legendItems"].append({
                "Code": pillar_code,
                "Name": pillar_item["IName"],
                "Score": pillar_item["Score"]
            })

            # Add dataset with properly positioned data
            pillar_color = colormap(pillar_code, alpha="66")
            output_dict["datasets"].append({
                "label": pillar_item["IName"],
                "pillarCode": pillar_code,
                "data": data,
                "backgroundColor": pillar_color,
                "borderColor": pillar_color,
                "pointBackgroundColor": pillar_color,
                "pointBorderColor": '#fff',
                "pointHoverBackgroundColor": '#fff',
                "pointHoverBorderColor": pillar_color,
                "fill": True
            })

        radar_documents.append(output_dict)

    if radar_documents:
        sspi_dynamic_radar_data.insert_many(radar_documents)
    return f"Successfully finalized dynamic radar data for {len(radar_documents)} country-year combinations!"


@finalize_bp.route("/finalize/dynamic/line")
@login_required
def finalize_dynamic_line_data():
    """
    Prepare the data for a Chart.js line plot
    """
    def combined_iterator():
        yield from finalize_dynamic_line_indicator_datasets()
        yield from finalize_dynamic_line_score_datasets()
    sspi_indicator_dynamic_line_data.delete_many({})
    sspi_item_dynamic_line_data.delete_many({})
    return Response(combined_iterator(), mimetype='text/event-stream')


def finalize_dynamic_line_indicator_datasets():
    min_year = 2000
    max_year = datetime.now().year
    label_list = list(range(min_year, max_year + 1))
    indicator_codes = sspi_metadata.indicator_codes()
    yield "Building Metadata Lookups\n"
    indicator_details = {
        ind["IndicatorCode"]: ind
        for ind in sspi_metadata.indicator_details()
    }
    goalposts_lookup = {
        code: sspi_metadata.get_goalposts(code)
        for code in indicator_codes
    }
    all_countries = set()
    for ind_data in sspi_indicator_data.find({
        "IndicatorCode": {"$in": indicator_codes},
        "Year": {"$gte": min_year, "$lte": max_year}
    }, {"CountryCode": 1}):
        all_countries.add(ind_data["CountryCode"])
    country_details_lookup = {
        country: sspi_metadata.get_country_detail(country)
        for country in all_countries
    }
    pipeline = [
        {
            "$match": {
                "IndicatorCode": {"$in": indicator_codes},
                "Year": {"$gte": min_year, "$lte": max_year}
            }
        },
        {
            "$sort": {"Year": 1}
        },
        {
            "$group": {
                "_id": {
                    "IndicatorCode": "$IndicatorCode",
                    "CountryCode": "$CountryCode"
                },
                "observations": {
                    "$push": {
                        "Year": "$Year",
                        "Score": "$Score",
                        "Unit": "$Unit",
                        "Datasets": "$Datasets"
                    }
                },
                "firstDatasets": {"$first": "$Datasets"} # Store first observation's Datasets
            }
        },
        {
            "$project": {
                "_id": 0,
                "IndicatorCode": "$_id.IndicatorCode",
                "CountryCode": "$_id.CountryCode",
                "observations": 1,
                "firstDatasets": 1
            }
        },
        {
            "$sort": {"IndicatorCode": 1, "CountryCode": 1}
        }
    ]
    yield "Executing Aggregation Pipeline\n"
    grouped_data_cursor = sspi_indicator_data.aggregate(pipeline)
    yield "Processing Indicator Line Data\n"
    documents = []
    BATCH_SIZE = 500
    count = 0
    total_documents_inserted = 0
    for group in grouped_data_cursor:
        indicator_code = group["IndicatorCode"]
        country_code = group["CountryCode"]
        observations = group["observations"]  # Already sorted by Year
        count += 1
        detail = indicator_details.get(indicator_code, {})
        lg, ug = goalposts_lookup.get(indicator_code, (None, None))
        lg = 0 if not lg else lg  # aggregates may not have goalposts
        ug = 1 if not ug else ug  # aggregates may not have goalposts
        group_list = country_details_lookup.get(country_code, {}).get("CountryGroups", [])
        country_name = country_details_lookup.get(country_code, {}).get("Country", country_code)
        country_flag = country_details_lookup.get(country_code, {}).get("Flag", country_code)

        # Build sparse arrays with None values
        years = [None] * len(label_list)
        scores = [None] * len(label_list)
        data = [None] * len(label_list)

        # Initialize dataset map from first observation
        sspi_dataset_map = {}
        for dataset in group.get("firstDatasets", []):
            sspi_dataset_map[dataset["DatasetCode"]] = {
                "data": [None] * len(label_list)
            }
        for obs in observations:
            try:
                year_index = label_list.index(obs["Year"])
            except ValueError:
                continue

            years[year_index] = obs["Year"]
            data[year_index] = obs["Score"]
            scores[year_index] = obs["Score"]

            # Populate dataset values
            for dataset in obs.get("Datasets", []):
                if dataset["DatasetCode"] in sspi_dataset_map:
                    sspi_dataset_map[dataset["DatasetCode"]]["data"][year_index] = dataset["Value"]
        # Build document
        dataset = {
            "CCode": country_code,
            "CName": country_name,
            "CFlag": country_flag,
            "ICode": indicator_code,
            "IName": detail.get("Indicator", ""),
            "CGroup": group_list,
            "pinned": False,
            "label": f"{country_code} - {country_name}",
            "years": years,
            "Datasets": sspi_dataset_map,
            "minYear": min_year,
            "maxYear": max_year,
            "data": data,
            "score": scores,
            "yAxisMinValue": lg * 0.95 if lg > 0 else lg * 1.05,
            "yAxisMaxValue": ug * 1.05 if ug > 0 else ug * 0.95
        }
        documents.append(dataset)
        if len(documents) >= BATCH_SIZE:
            sspi_indicator_dynamic_line_data.insert_many(documents)
            total_documents_inserted += len(documents)
            documents = []
    if documents:
        sspi_indicator_dynamic_line_data.insert_many(documents)
        total_documents_inserted += len(documents)
        yield f"Inserted final {len(documents)} documents\n"

    yield f"Complete - Processed {count} indicator-country combinations, inserted {total_documents_inserted} documents\n"


def finalize_dynamic_line_score_datasets():
    min_year = 2000
    max_year = datetime.now().year
    yield "Building Metadata Lookups\n"
    item_details = {
        item["ItemCode"]: item
        for item in sspi_metadata.item_details()
        if item.get("ItemCode")
    }
    all_countries = set()
    for item_data in sspi_item_data.find({}, {"CountryCode": 1}):
        all_countries.add(item_data["CountryCode"])

    country_details_lookup = {
        country: sspi_metadata.get_country_detail(country)
        for country in all_countries
    }
    yield "Building Aggregation Pipeline\n"
    pipeline = [
        {
            "$sort": {"Year": 1}
        },
        {
            "$group": {
                "_id": {
                    "ItemCode": "$ItemCode",
                    "CountryCode": "$CountryCode"
                },
                "observations": {
                    "$push": {
                        "Year": "$Year",
                        "Score": "$Score"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "ItemCode": "$_id.ItemCode",
                "CountryCode": "$_id.CountryCode",
                "observations": 1
            }
        },
        {
            "$sort": {"ItemCode": 1, "CountryCode": 1}
        }
    ]

    yield "Executing Aggregation Pipeline\n"
    grouped_data_cursor = sspi_item_data.aggregate(pipeline)

    yield "Processing Score Line Data\n"
    documents = []
    BATCH_SIZE = 500
    count = 0
    total_documents_inserted = 0

    for group in grouped_data_cursor:
        item_code = group["ItemCode"]
        country_code = group["CountryCode"]
        observations = group["observations"]  # Already sorted by Year
        detail = item_details.get(item_code, {})
        group_list = country_details_lookup.get(country_code, {}).get("CountryGroups", [])
        country_name = country_details_lookup.get(country_code, {}).get("Country", country_code)
        country_flag = country_details_lookup.get(country_code, {}).get("Flag", country_code)
        name_spec = ["IntermediateName", "IndicatorName",
                     "CategoryName", "PillarName", "Name"]
        item_name = ""
        for name in name_spec:
            if name in detail:
                item_name = detail[name]
                break
        dataset = {
            "CCode": country_code,
            "CName": country_name,
            "CFlag": country_flag,
            "ICode": item_code,
            "IName": item_name,
            "CGroup": group_list,
            "Detail": detail,
            "parsing": {
                "xAxisKey": "years",
                "yAxisKey": "scores"
            },
            "pinned": False,
            "hidden": "SSPI67" not in group_list,
            "label": f"{country_code} - {country_name}",
            "years": [o["Year"] for o in observations],
            "minYear": min_year,
            "maxYear": max_year,
            "data": [o["Score"] for o in observations],
            "score": [o["Score"] for o in observations],
            "yAxisMinValue": 0,
            "yAxisMaxValue": 1
        }
        documents.append(dataset)

        # Batch insert for better performance
        if len(documents) >= BATCH_SIZE:
            sspi_item_dynamic_line_data.insert_many(documents)
            total_documents_inserted += len(documents)
            documents = []

    # Insert any remaining documents
    if documents:
        sspi_item_dynamic_line_data.insert_many(documents)
        total_documents_inserted += len(documents)
        yield f"Inserted final {len(documents)} documents\n"

    yield f"Complete - Processed {count} item-country combinations, inserted {total_documents_inserted} documents\n"


@finalize_bp.route("/finalize/dynamic/matrix")
@login_required
def finalize_dynamic_matrix_data():
    local_path = os.path.join(os.path.dirname(app.instance_path), "local")
    endpoints = [str(r) for r in app.url_map.iter_rules()]
    return Response(finalize_matrix_iterator(local_path, endpoints), mimetype='text/event-stream')


def finalize_matrix_iterator(local_path, endpoints):
    sspi_dynamic_matrix_data.delete_many({})
    with open(os.path.join(local_path, "indicator-problems.json")) as f:
        problems = json.load(f)
    with open(os.path.join(local_path, "indicator-confident.json")) as f:
        confident = json.load(f)
    pipeline = [
        {
            "$group": {
                "_id": {
                    "IndicatorCode": "$IndicatorCode",
                    "CountryCode": "$CountryCode"
                },
                "yearSet": {
                    "$addToSet": {
                        "$cond": [{"$gt": ["$Year", 1990]}, "$Year", "$$REMOVE"]
                    }
                },
                "scoreList": {"$push": "$Score"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "IndicatorCode": "$_id.IndicatorCode",
                "CountryCode": "$_id.CountryCode",
                "yearCount": {"$size": "$yearSet"},
                "yearMin": {"$min": "$yearSet"},
                "yearMax": {"$max": "$yearSet"},
                "averageScore": {"$avg": "$scoreList"},
                "minScore": {"$min": "$scoreList"},
                "maxScore": {"$max": "$scoreList"}
            }
        }
    ]
    result = sspi_indicator_data.aggregate(pipeline)
    sspi49_countries = sspi_metadata.country_group("SSPI49")
    sspi_extended_countries = sspi_metadata.country_group("SSPIExtended")
    indicator_details, indicator_map = sspi_metadata.indicator_details(), {}
    for detail in indicator_details:
        indicator_map[detail["IndicatorCode"]] = {
            "IName": detail["Indicator"],
        }
    count = 1
    for obs in result:
        indicator_code = obs["IndicatorCode"]
        country = obs["CountryCode"]
        
        # Skip indicators not in metadata (safety check)
        if indicator_code not in indicator_map:
            continue
            
        sspi_dynamic_matrix_data.insert_one({
            "x": indicator_code,
            "y": country,
            "v": obs["yearCount"],
            "IName": indicator_map[indicator_code]["IName"],
            "SSPI49": country in sspi49_countries,
            "SSPIExtended": country in sspi_extended_countries,
            "CName": country_code_to_name(country)
        })
        if count % 100 == 0:
            yield f"Finalizing Observation {count}\n"
        count += 1


@finalize_bp.route("/finalize/dynamic/score")
@login_required
def finalize_sspi_dynamic_score():
    """
    Prepare the data for a Chart.js line plot
    """
    countries = request.args.getlist("CountryCode")
    country_group = request.args.get("CountryGroup")
    if country_group is None:
        country_group = "SSPI67"
    coverage = DataCoverage(2000, 2023, country_group, countries=countries)
    indicator_list = coverage.complete()
    country_list = list(coverage.country_codes)
    app.logger.info(f"country_list: {country_list}")
    app.logger.info(f"indicator_list: {indicator_list}")
    return Response(finalize_sspi_dynamic_score_iterator(indicator_list, country_list), mimetype='text/event-stream')


def finalize_sspi_dynamic_score_iterator(indicator_codes: list[str], country_codes: list[str] | None = None):
    sspi_item_data.delete_many({})

    # Filter to only complete indicators to avoid scoring incomplete categories
    if country_codes is None:
        country_codes = sspi_metadata.country_group("SSPI67")
    coverage = DataCoverage(2000, 2023, "SSPI67", countries=country_codes)
    complete_indicators = coverage.complete()

    # Get metadata for scoring - this properly filters to complete indicators
    # and includes the full hierarchy (pillars, categories, indicators, root)
    details_for_scoring = sspi_metadata.item_details(indicator_filter=complete_indicators)

    # Build item detail lookup from ALL item details for enrichment after scoring
    # This ensures we can enrich computed items (pillars, categories) with metadata
    all_details = sspi_metadata.item_details()
    item_detail_lookup = {detail.get("ItemCode"): detail for detail in all_details if detail.get("ItemCode")}

    yield "Building Aggregation Pipeline\n"

    # Optimized MongoDB aggregation pipeline:
    # 1. Unions both collections (indicator_data + imputed_data)
    # 2. Filters to only needed data
    # 3. Groups by CountryCode + Year in database (reduces 195k docs to ~1600 groups)
    # 4. Returns pre-grouped data ready for SSPI scoring
    pipeline = [
        # Stage 1: Match documents from sspi_indicator_data
        {
            "$match": {
                "CountryCode": {"$in": country_codes},
                "IndicatorCode": {"$in": complete_indicators},
                "Year": {"$gte": 2000, "$lte": 2023}
            }
        },
        # Stage 2: Union with sspi_imputed_data (combines both collections)
        {
            "$unionWith": {
                "coll": "sspi_imputed_data",
                "pipeline": [
                    {
                        "$match": {
                            "CountryCode": {"$in": country_codes},
                            "IndicatorCode": {"$in": complete_indicators},
                            "Year": {"$gte": 2000, "$lte": 2023}
                        }
                    }
                ]
            }
        },
        # Stage 3: Group by CountryCode and Year, collecting all indicator data
        # This is the key optimization: reduces ~195k docs to ~1600 groups in MongoDB
        {
            "$group": {
                "_id": {
                    "CountryCode": "$CountryCode",
                    "Year": "$Year"
                },
                "Data": {
                    "$push": {
                        "CountryCode": "$CountryCode",
                        "IndicatorCode": "$IndicatorCode",
                        "Score": "$Score",
                        "Year": "$Year",
                        "Unit": "$Unit",
                        "Datasets": "$Datasets"
                    }
                }
            }
        },
        # Stage 4: Reshape output for easier processing
        {
            "$project": {
                "_id": 0,
                "CountryCode": "$_id.CountryCode",
                "Year": "$_id.Year",
                "Data": 1
            }
        },
        # Stage 5: Sort for consistent processing order
        {
            "$sort": {"CountryCode": 1, "Year": 1}
        }
    ]

    yield "Executing Aggregation Pipeline\n"
    # Execute aggregation - returns cursor of pre-grouped country-year data
    grouped_data_cursor = sspi_indicator_data.aggregate(pipeline)

    yield "Scoring Data with Batch Inserts\n"

    # Batch insert configuration for better performance
    BATCH_SIZE = 500  # Insert every 500 documents to balance memory and DB performance
    documents = []
    count = 0
    total_documents_inserted = 0

    # Process cursor without loading everything into memory
    for group in grouped_data_cursor:
        country_code = group["CountryCode"]
        year = group["Year"]
        indicator_data = group["Data"]

        count += 1
        if count % 25 == 0:
            yield f"Scoring {country_code} ({year}) - Group {count}\n"

        # Create SSPI object and compute scores for this country-year
        sspi = SSPI(details_for_scoring, indicator_data)
        scores = sspi.to_score_documents(country_code)

        # Enrich score documents with metadata using pre-built lookup
        for doc in scores:
            item_code = doc["ItemCode"]
            if item_code in item_detail_lookup:
                detail = item_detail_lookup[item_code]
                doc["Children"] = detail.get("Children", [])

                # Add ItemName from metadata - use most specific name available
                name_priority = ["Indicator", "Category", "Pillar", "Name", "ItemName"]
                for name_key in name_priority:
                    if name_key in detail and detail[name_key]:
                        doc["ItemName"] = detail[name_key]
                        break

            documents.append(doc)

        # Batch insert when we hit the batch size threshold
        if len(documents) >= BATCH_SIZE:
            sspi_item_data.insert_many(documents)
            total_documents_inserted += len(documents)
            documents = []  # Clear batch

    # Insert any remaining documents
    if documents:
        sspi_item_data.insert_many(documents)
        total_documents_inserted += len(documents)
        yield f"Inserted final {len(documents)} documents\n"

    yield f"Scoring Complete - Total: {total_documents_inserted} documents inserted\n"


@finalize_bp.route("/finalize/globe")
@login_required
def finalize_globe_data():
    sspi_globe_data.delete_many({})
    globe_item_data = sspi_item_data.aggregate([
        { "$match": { "ItemCode": {"$in": ["SSPI", "SUS", "MS", "PG"]} } },
        { "$sort": { "Year": 1, "ItemCode": 1, "CountryCode": 1 } },
        { "$group": {
            "_id": {
                "ItemCode": "$ItemCode",
                "CountryCode": "$CountryCode"
            },
            "Scores": { "$push": "$Score" },
        } },
        { "$group": {
            "_id": "$_id.CountryCode",
            "items": { "$push": {"k": "$_id.ItemCode", "v": "$Scores"} }
        } },
        { "$project": { "_id": 0, "CountryCode": "$_id", "Scores": { "$arrayToObject": "$items"} } }
    ])
    scored_country_codes = {doc["CountryCode"] for doc in globe_item_data}
    globe_geojson = sspi_metadata.find_one({"DocumentType": "GlobeGeoJSON"})
    for feature in globe_geojson["Metadata"]["features"]:
        country_code = feature["properties"]["ISO_A3"]
        if str(country_code) == "-99" or not country_code:
            country_code = feature["properties"]["ADM0_A3"]
        result = pycountry.countries.get(alpha_3=country_code)
        if not result:
            print(feature["properties"])
            app.logger.error(f"Country Code {country_code} not found in pycountry!")
            continue
        country_name = result.name
        country_flag = result.flag
        if country_code not in scored_country_codes:
            feature["properties"] = {
                "SSPI": [None] * 24,
                "SUS": [None] * 24,
                "MS": [None] * 24,
                "PG": [None] * 24,
                "CName": country_name,
                "CCode": country_code,
                "CFlag": country_flag
            }
            continue
        country_data = {}
        i = 0
        while not country_data:
            if globe_item_data[i]["CountryCode"] == country_code:
                country_data = globe_item_data[i]
            i += 1
        feature["properties"] = {
            "SSPI": country_data["Scores"]["SSPI"],
            "SUS": country_data["Scores"]["SUS"],
            "MS": country_data["Scores"]["MS"],
            "PG": country_data["Scores"]["PG"],
            "CName": country_name,
            "CCode": country_code,
            "CFlag": country_flag
        }
    sspi_globe_data.insert_one(globe_geojson["Metadata"])
    return parse_json(globe_geojson["Metadata"])
