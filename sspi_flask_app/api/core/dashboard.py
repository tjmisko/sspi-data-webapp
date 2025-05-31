from sspi_flask_app.api.resources.utilities import (
    parse_json,
    lookup_database,
    country_code_to_name,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    generate_item_levels,
    generate_item_groups
)
import pycountry
import json
from flask import (
    Blueprint,
    Response,
    jsonify,
    request,
    render_template,
    current_app as app
)
from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app.models.coverage import DataCoverage
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_main_data_v3,
    sspi_metadata,
    sspi_panel_data,
    sspi_static_rank_data,
    sspi_static_radar_data,
    sspi_static_stack_data,
    sspi_dynamic_line_data,
    sspi_dynamic_matrix_data
)
import os
from datetime import datetime
import hashlib

dashboard_bp = Blueprint(
    'dashboard_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@dashboard_bp.route("/status/database/<database>")
@login_required
def get_database_status(database):
    ndocs = lookup_database(database).count_documents({})
    return render_template(
        "database-status.html",
        database=database,
        ndocs=ndocs
    )


@dashboard_bp.route("/compare")
@login_required
def compare():
    details = sspi_metadata.indicator_details()
    option_details = []
    for indicator in details:
        option_details.append({key: indicator[key] for key in [
                              "IndicatorCode", "Indicator"]})
    return render_template("compare.html", indicators=option_details)


@dashboard_bp.route("/static/indicator/<IndicatorCode>")
def get_static_indicator_data(IndicatorCode):
    """
    Get the static data for the given indicator code
    """
    static_data = parse_json(sspi_main_data_v3.find(
        {"IndicatorCode": IndicatorCode}, {"_id": 0})
    )
    data_series = [{
        "Year": document["Year"],
        "CountryCode": document["CountryCode"],
        "Rank": document["Rank"],
        "Score": document["Score"],
        "Value": document["Value"]
    } for document in static_data]
    labels = [document["CountryCode"] for document in static_data]
    chart_data = {
        "labels": labels,
        "datasets": [{
            "label": "Score",
            "data": data_series,
            "parsing": {
                "xAxisKey": "Rank",
                "yAxisKey": "Score"
            }
        }]
    }
    return jsonify(chart_data)


@dashboard_bp.route('/panel/score/<ItemCode>', methods=["GET"])
def get_dynamic_score_line_data(ItemCode):
    """
    Get the dynamic data for the given category code for a line chart
    """
    detail = sspi_metadata.get_item_detail(ItemCode)
    doc_type = detail["DocumentType"]
    if doc_type == "IndicatorDetail":
        item_options = sspi_metadata.indicator_options()
    elif doc_type == "CategoryDetail":
        item_options = sspi_metadata.category_options()
    elif doc_type == "PillarDetail":
        item_options = sspi_metadata.pillar_options()
    else:
        item_options = []
    name = detail["ItemName"]
    description = detail.get("Description", "")
    country_query = request.args.getlist("CountryCode")
    
    query = {"ICode": ItemCode}
    if country_query:
        query["CCode"] = {"$in": country_query}
    dynamic_score_data = parse_json(
        sspi_dynamic_line_data.find(query)
    )
    year_labels = list(range(2000, datetime.now().year + 1))  # Default to 2000-present
    if dynamic_score_data:
        min_year = dynamic_score_data[0]["minYear"]
        max_year = dynamic_score_data[0]["maxYear"]
        year_labels = [str(year) for year in range(min_year, max_year + 1)]
    chart_title = f"{name} ({ItemCode}) Score"
    group_options = sspi_metadata.country_groups()
    return jsonify({
        "data": dynamic_score_data,
        "title": {
            "display": True,
            "text": chart_title,
            "font": {
                "size": 18
            },
            "color": "#ccc",
            "align": "start"
        },
        "labels": year_labels,
        "description": description,
        "groupOptions": group_options,
        "hasScore": True,
        "itemOptions": item_options
    })


@dashboard_bp.route('/static/radar/<CountryCode>')
def get_static_radar_data(CountryCode):
    radar_data = sspi_static_radar_data.find_one({"CCode": CountryCode})
    return jsonify(radar_data)


@dashboard_bp.route('/dynamic/matrix/<country_group>')
def get_dynamic_matrix_data(country_group):
    countries = sspi_metadata.country_group(country_group)
    data = sspi_dynamic_matrix_data.find(
        {"y": {"$in": countries}}, {"_id": 0}
    )
    return jsonify({
        "data": data,
        "icodes": sspi_metadata.indicator_codes(),
        "ccodes": countries
    })


@dashboard_bp.route('/static/differential/pillar/<pillar_code>')
def get_static_pillar_differential(pillar_code):
    """
    Get the static category data
    """
    base_country = request.args.get("BaseCountry")
    comparison_country = request.args.get("ComparisonCountry")
    if not (base_country and comparison_country):
        return jsonify({
            "error": "BaseCountry and ComparisonCountry are required URL parameters."
        }), 400
    if base_country == "undefined" or comparison_country == "undefined":
        return jsonify({
            "error": "BaseCountry and ComparisonCountry must not be undefined"
        }), 400
    indicator_details = sspi_metadata.indicator_details()
    base_country_data = parse_json(
        sspi_main_data_v3.find(
            {"CountryCode": base_country},
            {"_id": 0}
        )
    )
    base_sspi = SSPI(indicator_details, base_country_data)
    base_pillar = base_sspi.get_pillar(pillar_code)
    comparison_country_data = parse_json(
        sspi_main_data_v3.find(
            {"CountryCode": comparison_country},
            {"_id": 0}
        )
    )
    comparison_sspi = SSPI(indicator_details, comparison_country_data)
    comparison_pillar = comparison_sspi.get_pillar(pillar_code)
    by_category = []
    by_indicator = []
    for category in base_pillar.categories:
        category_code = category.code
        comparison_category = comparison_pillar.get_category(category_code)
        base_score = category.score()
        comparison_score = comparison_category.score()
        for indicator in category.indicators:
            indicator_code = indicator.code
            base_indicator_score = indicator.score
            comparison_indicator = comparison_category.get_indicator(
                indicator.code)
            comparison_indicator_score = comparison_indicator.score
            by_indicator.append({
                "IndicatorCode": indicator_code,
                "BaseScore": base_indicator_score,
                "ComparisonScore": comparison_indicator_score,
                "Diff": comparison_indicator_score - base_indicator_score,
            })
        by_category.append({
            "label": category_code,
            "CategoryCode": category_code,
            "CategoryName": category.name,
            "baseScore": base_score,
            "comparisonScore": comparison_score,
            "Diff": comparison_score - base_score,
        })
    by_category.sort(key=lambda x: x["Diff"])
    by_indicator.sort(key=lambda x: x["Diff"])
    base_country_name = pycountry.countries.get(alpha_3=base_country).name
    comparison_country_name = pycountry.countries.get(
        alpha_3=comparison_country).name
    return jsonify({
        "labels": [c["CategoryCode"] for c in by_category],
        "datasets": [
            {
                "label": "Category Differential",
                "data": by_category
            },
            {
                "label": "Indicator Differential",
                "data": by_indicator,
                "hidden": True
            }
        ],
        "title": f"Category Score Difference ({comparison_country} - {base_country})",
        "baseCCode": base_country,
        "baseCName": base_country_name,
        "comparisonCCode": comparison_country,
        "comparisonCName": comparison_country_name,
    })


@dashboard_bp.route('/static/stacked/pillar/<pillar_code>')
def get_static_pillar_stack(pillar_code):
    country_codes = request.args.getlist("CountryCode")
    if not (country_codes):
        return jsonify({
            "error": "CountryCode URL Parameter not provided"
        }), 400
    if "undefined" in country_codes:
        return jsonify({
            "error": "CountryCode URL Parameter must not be undefined"
        }), 400
    indicator_details = sspi_metadata.indicator_details()
    datasets = []
    labels = []
    code_map = {}
    pillar_name = ""
    for i, cou in enumerate(country_codes):
        cou_data = parse_json(
            sspi_main_data_v3.find(
                {"CountryCode": cou},
                {"_id": 0}
            )
        )
        cou_sspi = SSPI(indicator_details, cou_data)
        cou_pillar = cou_sspi.get_pillar(pillar_code)
        if i == 0:
            pillar_name = cou_pillar.name
        country_name = pycountry.countries.get(alpha_3=cou).name
        country_flag = pycountry.countries.get(alpha_3=cou).flag
        code_map[cou] = {"name": country_name, "flag": country_flag}
        for j, category in enumerate(cou_pillar.categories):
            # Only add the category label once
            if i == 0:
                labels.append(category.name)
            for indicator in category.indicators:
                dataset = {}
                indicator_rank = sspi_static_rank_data.find_one(
                    {"ICode": indicator.code, "CCode": cou},
                    {"_id": 0}
                )["Rank"]
                data = [None] * len(cou_pillar.categories)
                n_indicators = len(category.indicators)
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
    return jsonify({
        "labels": labels,
        "datasets": datasets,
        "title": f"{pillar_name} Score Breakdown by Category and Indicator",
        "codeMap": code_map
    })


@dashboard_bp.route("/static/bar/score/<item_code>")
def get_static_score_item(item_code):
    score_data = sspi_static_rank_data.find({"ICode": item_code})
    item_name = score_data[0]["IName"]
    score_data_formatted = {
        "label": item_name,
        "data": [document["Score"] for document in score_data],
        "info": score_data,
    }
    return jsonify({
        "itemCode": item_code,
        "data": {
            "labels": [document["CName"] + " " + document["CFlag"]
                       for document in score_data],
            "datasets": [score_data_formatted]
        },
        "title": f"{item_name} Score by Country",
        "xTitle": f"{item_name} Score"
    })


@dashboard_bp.route("/static/stacked/sspi")
def get_static_stacked_sspi():
    score_data = sspi_static_stack_data.find_one({}, {"_id": 0})
    return jsonify({
        "title": "SSPI Overall Scores by Country",
        "data": score_data["data"]
    })


@dashboard_bp.route("/utilities/extrapolate/backward/<int:year>", methods=["POST"])
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
    item_level_dict = generate_item_levels(
        data,
        exclude_fields=exclude_fields,
        entity_id=entity_id,
        time_id=time_id,
        value_id=value_id,
        score_id=score_id
    )
    return parse_json(item_level_dict)


@dashboard_bp.route("/utilities/panel/plot", methods=["POST"])
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
    if not all(isinstance(item, dict) for item in data):
        return jsonify({"error": "All items in data must be dictionaries"}), 400

    def prepare_panel_data_iterator(data, exclude_fields, entity_id, time_id, value_id, score_id):
        sspi_panel_data.delete_many({})
        item_group_list = generate_item_groups(
            data,
            exclude_fields=exclude_fields,
            entity_id=entity_id,
            time_id=time_id,
            value_id=value_id,
            score_id=score_id
        )
        if len(item_group_list) > 30:
            yield "error: Too many levels (>30) to display! Run `sspi panel levels` to find levels to filter.\n"
            return jsonify({"error": "Too many items to display"})
        yield "================\n"
        count = 1
        for item in item_group_list:
            min_year = 2000
            max_year = datetime.now().year
            label_list = list(range(min_year, max_year + 1))
            identifiers = item["Identifier"]
            identifier_string = json.dumps(identifiers).encode('utf-8')
            id_hash = hashlib.sha1(identifier_string).hexdigest()
            yield "Identifier Hash: " + id_hash + "\n\n"
            for k, v in identifiers.items():
                yield f"{k}: {v}\n"
            yield "================\n"
            for cou, document in item["Datasets"].items():
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
                    value[year_index] = doc["value_id"]
                    data[year_index] = doc["value_id"]
                    score[year_index] = doc.get("score_id", None)
                document = {
                    "ItemIdentifier": id_hash,
                    "ItemOrder": count,
                    "CCode": cou,
                    "CName": country_code_to_name(cou),
                    "CGroup": group_list,
                    "parsing": {
                        "xAxisKey": "years",
                        "yAxisKey": "value"
                    },
                    "pinned": False,
                    "hidden": "SSPI49" not in group_list,
                    "label": f"{cou} - {country_code_to_name(cou)}",
                    "year": year,
                    "minYear": min_year,
                    "maxYear": max_year,
                    "data": data,
                    "value": value,
                }
                if any([s is not None for s in score]):
                    document["score"] = score
                document["Identifiers"] = identifiers
                sspi_panel_data.insert_one(document)
            count += 1
    return Response(
        prepare_panel_data_iterator(
            data, exclude_fields, entity_id, time_id, value_id, score_id
        ),
        mimetype='text/event-stream'
    )


@dashboard_bp.route("/view/panel")
def view_panel_plots():
    panel_data = sspi_panel_data.distinct("ItemIdentifier")
    return render_template("panel-utility.html", panel_id_list=panel_data)


@dashboard_bp.route("/panel/item/<panel_id>")
def get_panel_plot(panel_id):
    """
    Get the panel plot for a given panel id
    """
    def make_title(identifiers, panel_id):
        if "ItemCode" in identifiers.keys():
            return f"{identifiers['ItemCode']} (Item Hash: {panel_id})"
        if "IntermediateCode" in identifiers.keys():
            return f"{identifiers["IntermediateCode"]} (Item Hash: {panel_id})"
        if "IndicatorCode" in identifiers.keys():
            return f"{identifiers["IndicatorCode"]} (Item Hash: {panel_id})"
        return f"Panel Plot (Item Hash: {panel_id})"

    panel_data = sspi_panel_data.find({"ItemIdentifier": panel_id}, {"_id": 0})
    min_year = panel_data[0]["minYear"]
    max_year = panel_data[0]["maxYear"]
    has_score = panel_data[0].get("score", None) is not None
    identifiers = panel_data[0]["Identifiers"]
    year_labels = [str(year) for year in range(min_year, max_year + 1)]
    group_options = sspi_metadata.country_groups()
    yMin = 0
    yMax = 1
    for doc in panel_data:
        yMin = min(yMin, min([d for d in doc["value"] if d is not None]))
        yMax = max(yMax, max([d for d in doc["value"] if d is not None]))
    return jsonify({
        "data": panel_data,
        "title": {
            "display": True,
            "text": make_title(identifiers, panel_id),
            "font": {
                "size": 18
            },
            "color": "#ccc",
            "align": "start"
        },
        "labels": year_labels,
        "description": identifiers,
        "groupOptions": group_options,
        "hasScore": has_score,
        "yMin": yMin,
        "yMax": yMax
    })


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


@dashboard_bp.route("/utilities/coverage/report/indicator/<IndicatorCode>", methods=["GET"])
def coverage_indicator(IndicatorCode):
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).indicator_report(IndicatorCode)
    return coverage


@dashboard_bp.route("/utilities/coverage/report/country/<CountryCode>", methods=["GET"])
def coverage_country(CountryCode):
    group = request.args.get("CountryGroup", "SSPI67")
    coverage = DataCoverage(2000, 2023, group).country_report(CountryCode)
    return coverage
