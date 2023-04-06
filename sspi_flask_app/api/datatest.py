from datetime import datetime
import json
from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_required
from ..models.usermodel import User
import requests
from .. import sspi_main_data_v3, sspidb, sspi_clean_api_data, sspi_raw_api_data
from json import JSONEncoder
from bson import json_util
from .source_utilities.worldbank import collectWorldBankdata

def parse_json(data):
    return json.loads(json_util.dumps(data))

def print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

datatest_bp = Blueprint(
    'datatest_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

@datatest_bp.route('/database', methods=['GET', 'POST'])
#login_required
def database():
    if request.method == 'POST':
        data = json.loads(request.data)
        print("type of request.data", type(data))
        print("request.data", data[1:10])
        sspi_main_data_v3.insert_many(data)
        return redirect(url_for('datatest_bp.database'))
    else:
        sspi_data = sspi_main_data_v3.find()
        for doc in sspi_data:
            print(doc)
    return "database page"

@datatest_bp.route('/collect/coalpower', methods=['GET', 'POST'])
@login_required
def collect_coal_power():
    collection_time = datetime.now()
    response = requests.get("https://api.iea.org/stats/indicator/TESbySource?").json()
    store_raw_api_data(response, collection_time, "COALPW")
    return redirect(url_for('datatest_bp.query_coalpower'))

def store_raw_api_data(response, collection_time, IndicatorCode):
    """
    Store the response from an API call in the database
    """
    try:
        for r in response:
            sspi_raw_api_data.insert_one(
                {"collection-info": {"CollectedBy": current_user.username,
                                    "RawDataDestination": IndicatorCode,
                                    "CollectedAt": collection_time}, 
                "observation": r}) 
        return response
    except Exception as e:
        print("Error storing API data:", e)
        return "Error storing API data"

@datatest_bp.route('/query/coalpower')
@login_required
def query_coalpower():
    mongoQuery = {}
    countryCodesQuery = {'$in': request.args.getlist('countryCode')}
    yearsQuery = {'$in': request.args.getlist('timePeriod')}
    if countryCodesQuery['$in']:
        mongoQuery['observation.country'] = countryCodesQuery
    if yearsQuery['$in']:
        mongoQuery['observation.year'] = yearsQuery
    print('mongoQuery: ', mongoQuery)
    queryData = sspi_raw_api_data.find(mongoQuery)
    return parse_json(queryData)

@datatest_bp.route('/compute/coalpower')
@login_required
def compute_coalpower():
    """
    Compute the percentage of energy from coal power sources by country and year
    - First, check if there is data in the database
    - Second, check which years are available
    - Third, loop through the years and compute the percentage for each country
    """
    if not sspi_raw_api_data.find_one({'collection-info.RawDataDestination': 'COALPW'}):
        return "No data for coalpower to compute"
    observation_format = {
        "IndicatorCode": "COALPW",
        "IndicatorNameShort": "Coal Power",
        "IndicatorNameLong": "Energy from Coal Sources",
        "ObservationType": "IndicatorObservation"     
    }
    years_available = sspi_raw_api_data.distinct('observation.year', {'collection-info.RawDataDestination': 'COALPW'})
    countries_available = sspi_raw_api_data.distinct('observation.country', {'collection-info.RawDataDestination': 'COALPW'})
    for year in years_available:
        for country in countries_available:
            print("Computing coalpower for {} in year {}\n".format(country, year))
            countryYearTotalAllSources = sspi_raw_api_data.aggregate([
                {'$match': {'observation.country': country, 'observation.year': year, 'collection-info.RawDataDestination': 'COALPW'}},
                {'$group': {'_id': '$country', 'total': {'$sum': '$observation.value'}}}
            ]).json()
            print("Total energy from all sources in {} in year {}: {}".format(country, year, countryYearTotalAllSources))
    return "Checkstring"

@datatest_bp.route('/check-db')
@login_required
def check_db():
    x = sspi_main_data_v3.find()
    return parse_json(x)

@datatest_bp.route('/delete/coalpower')
@login_required
def delete_db():
    sspi_raw_api_data.delete_many({})
    return "Deleted all observations"

@datatest_bp.route('/database-metadata')
def get_metadata():
    return sspidb.list_collection_names()

@datatest_bp.route('/check-user-db')
def get_all_users():
    users = User.query.all()
    return str(users)

@datatest_bp.route('/wb')
@login_required
def wb():
    return collectWorldBankdata("EP.PMP.SGAS.CD")



