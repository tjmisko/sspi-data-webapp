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

api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api/v1'
)

@api_bp.route("/collect")
@login_required
def collect():
    print("hello")
    indicator = request.args.get('indicator')
    if not indicator:
        return "Please provide a valid argument to the 'indicator' query field"
    collector = collector_lookup(indicator)
    if not collector_lookup(indicator):
        return "Indicator was not found in SSPI database"
    return collector()

@api_bp.route("/compute")
@login_required
def compute():
    indicator = request.args.get('indicator')
    return indicator

# returns the collector function specified in the appropriate file path
def collector_lookup(indicator):
    print(indicator)
    if indicator == 'redlst':
        from .sspi.sustainability.ecosystem.redlist import collect as collector
        return collector
    return None