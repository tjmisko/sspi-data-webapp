from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)

import pandas as pd
import json
from io import StringIO

from sspi_flask_app.api.datasource.oecdstat import (
    # organizeOECDdata,
    # OECD_country_list,
    extractAllSeries,
    # filterSeriesList,
    filterSeriesListSeniors
)


@compute_bp.route("/SENIOR", methods=['GET'])
@login_required
def compute_senior():
    app.logger.info("Running /api/v1/compute/SENIOR")
    sspi_clean_api_data.delete_many({"IndicatorCode": "SENIOR"})
    raw_data = sspi_raw_api_data.fetch_raw_data("SENIOR")
    # metadata = raw_data[0]["Metadata"]
    # metadata_soup = bs.BeautifulSoup(metadata, "lxml")
    # to see the codes and their descriptions, uncomment and
    # return the following two lines
    # jsonify([[tag.get("value"), tag.get_text()]
    #          for tag in metadata_soup.find_all("code")])
    metadata_codes = {
        "PEN20A": "Expected years in retirement, men",
        "PEN20B": "Expected years in retirement, women",
        "PEN24A": "Old age income poverty, 66+",
    }
    metadata_code_map = {
        "PEN20A": "YRSRTM",
        "PEN20B": "YRSRTW",
        "PEN24A": "POVNRT",
    }
    series = extractAllSeries(raw_data[0]["Raw"])
    document_list = []
    for code in metadata_codes.keys():
        document_list.extend(filterSeriesListSeniors(
            series, code, "PAG", "SENIOR"))
    long_senior_data = pd.DataFrame(document_list)
    long_senior_data.drop(long_senior_data[long_senior_data["CountryCode"].map(
        lambda s: len(s) != 3)].index, inplace=True)
    long_senior_data["IntermediateCode"] = long_senior_data["VariableCodeOECD"].map(
        lambda x: metadata_code_map[x])
    long_senior_data.astype({"Year": "int", "Value": "float"})
    zipped_document_list = zip_intermediates(
        json.loads(str(long_senior_data.to_json(orient="records")),
                   parse_int=int, parse_float=float),
        "SENIOR",
        ScoreFunction=lambda YRSRTM, YRSRTW, POVNRT: 0.25 *
        YRSRTM + 0.25*YRSRTW + 0.50*POVNRT,
        ScoreBy="Score"
    )
    clean_document_list, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)


@compute_bp.route("/FATINJ", methods=['GET'])
@login_required
def compute_fatinj():
    app.logger.info("Running /api/v1/compute/FATINJ")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FATINJ"})
    raw_data = sspi_raw_api_data.fetch_raw_data("FATINJ")
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    fatinj_raw = pd.read_csv(csv_virtual_file)
    fatinj_raw = fatinj_raw[fatinj_raw["SEX"] == "SEX_T"]
    fatinj_raw = fatinj_raw[['REF_AREA',
                             'TIME_PERIOD',
                             'UNIT_MEASURE',
                             'OBS_VALUE']]
    fatinj_raw = fatinj_raw.rename(columns={'REF_AREA': 'CountryCode',
                                            'TIME_PERIOD': 'Year',
                                            'OBS_VALUE': 'Value',
                                            'UNIT_MEASURE': 'Unit'})
    fatinj_raw['IndicatorCode'] = 'FATINJ'
    fatinj_raw['Unit'] = 'Rate per 100,000'
    fatinj_raw.dropna(subset=['Value'], inplace=True)
    obs_list = json.loads(str(fatinj_raw.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "FATINJ")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


