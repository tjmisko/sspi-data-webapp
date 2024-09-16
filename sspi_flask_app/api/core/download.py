from io import BytesIO
from flask import Blueprint, request, send_file
import pandas as pd
from ..resources.utilities import lookup_database, parse_json
from flask_wtf import FlaskForm
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError
from ... import sspidb, sspi_metadata


download_bp = Blueprint("download_bp", __name__,
                        template_folder="templates", 
                        static_folder="static", 
                        url_prefix="/download")

db_choices = sspidb.list_collection_names()
ic_choices = sspi_metadata.indicator_codes()
cg_choices = sspi_metadata.country_groups()

class ClientDownloadForm(FlaskForm):
    database = SelectField(choices = [("sspi_main_data_v3", "SSPI V3 Data (2018 Only)"), ("sspi_final_api_data", "SSPI Dynamic Data (Experimental)")], validators=[DataRequired()], default="sspi_main_data_v3", label="Database")
    indicator_code = SelectField(choices = ic_choices, validators=[DataRequired()], label="Indicator Code", render_kw={"placeholder": "Indicator Code"})
    country_group = SelectField(choices = cg_choices, validators=[DataRequired()], default="sspi49", label="Country Group")
    submit = SubmitField('Download Data')

@download_bp.route("/client", methods=['POST'])
def client_download():
    return "data"

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
        MongoQuery["timePeriod"] = {"$in": request.args.getlist('timePeriod')}
    database_name = request_args.get("database", default = "sspi_main_data_v3")
    dataframe = lookup_database(database_name)
    data_to_download = parse_json(dataframe.find(MongoQuery))
    print(MongoQuery)
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
    return send_file(mem,
                     mimetype='text/csv',
                     download_name='data.csv',
                     as_attachment=True)

@download_bp.route("/json")
def download_json():
    """
    Download data from the database in json format
    """
    data_to_download = fetch_data_for_download(request.args)
    return data_to_download
