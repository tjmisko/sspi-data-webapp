import os
import re
import json
import pandas as pd
from flask import Blueprint, request, current_app as app, jsonify
from flask_login import login_required

from ... import sspi_bulk_data, sspi_metadata

load_bp = Blueprint("load_bp", __name__,
                    template_folder="templates", 
                    static_folder="static")
                   

@load_bp.route("/load/<IndicatorCode>", methods=["POST"])
@login_required
def load():
    """
    Utility function that handles loading data from the API into the database
    """
    observations_list = json.loads(request.get_json())
    count = sspi_bulk_data.insert_many(observations_list)
    return f"Inserted {count} observations into database."

@load_bp.route("/load/sspi_metadata", methods=['GET'])
@login_required
def load_metadata():
    local_path = os.path.join(os.path.dirname(app.instance_path), "local")
    indicator_details = pd.read_csv(os.path.join(local_path, "IndicatorDetails.csv"))
    intermediate_details = pd.read_csv(os.path.join(local_path, "IntermediateDetails.csv"))
    metadata = build_metadata(indicator_details, intermediate_details)
    count = sspi_metadata.insert_many(metadata)
    sspi_metadata.drop_duplicates()
    return f"Inserted {count} metadata documents into database."

@load_bp.route("/load/sspi_main_data_v3", methods=['POST'])
@login_required
def load_maindata():
    local_path = os.path.join(app.instance_path, "local")
    sspi_main_data_v3 = pd.read_csv(os.path.join(local_path, "SSPIMainDataV3.csv"))
    sspi_main_data_v3 = build_main_data(sspi_main_data_v3)
    return "success!"

def build_main_data(sspi_main_data_v3:pd.DataFrame):
    """
    Utility function that builds the main data JSON list from the SSPIMainDataV3.csv file
    """
    sspi_main_data_v3 = sspi_main_data_v3.drop(columns=["Unnamed: 0"])
    return sspi_main_data_v3.to_json(orient="records")

def build_metadata(indicator_details:pd.DataFrame, intermediate_details:pd.DataFrame) -> list:
    """
    Utility function that builds the metadata JSON list from the IndicatorDetails.csv and IntermediateDetails.csv files
    """
    metadata = []
    metadata.append(build_pillar_codes(indicator_details))
    metadata.append(build_category_codes(indicator_details))
    metadata.append(build_indicator_codes(indicator_details))
    metadata.append(build_intermediate_codes(intermediate_details))
    metadata.extend(build_intermediate_details(intermediate_details))
    metadata.extend(build_indicator_details(indicator_details, intermediate_details))
    assert type(metadata) == list
    return metadata

def build_pillar_codes(indicator_details:pd.DataFrame) -> dict:
    pillar_codes = indicator_details["PillarCode"].unique().tolist()
    return {"DocumentType": "PillarCodes", "Metadata": pillar_codes}

def build_category_codes(indicator_details:pd.DataFrame) -> dict:
    category_codes = indicator_details["CategoryCode"].unique().tolist()
    return {"DocumentType": "CategoryCodes", "Metadata": category_codes}

def build_indicator_codes(indicator_details:pd.DataFrame) -> dict:
    indicator_codes = indicator_details["IndicatorCode"].unique().tolist()
    return {"DocumentType": "CategoryCodes", "Metadata": indicator_codes}

def build_intermediate_codes(intermediate_details:pd.DataFrame) -> dict:
    intermediate_codes = intermediate_details["IntermediateCode"].unique().tolist()
    return {"DocumentType": "IntermediateCodes", "Metadata": intermediate_codes}

def build_intermediate_details(intermediate_details:pd.DataFrame) -> list[dict]:
    intermediate_details_list = json.loads(str(intermediate_details.to_json(orient="records")))
    return [{"DocumentType": "IntermediateDetail", "Metadata": intermediate_detail} for intermediate_detail in intermediate_details_list]

def build_indicator_details(indicator_details:pd.DataFrame, intermediate_details:pd.DataFrame):
    json_string = str(indicator_details.to_json(orient="records"))
    indicator_details_list = json.loads(json_string)
    for indicator_detail in indicator_details_list:
        indicator_detail["DocumentType"] = "IndicatorDetail"
        # Link intermediate_details to their corresponding indicator_detail
        if indicator_detail["IntermediateCodes"] is not None:
            intermediate_codes = re.findall(r"[A-Z0-9]{6}", indicator_detail["IntermediateCodes"])
            indicator_detail["IntermediateCodes"] = intermediate_codes
            filtered_intermediate_details = intermediate_details.loc[intermediate_details["IndicatorCode"] == indicator_detail["IndicatorCode"]]
            filtered_intermediate_details_list = json.loads(str(filtered_intermediate_details.to_json(orient="records")))
            indicator_detail["IntermediateDetails"] = filtered_intermediate_details_list
    return [{"DocumentType": "IndicatorDetail", "Metadata": indicator_detail} for indicator_detail in indicator_details_list]
