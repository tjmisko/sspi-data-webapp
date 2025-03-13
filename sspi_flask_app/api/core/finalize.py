from flask import Blueprint, jsonify, Response, stream_with_context
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    # sspi_imputed_data,
    sspi_metadata,
    sspi_main_data_v3,
    sspi_static_rank_data,
    sspi_static_radar_data,
    sspi_static_stack_data,
    sspi_dynamic_line_data,
    sspi_dynamic_matrix_data
)
from sspi_flask_app.api.resources.utilities import (
    # parse_json,
    country_code_to_name,
    colormap
)
from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app.models.rank import SSPIRankingTable
import re
import os
import json
import pycountry


finalize_bp = Blueprint(
    'finalize_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


def finalize_iterator():
    yield "Finalizing Static Rank Data\n"
    finalize_sspi_static_rank_data()
    yield "Finalizing Static Radar Data\n"
    finalize_sspi_static_radar_data()
    yield "Finalizing Dynamic Line Data\n"
    finalize_sspi_dynamic_line_data()
    yield "Finalizing Dynamic Matrix Data\n"
    finalize_dynamic_matrix_data()
    yield "Finalizing Static Stack Data\n"
    finalize_static_overall_stack_data()
    yield "Finalization Complete\n"


@finalize_bp.route("/production/finalize")
@login_required
def finalize_all_production_data():
    return Response(
        stream_with_context(finalize_iterator()),
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
    country_codes = sspi_metadata.country_group("SSPI49")
    indicator_details = sspi_metadata.indicator_details()
    sspi_item_codes = ["SSPI"] + sspi_metadata.pillar_codes() + \
        sspi_metadata.category_codes() + \
        sspi_metadata.indicator_codes()
    score_group_dictionary = {
        item_code: [
            {"CCode": "", "Score": 0, "Rank": 0,
                "IName": "", "ICode": "", "Year": 0}
            for _ in country_codes]
        for item_code in sspi_item_codes}
    for i, cou in enumerate(country_codes):
        country_data = sspi_main_data_v3.find({"CountryCode": cou})
        cname = country_code_to_name(cou)
        sspi_scores = SSPI(indicator_details, country_data)
        score_group_dictionary["SSPI"][i]["CCode"] = cou
        score_group_dictionary["SSPI"][i]["Score"] = sspi_scores.score()
        score_group_dictionary["SSPI"][i]["IName"] = "SSPI"
        score_group_dictionary["SSPI"][i]["Year"] = 2018
        for pillar in sspi_scores.pillars:
            score_group_dictionary[pillar.code][i]["CCode"] = cou
            score_group_dictionary[pillar.code][i]["Score"] = pillar.score()
            score_group_dictionary[pillar.code][i]["IName"] = pillar.name
            score_group_dictionary[pillar.code][i]["Year"] = 2018
            for category in pillar.categories:
                score_group_dictionary[category.code][i]["CCode"] = cou
                score_group_dictionary[category.code][i]["Score"] = category.score()
                score_group_dictionary[category.code][i]["IName"] = category.name
                score_group_dictionary[category.code][i]["Year"] = 2018
                for indicator in category.indicators:
                    score_group_dictionary[indicator.code][i]["CCode"] = cou
                    score_group_dictionary[indicator.code][i]["Score"] = indicator.score
                    score_group_dictionary[indicator.code][i]["IName"] = indicator.name
                    score_group_dictionary[indicator.code][i]["Year"] = indicator.year
                    score_group_dictionary[indicator.code][i]["Value"] = indicator.value
                    score_group_dictionary[indicator.code][i]["LowerGoalpost"] = indicator.lower_goalpost
                    score_group_dictionary[indicator.code][i]["UpperGoalpost"] = indicator.upper_goalpost
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


@finalize_bp.route("/production/finalize/dynamic/line")
@login_required
def finalize_sspi_dynamic_line_data():
    """
    Prepare the data for a Chart.js line plot
    """
    sspi_dynamic_line_data.delete_many({})
    for IndicatorCode in sspi_metadata.indicator_codes():
        detail = sspi_metadata.get_detail(IndicatorCode)["Metadata"]
        indicator_dict = {}
        data = sspi_clean_api_data.find(
            {"IndicatorCode": IndicatorCode},
            {"_id": 0}
        )
        year_list = [int(o["Year"]) for o in data]
        if len(year_list) == 0:
            continue
        print(IndicatorCode, len(year_list))
        min_year = min(year_list)
        max_year = max(year_list)
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
                year_index = label_list.index(doc["Year"])
                years[year_index] = doc["Year"]
                scores[year_index] = doc["Score"]
                values[year_index] = doc["Value"]
                data[year_index] = doc["Score"]
            document = {
                "CCode": CountryCode,
                "CName": country_code_to_name(CountryCode),
                "ICode": IndicatorCode,
                "IName": detail["Indicator"],
                "spanGaps": True,
                "CatCode": detail["CategoryCode"],
                "CatName": detail["Category"],
                "PilCode": detail["PillarCode"],
                "PilName": detail["Pillar"],
                "CGroup": group_list,
                "pinned": False,
                "hidden": (lambda group_list: False
                           if "SSPI49" in group_list
                           else True)(group_list),
                "label": f"{country_code_to_name(CountryCode)} ({CountryCode})",
                "years": years,
                "minYear": min_year,
                "maxYear": max_year,
                "scores": scores,
                "data": data,
                "values": values
            }
            sspi_dynamic_line_data.insert_one(document)
    return jsonify(sspi_dynamic_line_data.find({}, {"_id": 0}))


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
    indicator_details = sspi_metadata.indicator_details()
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


def production_data_by_indicator():
    """
    Minification is important for production data to minimize response times

    IndicatorCode -> IDCode
    CountryCode -> CCode
    CountryName -> CName
    Intermediates -> Intrmdts
    IntermediateCode -> IMCode
    """
    return "0"


@finalize_bp.route("/production/finalize/dynamic/matrix")
@login_required
def finalize_dynamic_matrix_data():
    sspi_dynamic_matrix_data.delete_many({})
    local_path = os.path.join(os.path.dirname(app.instance_path), "local")
    with open(os.path.join(local_path, "indicator-problems.json")) as f:
        problems = json.load(f)
    with open(os.path.join(local_path, "indicator-local-load.json")) as f:
        to_be_loaded = json.load(f)
    with open(os.path.join(local_path, "indicator-confident.json")) as f:
        confident = json.load(f)
    indicator_details = sspi_metadata.indicator_details()
    endpoints = [str(r) for r in app.url_map.iter_rules()]
    collect_implemented = [r.group(0) for r in [re.search(
        r'(?<=api/v1/collect/)(?!static)[\w]*', r)
        for r in endpoints] if r is not None
    ]
    compute_implemented = [r.group(0) for r in [re.search(
        r'(?<=api/v1/compute/)(?!static)[\w]*', r)
        for r in endpoints] if r is not None
    ]
    countries = sspi_metadata.country_group("SSPI49")
    final_data = []
    for detail in indicator_details:
        indicator_code = detail["Metadata"]["IndicatorCode"]
        for country in countries:
            stored_observations = sspi_clean_api_data.find(
                {"IndicatorCode": indicator_code, "CountryCode": country}
            )
            final_data.append(
                {
                    "x": indicator_code,
                    "collect": indicator_code in collect_implemented,
                    "compute": indicator_code in compute_implemented,
                    "problems": (lambda code:
                                 problems[indicator_code]
                                 if code in problems.keys()
                                 else None)(indicator_code),
                    "to_be_loaded": (lambda code:
                                     to_be_loaded[indicator_code]
                                     if code in to_be_loaded.keys()
                                     else None)(indicator_code),
                    "confident": (lambda code:
                                  confident[indicator_code]
                                  if code in confident.keys()
                                  else None)(indicator_code),
                    "IName": detail["Metadata"]["Indicator"],
                    "CatCode": detail["Metadata"]["CategoryCode"],
                    "CatName": detail["Metadata"]["Category"],
                    "PilCode": detail["Metadata"]["PillarCode"],
                    "PilName": detail["Metadata"]["Pillar"],
                    "y": country,
                    "CName": country_code_to_name(country),
                    "v": len(stored_observations)
                }
            )
    count = sspi_dynamic_matrix_data.insert_many(final_data)
    # sspi_dynamic_matrix_data
    return f"Inserted {count} documents into sspi_dynamic_matrix_data"


@finalize_bp.route("/production/finalize/static/stack")
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
        "data": [c["Score"]/3 for c in sus_scores],
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
        "data": [c["Score"]/3 for c in ms_scores],
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
        "data": [c["Score"]/3 for c in pg_scores],
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
