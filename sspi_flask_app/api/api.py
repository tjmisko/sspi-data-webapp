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
    This function takes a country data (a name or code) and returns pycountry country object
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