from datetime import datetime
import json
from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_required
from ..models.usermodel import User
import requests
from .. import sspi_main_data_v3, sspidb, sspi_clean_api_data, sspi_raw_api_data
from json import JSONEncoder
from bson import json_util

def parse_json(data):
    return json.loads(json_util.dumps(data))

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

@datatest_bp.route('/collect-iea-data', methods=['GET', 'POST'])
@login_required
def collect_coal_power():
    response = requests.get("https://api.iea.org/stats/indicator/TESbySource?").json()
    for r in response:
       sspi_raw_api_data.insert_one({"observation": r,
                                  "collection-info": {"collector": current_user.username,
                                                      "datetime": datetime.now()}})
    return redirect(url_for('home_bp.data'))

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
    return None

@datatest_bp.route('/check-db')
@login_required
def check_db():
    x = sspi_main_data_v3.find()
    return parse_json(x)

@datatest_bp.route('/delete-db')
@login_required
def delete_db():
    sspi_main_data_v3.delete_many({})
    return "Deleted all observations"

@datatest_bp.route('/database-metadata')
def get_metadata():
    return sspidb.list_collection_names()

@datatest_bp.route('/check-user-db')
@login_required
def get_all_users():
    users = User.query.all()
    return str(users)



