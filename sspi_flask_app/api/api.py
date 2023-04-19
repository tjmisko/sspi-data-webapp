from datetime import datetime
import json
from io import BytesIO
from flask import Blueprint, redirect, request, url_for, escape, send_file, current_app as app
from flask_login import current_user, login_required
from ..models.usermodel import User
from .. import sspi_main_data_v3, sspi_raw_api_data, sspi_clean_api_data
from bson import json_util
from pycountry import countries
import pandas as pd
import re



def parse_json(data):
    return json.loads(json_util.dumps(data))

def print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api/v1'
)

@api_bp.route("/country/lookup")
def countryLookup(countryData=''):
    """
    Take country data (a name or code) and return a string of a pycountry country object
    """
    if request.args:
        countryData = escape(request.args.get('countryData', default = '', type = str))
    try:
        print("countryData:", countryData)
        country = countries.search_fuzzy(countryData)[0]
        print("Fuzzy lookup guessed that", countryData, "is", country.name)
    except LookupError:
       return "country not found"
    return str(country)

# @api_bp.route("/save/<indicator:string>", methods=['POST'])
# def save_indicator(indicator, indicator_data={}):
#     """
#     take an indicator name and request argument options
#     - overwrite: bool, default False
#     - collect: bool, default False
#     """
#     overwrite = bool(request.args.get('overwrite', default = False, type = bool))
#     print("overwrite:", overwrite)
#     inMongo = bool(sspi_main_data_v3.find_one({"indicator": indicator}))
#     print("inMongo:", inMongo)
#     collect = bool(request.args.get('collect', default = False, type = bool))
#     print("collect:", collect)
#     if not inMongo:
#         sspi_main_data_v3.insert_many(indicator_data)
#     elif overwrite:
#         sspi_main_data_v3.delete_many({"indicator": indicator})
#         sspi_main_data_v3.insert_many(indicator_data)

# route querying indicator data from mongodb
@api_bp.route("/query/indicator/<IndicatorCode>")
def query_indicator(IndicatorCode):
    """
    Take an indicator code and return the data
    """
    raw = request.args.get('raw', default = False, type = bool)
    if raw:
        indicator_data = sspi_raw_api_data.find({"collection-info": {"RawDataDestination": IndicatorCode}})
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
    if not request.args.get('dataset'):
        dataframe = sspi_main_data_v3
    elif request.args.get('dataset') == 'dynamic':
        dataframe = sspi_clean_api_data
    format = request.args.get('format', default = 'json', type = str)
    data_to_download = parse_json(dataframe.find(MongoQuery))
    if format == 'csv':
        df = pd.DataFrame(data_to_download).to_csv()
        mem = BytesIO()
        mem.write(df.encode('utf-8'))
        mem.seek(0)
        return send_file(mem,
                         mimetype='text/csv',
                         downflload_name='data.csv',
                         as_attachment=True)
    elif format=='json':
        return data_to_download
    else:
        return "Invalid format"

@api_bp.route('/coverage')
def coverage():
    endpoints = [str(r) for r in app.url_map.iter_rules()]
    collect_implemented = [re.search(r'(?<=api/v1/collect/)(?!static)([\w]*)', r).group() for r in endpoints if re.search(r'(?<=api/v1/collect/)(?!static)[\w]*', r)]
    compute_implemented = [re.search(r'(?<=api/v1/compute/)(?!static)[\w]*', r).group() for r in endpoints if re.search(r'(?<=api/v1/compute/)(?!static)[\w]*', r)]
    coverage_data = {"collect_implemented": collect_implemented, "compute_implemented": compute_implemented}
    return parse_json(coverage_data)