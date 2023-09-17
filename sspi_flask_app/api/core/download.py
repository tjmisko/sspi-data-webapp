from io import BytesIO
from flask import Blueprint, request, send_file
import pandas as pd

from ..api import lookup_database, parse_json
from .query import country_group


download_bp = Blueprint("download_bp", __name__,
                        template_folder="templates", 
                        static_folder="static", 
                        url_prefix="/download")

@download_bp.route("/<database_name>/<format>")
def download(database_name, format):
    """
    Download the data from the database
    """
    MongoQuery = {}
    print(request.args)
    if request.args.getlist('IndicatorCode'):
        MongoQuery["IndicatorCode"] = {"$in": request.args.getlist('IndicatorCode')}
    if request.args.get('CountryGroup'):
        MongoQuery['CountryCode'] = {"$in": country_group(request.args.get('CountryGroup'))}
    elif request.args.getlist('CountryCode'):
        MongoQuery["CountryCode"] = {"$in": request.args.getlist('CountryCode')}
    if request.args.getlist('YEAR'):
        MongoQuery["timePeriod"] = {"$in": request.args.getlist('timePeriod')}
    dataframe = lookup_database(database_name)
    format = request.args.get('format', default = 'json', type = str)
    data_to_download = parse_json(dataframe.find(MongoQuery))
    if format == 'csv':
        df = pd.DataFrame(data_to_download).to_csv()
        mem = BytesIO()
        mem.write(df.encode('utf-8'))
        mem.seek(0)
        return send_file(mem,
                         mimetype='text/csv',
                         download_name='data.csv',
                         as_attachment=True)
    elif format == 'json':
        return data_to_download