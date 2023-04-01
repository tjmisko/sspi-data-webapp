from datetime import datetime
import json
from flask import Blueprint, redirect, request, url_for
from flask_login import current_user, login_required
from ..models.usermodel import User
import requests
from .. import sspi_main_data, sspidb
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
def database():
    if request.method == 'POST':
        print("type of request.data", type(request.data))
        print("type of parsed request.data", type(parse_json(request.data)))
        sspi_main_data.insert_many(parse_json(request.data))
        return redirect(url_for('database'))
    else:
        sspi_data = sspi_main_data.find()
        for doc in sspi_data:
            print(doc)
    return "database page"


@datatest_bp.route('/collect-iea-data')
@login_required
def collect_coal_power():
    response = requests.get("https://api.iea.org/stats/indicator/TESbySource?").json()
    for r in response:
       sspi_main_data.insert_one({"observation": r,
                                  "collection-info": {"collector": current_user.username,
                                                      "datetime": datetime.now()}})
    return str(len(response))

@datatest_bp.route('/check-db')
@login_required
def check_db():
    x = sspi_main_data.find()
    return parse_json(x)

@datatest_bp.route('/delete-db')
@login_required
def delete_db():
    sspi_main_data.delete_many({})
    return "Deleted all observations"

@datatest_bp.route('/database-metadata')
def get_metadata():
    return sspidb.list_collection_names()

@datatest_bp.route('/check-user-db')
@login_required
def get_all_users():
    users = User.query.all()
    return str(users)
