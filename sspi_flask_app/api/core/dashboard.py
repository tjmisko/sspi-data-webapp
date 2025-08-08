from sspi_flask_app.api.resources.utilities import (
    parse_json,
    lookup_database,
    country_code_to_name,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    generate_series_levels,
    generate_series_groups,
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
from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app.models.coverage import DataCoverage
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_main_data_v3,
    sspi_item_data,
    sspi_metadata,
    sspi_panel_data,
    sspi_static_rank_data,
    sspi_static_radar_data,
    sspi_static_stack_data,
    sspi_indicator_dynamic_line_data,
    sspi_item_dynamic_line_data,
    sspi_dynamic_matrix_data,
)
from datetime import datetime
import hashlib

dashboard_bp = Blueprint(
    "dashboard_bp", __name__, template_folder="templates", static_folder="static"
)


@dashboard_bp.route("/status/database/<database>")
@login_required
def get_database_status(database):
    ndocs = lookup_database(database).count_documents({})
    return render_template("database-status.html", database=database, ndocs=ndocs)


@dashboard_bp.route("/compare")
@login_required
def compare():
    details = sspi_metadata.indicator_details()
    option_details = []
    for indicator in details:
        option_details.append(
            {key: indicator[key] for key in ["IndicatorCode", "Indicator"]}
        )
    return render_template("compare.html", indicators=option_details)


