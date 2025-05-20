from flask import Blueprint, Response, stream_with_context, request
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_score_data,
    sspi_metadata,
    sspi_static_metadata,
    sspi_main_data_v3,
    sspi_static_rank_data,
    sspi_static_radar_data,
    sspi_static_stack_data,
    sspi_dynamic_line_data,
    sspi_dynamic_matrix_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
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
    yield "Finalizing Static Rank Data\n"
    finalize_sspi_static_rank_data()
    yield "Finalizing Static Radar Data\n"
    finalize_sspi_static_radar_data()
    yield "Finalizing Static Stack Data\n"
    finalize_static_overall_stack_data()
    yield "Finalizing Dynamic Line Data\n"
    yield from finalize_dynamic_line_iterator()
    yield "Finalizing Dynamic Matrix Data\n"
    yield from finalize_matrix_iterator(local_path, endpoints)
    yield "Finalization Complete\n"


@finalize_bp.route("/production/finalize")
@login_required
def finalize_all_production_data():
    local_path = os.path.join(os.path.dirname(app.instance_path), "local")
    endpoints = [str(r) for r in app.url_map.iter_rules()]
    return Response(
        stream_with_context(finalize_iterator(local_path, endpoints)),
        mimetype='text/event-stream'
    )


@finalize_bp.route("/production/finalize/static/rank")
@login_required
def finalize_sspi_static_rank_data():
    """
    Computes the SSPI scores at all levels and stores them in a database
    ItemCode is the PillarCode, CategoryCode, or IndicatorCode
    """
    sspi_static_rank_data.delete_many({})
    country_codes = sspi_static_metadata.country_group("SSPI49")
    indicator_details = sspi_static_metadata.indicator_details()
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
        sspi_scores = SSPI(indicator_details, country_data)
        score_group_dictionary["SSPI"][i].update({
            "CCode": cou,
            "Score": sspi_scores.score(),
            "IName": "SSPI",
            "Year": 2018
        })
        for pillar in sspi_scores.pillars:
            score_group_dictionary[pillar.code][i].update({
                "CCode": cou,
                "Score": pillar.score(),
                "IName": pillar.name,
                "Year": 2018
            })
            for category in pillar.categories:
                score_group_dictionary[category.code][i].update({
                    "CCode": cou,
                    "Score": category.score(),
                    "IName": category.name,
                    "Year": 2018
                })
                for indicator in category.indicators:
                    score_group_dictionary[indicator.code][i].update({
                        "CCode": cou,
                        "Score": indicator.score,
                        "IName": indicator.name,
                        "Year": indicator.year,
                        "Value": indicator.value,
                        "LowerGoalpost": indicator.lower_goalpost,
                        "UpperGoalpost": indicator.upper_goalpost
                    })
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
                "CFlag": pycountry.countries.get(
                    alpha_3=score["CCode"]).flag,
                "Year": score["Year"],
                "Tie": score["Tie"],
                "Score": score["Score"],
                "Rank": score["Rank"]
            }
            if score.get("Value") is not None:
                doc["Value"] = score["Value"]
            if score.get("LowerGoalpost") is not None:
                doc["LowerGoalpost"] = score["LowerGoalpost"]
            if score.get("UpperGoalpost") is not None:
                doc["UpperGoalpost"] = score["UpperGoalpost"]
            sspi_static_rank_data.insert_one(doc)
    return "Successfully finalized rank data!"


@finalize_bp.route("/production/finalize/static/stack")
@login_required
def finalize_static_overall_stack_data():
    sspi_static_stack_data.delete_many({})
    overall_scores = sspi_static_rank_data.find({"ICode": "SSPI"}, {"_id": 0})

    def fetch_overall(observation, field="Rank"):
        for score in overall_scores:
            if score["CCode"] == observation["CCode"]:
                return score[field]
        return None

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


