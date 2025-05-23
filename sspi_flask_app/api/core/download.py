from io import BytesIO
from flask import Blueprint, request, send_file
import pandas as pd
from ..resources.utilities import lookup_database, parse_json
from sspi_flask_app.models.database import sspidb, sspi_metadata
import json


download_bp = Blueprint(
    "download_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/download"
)

db_choices = sspidb.list_collection_names()
ic_choices = sspi_metadata.indicator_codes()
cg_choices = sspi_metadata.country_groups()


def fetch_data_for_download(request_args):
    """
    request_args has type ImmutableMultiDict
    """
    mongo_query = {}
    if request_args.getlist('IndicatorCode'):
        mongo_query["IndicatorCode"] = {
            "$in": request.args.getlist('IndicatorCode')}
    if request_args.get('CountryGroup'):
        mongo_query['CountryCode'] = {
            "$in": sspi_metadata.country_group(request.args.get('CountryGroup'))
        }
    elif request_args.getlist('CountryCode'):
        mongo_query["CountryCode"] = {
            "$in": request.args.getlist('CountryCode')
        }
    if request_args.getlist('YEAR'):
        mongo_query["timePeriod"] = {
            "$in": request.args.getlist('timePeriod')
        }
    database_name = request_args.get("database", default="sspi_main_data_v3")
    database = lookup_database(database_name)
    data_to_download = parse_json(database.find(mongo_query))
    return data_to_download


@download_bp.route("/csv")
def download_csv():
    """
    Download the data from the database in csv format
    """
    data_to_download = fetch_data_for_download(request.args)
    df = pd.DataFrame(data_to_download).to_csv()
    mem = BytesIO()
    mem.write(df.encode('utf-8'))
    mem.seek(0)
    return send_file(
        mem,
        mimetype='text/csv',
        download_name='SSPIData.csv',
        as_attachment=True
    )


@download_bp.route("/json")
def download_json():
    """
    Download data from the database in json format
    """
    data_to_download = fetch_data_for_download(request.args)
    mem = BytesIO()
    mem.write(json.dumps(data_to_download).encode('utf-8'))
    mem.seek(0)
    return send_file(
        mem,
        mimetype='application/json',
        download_name='SSPIData.json',
        as_attachment=True
    )
