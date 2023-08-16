from datetime import datetime
from ..api import api_bp, parse_json
import json
import math
from io import BytesIO
from flask import Blueprint, redirect, request, url_for, escape, send_file, current_app as app, render_template, flash, get_flashed_messages
from flask_login import current_user, fresh_login_required, login_required
from ...models.usermodel import User
from ... import sspi_main_data_v3, sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from bson import json_util
from pycountry import countries
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired
import pandas as pd
import numpy as np
import re
import os

@api_bp.route("/", methods=["GET"])
@login_required
def api_home():
    return render_template("api.html")

@api_bp.route("/status/database/<database>")
@login_required
def get_database_status(database):
    ndocs = lookup_database(database).count_documents({})
    return render_template("database_status.html", database=database, ndocs=ndocs)

@api_bp.route("/query")
def query_full_database():
    database = request.args.get('database', default = "sspi_main_data_v3", type = str)
    if database == "sspi_raw_api_data":
        return parse_json(sspi_raw_api_data.find())
    elif database == "sspi_clean_api_data":
        return parse_json(sspi_clean_api_data.find())
    else:  
        return parse_json(sspi_main_data_v3.find())

@api_bp.route("/query/indicator/<IndicatorCode>")
def query_indicator(IndicatorCode):
    """
    Take an indicator code and return the data
    """
    country_group = request.args.get('country_group', default = "all", type = str)
    if country_group != "all":

        query_parameters = {"CountryGroup": country_group}
    database = request.args.get('database', default = "sspi_main_data_v3", type = str)
    if database == "sspi_raw_api_data":
        indicator_data = sspi_raw_api_data.find({"collection-info.RawDataDestination": IndicatorCode})
    elif database == "sspi_clean_api_data":
        indicator_data = sspi_clean_api_data.find({"IndicatorCode": IndicatorCode}, {"_id": 0, "Intermediates": 0})
    else:  
        indicator_data = sspi_main_data_v3.find({"IndicatorCode": IndicatorCode})
    return parse_json(indicator_data)

@api_bp.route("/query/country/<CountryCode>")
def query_country(CountryCode):
    """
    Take a country code and return the data
    """
    country_data = sspi_main_data_v3.find({"CountryCode": CountryCode})
    return parse_json(country_data)

@api_bp.route("/download")
def download():
    """
    Download the data from the database
    """
    MongoQuery = {}
    # implement filter parameters
    if request.args.getlist('IndicatorCode'):
        MongoQuery["IndicatorCode"] = {"$in": request.args.getlist('IndicatorCode')}
    if request.args.getlist('CountryCode'):
        MongoQuery["CountryCode"] = {"$in": request.args.getlist('CountryCode')}
    if request.args.getlist('YEAR'):
        MongoQuery["timePeriod"] = {"$in": request.args.getlist('timePeriod')}
    dataframe = lookup_database(request.args.get('database'))
    format = request.args.get('format', default = 'json', type = str)
    data_to_download = parse_json(dataframe.find(MongoQuery))
    if format == 'csv':
        df = pd.DataFrame(data_to_download).to_csv()
        mem = BytesIO()
        mem.write(df.encode('utf-8'))
        mem.seek(0)
        return send_file(mem,
                         mimetype='text/csv',
                         download_name='data.csv',
                         as_attachment=True)
    elif format=='json':
        return data_to_download
    else:
        return "Invalid format"

@api_bp.route('/api_coverage')
def api_coverage():
    """
    Return a list of all endpoints and whether they are implemented
    """
    all_indicators = indicator_codes()
    endpoints = [str(r) for r in app.url_map.iter_rules()]
    collect_implemented = [re.search(r'(?<=api/v1/collect/)(?!static)([\w]*)', r).group() for r in endpoints if re.search(r'(?<=api/v1/collect/)(?!static)[\w]*', r)]
    compute_implemented = [re.search(r'(?<=api/v1/compute/)(?!static)[\w]*', r).group() for r in endpoints if re.search(r'(?<=api/v1/compute/)(?!static)[\w]*', r)]
    coverage_data_object = []
    for indicator in all_indicators:
        coverage_data_object.append({"IndicatorCode": indicator, "collect_implemented": indicator in collect_implemented, "compute_implemented": indicator in compute_implemented})
    #{"collect_implemented": collect_implemented, "compute_implemented": compute_implemented}
    return parse_json(coverage_data_object)