@finalize_bp.route("/production/finalize/static/radar")
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
    indicator_details = sspi_static_metadata.indicator_details()
    country_lookup = make_country_lookup(main_data)
    radar_data = []
    for country_code, data_dict in country_lookup.items():
        output_dict = {
            "CCode": country_code,
            "Year": 2018
        }
        output_dict["legendItems"] = []
        output_dict["title"] = country_code_to_name(country_code)
        sspi = SSPI(indicator_details, country_lookup[country_code]["Data"])
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
                "Score": pillar.score()
            })
            for i, category in enumerate(pillar.categories):
                data[category_start_index + i] = category.score()
                output_dict["ranks"].append(sspi_static_rank_data.find_one(
                    {"ICode": category.code, "CCode": country_code},
                    {"_id": 0}
                ))
            category_start_index += len(pillar.categories)
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


@finalize_bp.route("/production/finalize/dynamic/line")
@login_required
def finalize_sspi_dynamic_line_data():
    """
    Prepare the data for a Chart.js line plot
    """
    return Response(finalize_dynamic_line_iterator(), mimetype='text/event-stream')


def finalize_dynamic_line_iterator():
    sspi_dynamic_line_data.delete_many({})
    indicator_codes = sspi_metadata.indicator_codes()
    count = 1
    for IndicatorCode in indicator_codes:
        yield f"{IndicatorCode} [ {count} of {len(indicator_codes)} ]\n"
        detail = sspi_metadata.get_indicator_detail(IndicatorCode)
        lg, ug = detail["LowerGoalpost"], detail["UpperGoalpost"]
        lg = 0 if not lg else lg  # if the indicator doesn't have goalposts, it's an aggregate index
        ug = 1 if not ug else ug  # if the indicator doesn't have goalposts, it's an aggregate index
        indicator_dict = {}
        data = sspi_clean_api_data.find(
            {"IndicatorCode": IndicatorCode},
            {"_id": 0}
        )
        min_year = 2000
        max_year = datetime.now().year
        label_list = list(range(min_year, max_year + 1))
        for observation in data:
            CountryCode = observation["CountryCode"]
            if CountryCode not in indicator_dict.keys():
                indicator_dict[CountryCode] = []
            indicator_dict[CountryCode].append(observation)
        for CountryCode, document in indicator_dict.items():
            document = sorted(document, key=lambda x: x["Year"])
            group_list = sspi_metadata.get_country_groups(CountryCode)
            years = [None] * len(label_list)
            scores = [None] * len(label_list)
            values = [None] * len(label_list)
            data = [None] * len(label_list)
            for doc in document:
                try:
                    year_index = label_list.index(doc["Year"])
                except ValueError:
                    continue
                years[year_index] = doc["Year"]
                data[year_index] = doc["Score"]
                scores[year_index] = doc["Score"]
                values[year_index] = doc["Value"]
                data[year_index] = doc["Score"]
            document = {
                "CCode": CountryCode,
                "CName": country_code_to_name(CountryCode),
                "ICode": IndicatorCode,
                "IName": detail["Indicator"],
                "CatCode": detail["CategoryCode"],
                "CatName": detail["Category"],
                "PilCode": detail["PillarCode"],
                "PilName": detail["Pillar"],
                "CGroup": group_list,
                "parsing": {
                    "xAxisKey": "years",
                    "yAxisKey": "scores"
                },
                "pinned": False,
                "hidden": "SSPI49" not in group_list,
                "label": f"{CountryCode} - {country_code_to_name(CountryCode)}",
                "years": years,
                "minYear": min_year,
                "maxYear": max_year,
                "data": data,
                "score": scores,
                "value": values,
                "yAxisMinValue": lg * 0.95 if lg > 0 else lg * 1.05,
                "yAxisMaxValue": ug * 1.05 if ug > 0 else ug * 0.95
            }
            sspi_dynamic_line_data.insert_one(document)
        count += 1


