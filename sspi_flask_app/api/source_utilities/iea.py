import json
import requests
from ..api import parse_json


def collect_IEA_indicator_data(indicator_code):
    json_data = requests.get('https://api.iea.org/stats/indicator/' + indicator_code + '?').json()
    return (json_data)