@api_bp.route('/dynamic/<IndicatorCode>')
def get_dynamic_data(IndicatorCode):
    """
    Use the format argument to control whether the document is formatted for the website table
    """
    request_country_group = request.args.get("country_group", default = "sspi_67", type = str)
    country_codes = country_group(request_country_group)
    query_results = parse_json(sspi_clean_api_data.find({"IndicatorCode": IndicatorCode, "CountryCode": {"$in": country_codes}},
                                                        {"_id": 0, "Intermediates": 0, "IndicatorCode": 0}))
    print(query_results)
    long_data = pd.DataFrame(query_results).drop_duplicates()
    long_data = long_data.astype({"YEAR": int, "RAW": float})
    long_data = long_data.round(3)
    wide_dataframe = pd.pivot(long_data, index="CountryCode", columns="YEAR", values="RAW")
    nested_data = json.loads(wide_dataframe.to_json(orient="index"))
    return_data = []
    for country_code in nested_data.keys():
        country_data = nested_data[country_code]
        country_data["CountryCode"] = country_code
        country_data["CountryName"] = countries.lookup(country_code).name
        return_data.append(country_data)
    return parse_json(return_data)

def store_raw_observation(observation, collection_time, RawDataDestination):
    """
    Store the response from an API call in the database
    - Observation to be passed as a well-formed dictionary for entry into pymongo
    - RawDataDestination is the indicator code for the indicator that the observation is for
    """
    sspi_raw_api_data.insert_one(
    {"collection-info": {"CollectedBy": current_user.username,
                        "RawDataDestination": RawDataDestination,
                        "CollectedAt": collection_time}, 
    "observation": observation})

@api_bp.route("/post_static_data", methods=["POST"])
@fresh_login_required
def post_static_data():
    data = json.loads(request.data)
    sspi_main_data_v3.insert_many(data)
    return redirect(url_for('datatest_bp.database'))

class RemoveDuplicatesForm(FlaskForm):
    database = SelectField(choices = ["sspi_main_data_v3", "sspi_raw_api_data", "sspi_clean_api_data"], validators=[DataRequired()], default="sspi_raw_api_data", label="Database")
    indicator_code = SelectField(choices = ["BIODIV", "COALPW"], validators=[DataRequired()], default="None", label="Indicator Code")
    submit = SubmitField('Remove Duplicates')

@api_bp.route("/remove_duplicates", methods=["POST"])
def remove_duplicates():
    database = request.form.get("database")
    IndicatorCode = request.form.get("indicator_code")
    print(database, IndicatorCode)
    return redirect(url_for("api_bp.delete"))

class DeleteIndicatorForm(FlaskForm):
    database = SelectField(choices = ["sspi_main_data_v3", "sspi_raw_api_data", "sspi_clean_api_data"], validators=[DataRequired()], default="sspi_main_data_v3", label="Database")
    indicator_code = SelectField(choices = ["BIODIV", "REDLST", "COALPW"], validators=[DataRequired()], default="None", label="Indicator Code")
    submit = SubmitField('Delete')

class ClearDatabaseForm(FlaskForm):
    database = StringField(validators=[DataRequired()], label="Database Name")
    database_confirm = StringField(validators=[DataRequired()], label="Confirm Database Name")
    submit = SubmitField('Clear Database')

