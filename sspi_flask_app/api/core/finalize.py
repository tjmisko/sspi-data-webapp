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
    sspi_dynamic_matrix_data
)
from sspi_flask_app.api.resources.utilities import (
    country_code_to_name,
    colormap
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
        country_data = sspi_main_data_v3.find({"CountryCode": cou})
        sspi_scores = SSPI(item_details, country_data, strict_year=False)
        rank_dict = sspi_scores.to_rank_dict(cou, 2018)
        for item_code, rank_dict in rank_dict.items():
            if item_code in score_group_dictionary:
                score_group_dictionary[item_code][i].update(rank_dict)
    for item_code in sspi_item_codes:
        # Ranking table modifies each list[dict] in place
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
    indicator_data = sspi_indicator_data.find({
        "IndicatorCode": {"$in": indicator_codes},
        "Year": {"$gte": min_year, "$lte": max_year}
    })
    data_map = {}
    for obs in indicator_data:
        indicator_code = obs["IndicatorCode"]
        country_code = obs["CountryCode"]
        data_map.setdefault(indicator_code, {})
        data_map[indicator_code].setdefault(country_code, [])
        data_map[indicator_code][country_code].append(obs)
    count = 1
    for indicator_code in indicator_codes:
        yield f"{indicator_code} [ {count} of {len(indicator_codes)} ]\n"
        detail = sspi_metadata.get_indicator_detail(indicator_code)
        lg, ug = sspi_metadata.get_goalposts(indicator_code)
        lg = 0 if not lg else lg  # aggregates may not have goalposts
        ug = 1 if not ug else ug  # aggregates may not have goalposts
        if not data_map.get(indicator_code, None):
            count += 1
            continue
        for country_code, obs_list in data_map[indicator_code].items():
            obs_list = sorted(obs_list, key=lambda x: x["Year"])
            group_list = sspi_metadata.get_country_groups(country_code)
            years = [None] * len(label_list)
            scores = [None] * len(label_list)
            data = [None] * len(label_list)
            sspi_dataset_map = {}
            for dataset in obs_list[0].get("Datasets", []):
                sspi_dataset_map[dataset["DatasetCode"]] = {
                    "data": [None] * len(label_list)
                }
            for doc in obs_list:
                try:
                    year_index = label_list.index(doc["Year"])
                except ValueError:
                    continue
                years[year_index] = doc["Year"]
                data[year_index] = doc["Score"]
                scores[year_index] = doc["Score"]
                sspi_datasets = doc["Datasets"]
                for dataset in sspi_datasets:
                    if dataset["DatasetCode"] in sspi_dataset_map:
                        sspi_dataset_map[dataset["DatasetCode"]]["data"][year_index] = dataset["Value"]
            dataset = {
                "CCode": country_code,
                "CName": country_code_to_name(country_code),
                "ICode": indicator_code,
                "IName": detail["Indicator"],
                "CGroup": group_list,
                "pinned": False,
                "label": f"{country_code} - {country_code_to_name(country_code)}",
                "years": years,
                "Datasets": sspi_dataset_map,
                "minYear": min_year,
                "maxYear": max_year,
                "data": data,
                "score": scores,
                "yAxisMinValue": lg * 0.95 if lg > 0 else lg * 1.05,
                "yAxisMaxValue": ug * 1.05 if ug > 0 else ug * 0.95
            }
            sspi_indicator_dynamic_line_data.insert_one(dataset)
        count += 1


def finalize_dynamic_line_score_datasets():
    min_year = 2000
    max_year = datetime.now().year
    scores = sspi_item_data.find({})
    score_map = {}
    for observation in scores:
        country_code = observation["CountryCode"]
        item_code = observation["ItemCode"]
        score_map.setdefault(item_code, {})
        score_map[item_code].setdefault(country_code, [])
        score_map[item_code][country_code].append(observation)
    count = 1
    for item_code in score_map.keys():
        yield f"{item_code} [ {count} of {len(score_map.keys())} ]\n"
        detail = sspi_metadata.get_item_detail(item_code)
        # find the most specific name in the detail
        name_spec = ["IntermediateName", "IndicatorName",
                     "CategoryName", "PillarName", "Name"]
        item_name = ""
        for name in name_spec:
            if name in detail.keys():
                item_name = name
                break
        for country_code, obs_list in score_map[item_code].items():
            group_list = sspi_metadata.get_country_groups(country_code)
            obs_list = sorted(obs_list, key=lambda x: x["Year"])
            dataset = {
                "CCode": country_code,
                "CName": country_code_to_name(country_code),
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
                "label": f"{country_code} - {country_code_to_name(country_code)}",
                "years": [o["Year"] for o in obs_list],
                "minYear": min_year,
                "maxYear": max_year,
                "data": [o["Score"] for o in obs_list],
                "score": [o["Score"] for o in obs_list],
                "yAxisMinValue": 0,
                "yAxisMaxValue": 1
            }
            sspi_item_dynamic_line_data.insert_one(dataset)
        count += 1


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
    mongo_query = {
        "CountryCode": {"$in": country_codes},
        "IndicatorCode": {"$in": complete_indicators},
        "Year": {"$gte": 2000, "$lte": 2023}
    }
    details = sspi_metadata.item_details(indicator_filter=complete_indicators)
    clean_data = sspi_indicator_data.find(mongo_query)
    imputed_data = sspi_imputed_data.find(mongo_query)
    yield "Building Data Map\n"
    data_map = {}
    # Combine the two lists since they're already converted by MongoWrapper
    combined_data = clean_data + imputed_data
    for observation in combined_data:
        country_code = observation["CountryCode"]
        data_map.setdefault(country_code, {})
        data_map[country_code].setdefault(
            observation["Year"], {"Data": [], "SSPI": None})
        data_map[country_code][observation["Year"]]["Data"].append(observation)
    yield "Scoring Data\n"
    documents = []
    for country_code, year_data in data_map.items():
        yield f"Scoring {country_code}\n"
        for year, data in year_data.items():
            data["SSPI"] = SSPI(details, data["Data"])
            scores = data["SSPI"].to_score_documents(country_code)
            for doc in scores:
                detail = sspi_metadata.get_item_detail(doc["ItemCode"])
                doc["Children"] = detail.get("Children", [])
                # Add ItemName from metadata - use most specific name available
                name_priority = ["Indicator", "Category", "Pillar", "Name", "ItemName"]
                item_name = ""
                for name_key in name_priority:
                    if name_key in detail and detail[name_key]:
                        item_name = detail[name_key]
                        break
                doc["ItemName"] = item_name
                documents.append(doc)
    sspi_item_data.insert_many(documents)
