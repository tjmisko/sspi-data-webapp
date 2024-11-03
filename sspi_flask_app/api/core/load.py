from flask import Blueprint, Response,  request
from flask_login import login_required, current_user
import pandas as pd
import numpy as np
from pycountry import countries
from sspi_flask_app.models.database import sspi_country_characteristics
import json

from sspi_flask_app.models.database import (
    sspi_bulk_data,
    sspi_metadata,
    sspi_main_data_v3
)

load_bp = Blueprint("load_bp", __name__,
                    template_folder="templates",
                    static_folder="static",
                    url_prefix="/load")


###############################################
# Routes in this blueprint load extra data that
# is not formally part of the SSPI but which is
# sometimes useful. e.g. GDP and population data
###############################################
@load_bp.route("/UNPOPL", methods=['GET'])
@login_required
def unpopl():
    def collect_iterator(**kwargs):
        # insert UN population data into sspi_country_characteristics database
        yield from insert_pop_data()
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


def insert_pop_data():
    pop_data = pd.read_csv(
        "local/UN_population_data.csv").astype(str).drop(columns="Unnamed: 0")
    pop_data["CountryCode"] = pop_data["country"].map(lambda cou: countries.get(name=cou).alpha_3
                                                      if countries.get(name=cou) is not None else np.nan)
    pop_data = pop_data.dropna()
    pop_data["year"] = (pop_data["year"]).astype(int)
    pop_data["pop"] = (pop_data["pop"]).astype(int)
    obs_list = []
    intermediate_code = "UNPOPL"
    country_list = pop_data["CountryCode"].unique().tolist()
    count = 0
    for country in country_list:
        yield f"Processing {country}\n"
        country_df = pop_data[pop_data["CountryCode"] == country]
        country_years = country_df["year"].tolist()
        for year in country_years:
            value = country_df[country_df["year"] == year]["pop"].values[0]
            obs = {"CountryCode": country,
                   "Value": int(value),
                   "Year": year,
                   "Unit": "population",
                   "IntermediateCode": intermediate_code
                   }
            count += 1
            obs_list.append(obs)
    sspi_country_characteristics.insert_many(obs_list)
    yield f"Done! {count} UN population observations inserted into sspi_country_characteristics"


@load_bp.route("/load/<IndicatorCode>", methods=["POST"])
@login_required
def load(IndicatorCode):
    """
    Utility function that handles loading data from the API into the database
    """
    observations_list = json.loads(request.get_json())
    count = sspi_bulk_data.insert_many(observations_list)
    return f"Inserted {count} observations into database for Indicator {IndicatorCode}."


@load_bp.route("/load/sspi_main_data_v3", methods=['GET'])
@login_required
def load_maindata():
    count = sspi_main_data_v3.load()
    return f"Inserted {count} main data documents into database."


@load_bp.route("/load/sspi_metadata", methods=['GET'])
@login_required
def load_metadata():
    count = sspi_metadata.load()
    return f"Inserted {count} metadata documents into database."