@dashboard_bp.route("/static/indicator/<IndicatorCode>")
def get_static_indicator_data(IndicatorCode):
    """
    Get the static data for the given indicator code
    """
    static_data = parse_json(
        sspi_main_data_v3.find({"IndicatorCode": IndicatorCode}, {"_id": 0})
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
    name_map = {
        detail["ItemCode"]: detail["ItemName"] for detail in indicator_details
    }
    active_schema = sspi_item_data.active_schema(name_map=name_map)
    detail = sspi_metadata.get_item_detail(indicator_code)
    doc_type = detail.get("ItemType", "No Item Type")
    print("Document Type:", doc_type)
    if not doc_type == "Indicator":
        return jsonify({"error": "Invalid Item Type for dynamic indicator data"}), 400
    item_options = sspi_metadata.indicator_options()
    name = detail.get("ItemName")
    description = detail.get("Description", "")
    country_query = request.args.getlist("CountryCode")
    query = {"ICode": indicator_code}
    if country_query:
        query["CCode"] = {"$in": country_query}
    dynamic_score_data = sspi_indicator_dynamic_line_data.find(query)
    available_datasets = list(dynamic_score_data[0].get("Datasets", []))
    dataset_options = []
    for dscode in available_datasets:
        detail = sspi_metadata.get_dataset_detail(dscode)
        ds_range = detail.get("Range", {})
        if ds_range:
            dataset_options.append({
                "datasetCode": dscode,
                "datasetDescription": detail.get("Description", ""),
                "unit": detail.get("Unit", ""),
                "yMin": ds_range.get("yMin", 0),
                "yMax": ds_range.get("yMax", 1),
            })
        else:
            dataset_options.append({
                "datasetCode": dscode,
                "datasetDescription": detail.get("Description", ""),
                "unit": detail.get("Unit", ""),
                "yMin": 0,
                "yMax": 1,
            })
    year_labels = list(range(2000, datetime.now().year + 1))  # Default to 2000-present
    if dynamic_score_data:
        min_year = dynamic_score_data[0]["minYear"]
        max_year = dynamic_score_data[0]["maxYear"]
        year_labels = [str(year) for year in range(min_year, max_year + 1)]
    chart_title = f"{name} ({indicator_code}) Score"
    group_options = sspi_metadata.country_groups()
    return jsonify(
        {
            "data": dynamic_score_data,
            "title": chart_title,
            "labels": year_labels,
            "description": description,
            "groupOptions": group_options,
            "itemOptions": item_options,
            "itemType": doc_type,
            "itemCode": indicator_code,
            "datasetOptions": dataset_options,
            "tree": active_schema,
        }
    )


@dashboard_bp.route("/panel/score/<item_code>", methods=["GET"])
def get_dynamic_score_line_data(item_code):
    """
    Get the dynamic data for the given category code for a line chart
    """
    indicator_details = sspi_metadata.indicator_details()
    name_map = {
        detail["ItemCode"]: detail["ItemName"] for detail in indicator_details
    }
    active_schema = sspi_item_data.active_schema(name_map=name_map)
    detail = sspi_metadata.get_item_detail(item_code)
    print(detail)
    doc_type = detail.get("ItemType", "No Item Type")
    print("Document Type:", doc_type)
    if doc_type == "Indicator":
        item_options = sspi_metadata.indicator_options()
    elif doc_type == "Category":
        item_options = sspi_metadata.category_options()
    elif doc_type == "Pillar":
        item_options = sspi_metadata.pillar_options()
    else:
        item_options = []
    name = detail["ItemName"]
    description = detail.get("Description", "")
    country_query = request.args.getlist("CountryCode")
    query = {"ICode": item_code}
    if country_query:
        query["CCode"] = {"$in": country_query}
    dynamic_score_data = parse_json(sspi_item_dynamic_line_data.find(query))
    year_labels = list(range(2000, datetime.now().year + 1))  # Default to 2000-present
    if dynamic_score_data:
        min_year = dynamic_score_data[0]["minYear"]
        max_year = dynamic_score_data[0]["maxYear"]
        year_labels = [str(year) for year in range(min_year, max_year + 1)]
    chart_title = f"{name} ({item_code}) Score"
    group_options = sspi_metadata.country_groups()
    return jsonify(
        {
            "data": dynamic_score_data,
            "title": chart_title,
            "labels": year_labels,
            "description": description,
            "groupOptions": group_options,
            "itemOptions": item_options,
            "itemType": doc_type,
            "itemCode": item_code,
            "tree": active_schema,
        }
    )


@dashboard_bp.route("/static/radar/<CountryCode>")
def get_static_radar_data(CountryCode):
    radar_data = sspi_static_radar_data.find_one({"CCode": CountryCode})
    return jsonify(radar_data)


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
    indicator_details = sspi_metadata.indicator_details()
    base_country_data = parse_json(
        sspi_main_data_v3.find({"CountryCode": base_country}, {"_id": 0})
    )
    base_sspi = SSPI(indicator_details, base_country_data, strict_year=False)
    base_pillar = base_sspi.get_pillar(pillar_code)
    comparison_country_data = parse_json(
        sspi_main_data_v3.find({"CountryCode": comparison_country}, {"_id": 0})
    )
    comparison_sspi = SSPI(
        indicator_details, comparison_country_data, strict_year=False
    )
    comparison_pillar = comparison_sspi.get_pillar(pillar_code)
    by_category = []
    by_indicator = []
    assert base_pillar is not None
    assert comparison_pillar is not None
    for category in base_pillar.categories:
        category_code = category.code
        comparison_category = comparison_pillar.get_category(category_code)
        base_score = category.score()
        comparison_score = comparison_category.score()
        for indicator in category.indicators:
            indicator_code = indicator.code
            base_indicator_score = indicator.score
            comparison_indicator = comparison_category.get_indicator(indicator.code)
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
    indicator_details = sspi_metadata.indicator_details()
    datasets = []
    labels = []
    code_map = {}
    pillar_name = ""
    for i, cou in enumerate(country_codes):
        cou_data = parse_json(sspi_main_data_v3.find({"CountryCode": cou}, {"_id": 0}))
        cou_sspi = SSPI(indicator_details, cou_data, strict_year=False)
        cou_pillar = cou_sspi.get_pillar(pillar_code)
        assert cou_pillar is not None, f"Pillar {pillar_code} not found for country {cou}"
        if i == 0:
            pillar_name = cou_pillar.name
        country_lookup = pycountry.countries.get(alpha_3=cou) 
        assert country_lookup is not None, "Country not found"
        country_name = country_lookup.name
        country_flag = country_lookup.flag
        code_map[cou] = {"name": country_name, "flag": country_flag}
        for j, category in enumerate(cou_pillar.categories):
            # Only add the category label once
            if i == 0:
                labels.append(category.name)
            for indicator in category.indicators:
                dataset = {}
                indicator_rank = sspi_static_rank_data.find_one(
                    {"ICode": indicator.code, "CCode": cou}, {"_id": 0}
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
        {"title": "SSPI Overall Scores by Country", "data": score_data["data"]}
    )


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
                if field_type == 'value':
                    # We previously saw values, now seeing scores - mixed data
                    yield "error: Inconsistent data detected! Some observations have scores while others have values.\n"
                    yield "Panel plots require all observations to use the same field type.\n"
                    yield "Filter your data to include only scores or only values.\n"
                    return
                field_type = 'score'
            elif obs_has_value:
                if field_type == 'score':
                    # We previously saw scores, now seeing values - mixed data
                    yield "error: Inconsistent data detected! Some observations have scores while others have values.\n"
                    yield "Panel plots require all observations to use the same field type.\n"
                    yield "Filter your data to include only scores or only values.\n"
                    return
                field_type = 'value'
        
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
                    value[year_index] = doc.get("value_id", None) if "value_id" in doc else None
                    score[year_index] = doc.get("score_id", None) if "score_id" in doc else None
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
    year_labels = [str(year) for year in range(min_year, max_year + 1)]
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


@dashboard_bp.route("/country/dynamic/stack/<CountryCode>/<RootItemCode>")
def dynamic_stack_data(CountryCode, RootItemCode):
    """
    Get the dynamic data for the given country code and root item code
    """
    root_item_detail = sspi_metadata.get_item_detail(RootItemCode)
    child_items = sspi_metadata.get_child_details(RootItemCode)
    child_codes = [child["Metadata"]["ItemCode"] for child in child_items]
    stack_div = len(child_codes)
    mongo_query = {
        "CCode": CountryCode,
        "ICode": {"$in": child_codes + [RootItemCode]},
    }
    data = sspi_item_dynamic_line_data.find(mongo_query)
    year_labels = list(range(2000, datetime.now().year + 1))
    for document in data:
        if document["ICode"] == RootItemCode:
            document["hidden"] = True
        else:
            document["divisor"] = stack_div
            document["data"] = [s / stack_div for s in document["score"]]
            document["fill"] = "stack"
    return parse_json(
        {
            "data": data,
            "title": f"{root_item_detail['ItemName']} ({RootItemCode}) for Country {CountryCode}",
            "labels": year_labels,
            "itemType": root_item_detail["DocumentType"][0:-6].lower(),
            "hasScore": True,
            "yMin": 0,
            "yMax": 1,
        }
    )

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
