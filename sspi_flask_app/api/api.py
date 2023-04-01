from datetime import datetime
import json
from flask import Blueprint, redirect, request, url_for, escape
from flask_login import current_user, login_required
from ..models.usermodel import User
from .. import sspi_main_data, sspidb
from bson import json_util
from pycountry import countries


def parse_json(data):
    return json.loads(json_util.dumps(data))

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
#     inMongo = bool(sspi_main_data.find_one({"indicator": indicator}))
#     print("inMongo:", inMongo)
#     collect = bool(request.args.get('collect', default = False, type = bool))
#     print("collect:", collect)
#     if not inMongo:
#         sspi_main_data.insert_many(indicator_data)
#     elif overwrite:
#         sspi_main_data.delete_many({"indicator": indicator})
#         sspi_main_data.insert_many(indicator_data)

# route querying indicator data from mongodb
@api_bp.route("/query/<IndicatorCode>")
def query_indicator(IndicatorCode):
    """
    Take an indicator code and return the data
    """
    indicator_data = sspi_main_data.find({"IndicatorGroup": IndicatorCode})
    return parse_json(indicator_data)
      