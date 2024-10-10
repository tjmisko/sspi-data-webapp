from ..resources.utilities import parse_json, lookup_database
import json
from flask import (
    Blueprint,
    session,
    jsonify,
    request,
    render_template
)
from flask import current_app as app
from flask_login import login_required
from ... import (
    sspi_main_data_v3,
    sspi_metadata,
    sspi_static_radar_data,
    sspi_dynamic_line_data
)
import pandas as pd
import re
import os

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
    print(details)
    option_details = []
    for indicator in details:
        option_details.append({key: indicator[key] for key in [
                              "IndicatorCode", "Indicator"]})
    return render_template("compare.html", indicators=option_details)


@dashboard_bp.route('/compare/<IndicatorCode>')
def get_compare_data(IndicatorCode):
    # Prepare the main data
    main_data = parse_json(sspi_main_data_v3.find(
        {"IndicatorCode": IndicatorCode}, {"_id": 0}))
    main_data = pd.DataFrame(main_data)
    main_data = main_data.rename(columns={"Value": "sspi_static_raw"})
    # Prepare the dynamic data
    # dynamic_data = parse_json(sspi_production_data.find({"IndicatorCode": IndicatorCode, "Year": 2018, "CountryGroup": "SSPI49"}, {"_id": 0}))
    return jsonify(json.loads(str(main_data.to_json(orient="records"))))
    # dynamic_data = pd.DataFrame(dynamic_data)
    # dynamic_data["Value"].replace("NaN", np.nan, inplace=True)
    # dynamic_data["Value"].astype(float)
    # dynamic_data["Value"] = dynamic_data["Value"].round(3)
    # dynamic_data = dynamic_data.rename(columns={"Value": "sspi_dynamic_raw"})
    # # Merge the data
    # comparison_data = main_data.merge(dynamic_data, on=["CountryCode", "IndicatorCode", "YEAR"], how="left")
    # comparison_data = json.loads(str(comparison_data.to_json(orient="records")))
    # return jsonify(comparison_data)


@dashboard_bp.route('/api_coverage')
def api_coverage():
    """
    Return a list of all endpoints and whether they are implemented
    """
    all_indicators = sspi_metadata.indicator_codes()
    endpoints = [str(r) for r in app.url_map.iter_rules()]
    collect_implemented = [r.group(0) for r in [re.search(
        r'(?<=api/v1/collect/)(?!static)[\w]*', r) for r in endpoints] if r is not None]
    compute_implemented = [r.group(0) for r in [re.search(
        r'(?<=api/v1/compute/)(?!static)[\w]*', r) for r in endpoints] if r is not None]
    coverage_data_object = []
    for indicator in all_indicators:
        coverage_data_object.append({
            "IndicatorCode": indicator,
            "collect_implemented": indicator in collect_implemented,
            "compute_implemented": indicator in compute_implemented
        })
    return parse_json(coverage_data_object)


@dashboard_bp.route("/local")
@login_required
def local():
    return render_template('local-upload-form.html', database_names=check_for_local_data())


@dashboard_bp.route("/local/database/list", methods=['GET'])
@login_required
def check_for_local_data():
    app.instance_path
    try:
        database_files = os.listdir(os.path.join(os.getcwd(), 'local'))
    except FileNotFoundError:
        database_files = os.listdir("/var/www/sspi.world/local")
    database_names = [db_file.split(".")[0] for db_file in database_files]
    return parse_json(database_names)


@dashboard_bp.route("/fetch-controls")
@login_required
def api_internal_buttons():
    implementation_data = api_coverage()
    return render_template("dashboard-controls.html",
                           implementation_data=implementation_data)


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


@dashboard_bp.route('/dynamic/line/<IndicatorCode>', methods=["GET", "POST"])
def get_dynamic_indicator_line_data(IndicatorCode):
    """
    Get the dynamic data for the given indicator code for a line chart
    """
    def validate_preferences(preferences):
        if not preferences:
            return None
        if not preferences.get("pinnedArray"):
            return None
        return preferences

    if request.method == "POST":
        chart_preferences = request.get_json()
        print(type(chart_preferences))
        session["chart_preferences"] = chart_preferences
        return "Preferences saved"
    else:
        chart_preferences = session.get("chart_preferences")
        chart_preferences = validate_preferences(chart_preferences)
        if chart_preferences is None:
            chart_preferences = {"pinnedArray": []}
        country_query = request.args.getlist("CountryCode")
        query = {"ICode": IndicatorCode}
        if country_query:
            query["CCode"] = {"$in": country_query}
        dynamic_indicator_data = parse_json(
            sspi_dynamic_line_data.find(query, {"_id": 0})
        )
        min_year, max_year = 9999, 0
        for document in dynamic_indicator_data:
            min_year = min(min_year, min(document["years"]))
            max_year = max(max_year, max(document["years"]))
        year_labels = [str(year) for year in range(min_year, max_year + 1)]
        if not dynamic_indicator_data:
            return jsonify({"error": "No data found"})
        chart_title = f"{dynamic_indicator_data[0]["IName"]} ({
            IndicatorCode}) Score"
        group_options = sspi_metadata.country_groups()
        return jsonify({
            "data": dynamic_indicator_data,
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
            "groupOptions": group_options,
            "chartPreferences": chart_preferences
        })


@dashboard_bp.route('/static/radar/<CountryCode>')
def get_static_radar_data(CountryCode):
    radar_data = sspi_static_radar_data.find_one({"CountryCode": CountryCode})
    return jsonify(radar_data)
