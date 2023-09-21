from io import BytesIO
from flask import Blueprint, request, send_file
import pandas as pd

from ..api import lookup_database, parse_json
from .query import country_group


download_bp = Blueprint("download_bp", __name__,
                        template_folder="templates", 
                        static_folder="static", 
                        url_prefix="/download")

def fetch_data_for_download(request_args):
    """
    request_args has type ImmutableMultiDict
    """
    MongoQuery = {}
    if request_args.getlist('IndicatorCode'):
          MongoQuery["IndicatorCode"] = {"$in": request.args.getlist('IndicatorCode')}
    if request_args.get('CountryGroup'):
        MongoQuery['CountryCode'] = {"$in": country_group(request.args.get('CountryGroup'))}
    elif request_args.getlist('CountryCode'):
        MongoQuery["CountryCode"] = {"$in": request.args.getlist('CountryCode')}
    if request_args.getlist('YEAR'):
        MongoQuery["timePeriod"] = {"$in": request.args.getlist('timePeriod')}'
    if request_args.get("database"):
        database_name=
    dataframe = lookup_database(database_name)
    format = request.args.get('format', default = 'json', type = str)
    data_to_download = parse_json(dataframe.find(MongoQuery))
    return data_to_download
  

@download_bp.route("/csv")
def download_csv():
    """
    Download the data from the database in csv format
    """
    MongoQuery = get_download_query_args(request.args)
    data_to_download = query_db(MongoQuery)
    df = pd.DataFrame(data_to_download).to_csv()
    mem = BytesIO()
    mem.write(df.encode('utf-8'))
    mem.seek(0)
    return send_file(mem,
                     mimetype='text/csv',
                     download_name='data.csv',
                     as_attachment=True)

@download_bp.route("/json")
def download_json():
    """
    Download data from the database in json format
    """
    MongoQuery = get_download_query_args(request.args)
    df = query_db(MongoQuery)
    return df.json()