@finalize_bp.route("/production/finalize/dynamic/matrix")
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
    collect_implemented = [r.group(0) for r in [re.search(
        r'(?<=api/v1/collect/)(?!static)[\w]*', r)
        for r in endpoints] if r is not None
    ]
    compute_implemented = [r.group(0) for r in [re.search(
        r'(?<=api/v1/compute/)(?!static)[\w]*', r)
        for r in endpoints] if r is not None
    ]
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
    result = sspi_clean_api_data.aggregate(pipeline)
    sspi49_countries = sspi_metadata.country_group("SSPI49")
    sspi_extended_countries = sspi_metadata.country_group("SSPIExtended")
    indicator_details, indicator_map = sspi_metadata.indicator_details(), {}
    for detail in indicator_details:
        indicator_map[detail["IndicatorCode"]] = {
            "collect": detail["IndicatorCode"] in collect_implemented,
            "compute": detail["IndicatorCode"] in compute_implemented,
            "problems": detail["IndicatorCode"] in problems.keys(),
            "confident": detail["IndicatorCode"] in confident.keys(),
            "IName": detail["Indicator"],
            "CatCode": detail["CategoryCode"],
            "CatName": detail["Category"],
            "PilCode": detail["PillarCode"],
            "PilName": detail["Pillar"]
        }
    count = 1
    for obs in result:
        indicator_code = obs["IndicatorCode"]
        country = obs["CountryCode"]
        sspi_dynamic_matrix_data.insert_one({
            "x": indicator_code,
            "y": country,
            "v": obs["yearCount"],
            "problems": indicator_map[indicator_code]["problems"],
            "confident": indicator_map[indicator_code]["confident"],
            "collect": indicator_map[indicator_code]["collect"],
            "compute": indicator_map[indicator_code]["compute"],
            "IName": indicator_map[indicator_code]["IName"],
            "CatCode": indicator_map[indicator_code]["CatCode"],
            "CatName": indicator_map[indicator_code]["CatName"],
            "PilCode": indicator_map[indicator_code]["PilCode"],
            "PilName": indicator_map[indicator_code]["PilName"],
            "SSPI49": country in sspi49_countries,
            "SSPIExtended": country in sspi_extended_countries,
            "CName": country_code_to_name(country)
        })
        if count % 100 == 0 or count == len(result):
            yield f"Finalizing Observation {count} / {len(result)}\n"
        count += 1


@finalize_bp.route("/production/finalize/dynamic/score")
@login_required
def finalize_sspi_dynamic_score():
    """
    Prepare the data for a Chart.js line plot
    """
    countries = request.args.getlist("CountryCode")
    country_group = request.args.get("CountryGroup")
    coverage = DataCoverage(2000, 2023, country_group, countries=countries)
    indicator_list = coverage.complete()
    country_list = coverage.country_codes
    app.logger.info(f"country_list: {country_list}")
    app.logger.info(f"indicator_list: {indicator_list}")
    return Response(finalize_sspi_dynamic_score_iterator(indicator_list, country_list), mimetype='text/event-stream')


def finalize_sspi_dynamic_score_iterator(indicator_codes: list[str], country_codes: list[str] = None):
    mongo_query = {
        "CountryCode": {"$in": country_codes},
        "IndicatorCode": {"$in": indicator_codes},
        "Year": {"$gte": 2000, "$lte": 2023}
    }
    sspi_score_data.delete_many(mongo_query)
    details = sspi_metadata.indicator_details(filter=indicator_codes)
    clean_data = sspi_clean_api_data.find(mongo_query)
    imputed_data = sspi_imputed_data.find(mongo_query)
    yield "Building Data Map\n"
    data_map = {}
    for observation in clean_data + imputed_data:
        country_code = observation["CountryCode"]
        data_map.setdefault(country_code, {})
        data_map[country_code].setdefault(observation["Year"], {"Data": [], "SSPI": None})
        data_map[country_code][observation["Year"]]["Data"].append(observation)
    yield "Scoring Data\n"
    documents = []
    for country_code, year_data in data_map.items():
        print(year_data)
        for year, data in year_data.items():
            data["SSPI"] = SSPI(details, data["Data"])
            yield f"{country_code}: {year}: {data["SSPI"].score()}\n"
            documents.extend(data["SSPI"].score_documents())
    sspi_score_data.insert_many(documents)