@api_bp.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    remove_duplicates_form = RemoveDuplicatesForm(request.form)
    delete_indicator_form = DeleteIndicatorForm(request.form)
    clear_database_form = ClearDatabaseForm(request.form)
    if request.method == "POST" and delete_indicator_form.validate_on_submit():
        IndicatorCode = delete_indicator_form.indicator_code.data
        if delete_indicator_form.database.data == "sspi_main_data_v3":
            count = sspi_main_data_v3.delete_many({"IndicatorCode": IndicatorCode}).deleted_count
        elif delete_indicator_form.database.data == "sspi_raw_api_data":
            count = sspi_raw_api_data.delete_many({"collection-info.RawDataDestination": IndicatorCode}).deleted_count
        elif delete_indicator_form.database.data == "sspi_clean_api_data":
            count = sspi_clean_api_data.delete_many({"IndicatorCode": IndicatorCode}).deleted_count
        flash("Deleted " + str(count) + " documents")

    if request.method == "POST" and clear_database_form.validate_on_submit():
        if clear_database_form.database.data == clear_database_form.database_confirm.data:
            lookup_database(clear_database_form.database.data).delete_many({})
            flash("Cleared database " + clear_database_form.database.data)
        else:
            flash("Database names do not match")
    return render_template('api-delete-page.html', remove_duplicates_form=remove_duplicates_form, delete_indicator_form=delete_indicator_form, messages=get_flashed_messages(), clear_database_form=clear_database_form)

@api_bp.route("/metadata", methods=["GET"])
def metadata():
    # Implement request.args for filtering the metadata
    return parse_json(sspi_metadata.find())

@api_bp.route("/metadata", methods=["POST"])
def post_metadata():
    data = json.loads(request.data)
    sspi_metadata.insert_many(data)
    return redirect(url_for('datatest_bp.database'))

@api_bp.route("/metadata/indicator_codes", methods=["GET"])
def indicator_codes():
    """
    Return a list of all indicator codes in the database
    """
    query_result = parse_json(sspi_metadata.find_one({"indicator_codes": {"$exists": True}}))["indicator_codes"]
    return query_result

@api_bp.route("/metadata/country_groups", methods=["GET"])
def country_groups():
    """
    Return a list of all country groups in the database
    """
    query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"]
    return parse_json(query_result.keys())

@api_bp.route("/metadata/country_groups/<country_group>", methods=["GET"])
def country_group(country_group):
    """
    Return a list of all countries in a given country group
    """
    query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"][country_group]
    return query_result

# utility functions
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
    
def fetch_raw_data(RawDataDestination):
    """
    Utility function that handles querying the database
    """
    mongoQuery = {"collection-info.RawDataDestination": RawDataDestination}
    raw_data = parse_json(sspi_raw_api_data.find(mongoQuery))
    return raw_data

def lookup_database(database_name):
    if database_name == "sspi_main_data_v3":
        return sspi_main_data_v3
    elif database_name == "sspi_raw_api_data":
        return sspi_raw_api_data
    elif database_name == "sspi_clean_api_data":
        return sspi_clean_api_data
    elif database_name == "sspi_metadata":
        return sspi_metadata

@api_bp.route("/local")
@login_required
def local():
    return render_template('local.html', database_names=check_for_local_data())

@api_bp.route("/local/database/list", methods=['GET'])
@login_required
def check_for_local_data():
    try:
        database_files = os.listdir(os.path.join(os.getcwd(),'local'))
    except FileNotFoundError:
        database_files = os.listdir("/var/www/sspi.world/local")
    database_names = [db_file.split(".")[0] for db_file in database_files]
    return parse_json(database_names)

@api_bp.route("/local/reload/<database_name>", methods=["POST"])
@login_required
def reload_from_local(database_name):
    if not database_name in check_for_local_data():
        return "Unable to Reload Data: Invalid database name"
    database = lookup_database(database_name)
    del_count = database.delete_many({}).deleted_count
    try: 
        filepath = os.path.join(os.getcwd(),'local', database_name + ".json")
        json_file = open(filepath)
    except FileNotFoundError:
        filepath = os.path.join("/var/www/sspi.world/local", database_name + ".json")
        json_file = open(filepath)
    local_data = json.load(json_file)
    ins_count = len(database.insert_many(local_data).inserted_ids)
    json_file.close()
    return "Reload successful: Dropped {0} observations from {1} and reloaded with {2} observations".format(del_count, database_name, ins_count)

def string_to_float(string):
    """
    Passes back string 'NaN' instead of float NaN
    """
    if math.isnan(float(string)):
        return "NaN"
    return float(string)

@api_bp.route("/dashboard")
def api_internal_buttons():
    implementation_data = api_coverage()
    return render_template("api-internal-buttons.html", implementation_data=implementation_data)
