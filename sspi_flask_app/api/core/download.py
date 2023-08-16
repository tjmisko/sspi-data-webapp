from io import BytesIO
from flask import Blueprint, request, send_file
import pandas as pd
from ..api import lookup_database, parse_json


download_bp = Blueprint("download_bp", __name__,
                        template_folder="templates", 
                        static_folder="static", 
                        url_prefix="/download")

@download_bp.route("/download")
def download():
    """
    Download the data from the database
    """
    MongoQuery = {}
    # implement filter parameters
    if request.args.getlist('IndicatorCode'):
        MongoQuery["IndicatorCode"] = {"$in": request.args.getlist('IndicatorCode')}
    if request.args.getlist('CountryCode'):
        MongoQuery["CountryCode"] = {"$in": request.args.getlist('CountryCode')}
    if request.args.getlist('YEAR'):
        MongoQuery["timePeriod"] = {"$in": request.args.getlist('timePeriod')}
    dataframe = lookup_database(request.args.get('database'))
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
    elif format=='json':
        return data_to_download
    else:
        return "Invalid format"