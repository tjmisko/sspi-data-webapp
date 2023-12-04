import os
import re
import json
import pandas as pd
from flask import Blueprint, request, current_app as app, jsonify
from flask_login import login_required

from ... import sspi_bulk_data

load_bp = Blueprint("load_bp", __name__,
                    template_folder="templates", 
                    static_folder="static")
                   

@load_bp.route("/load/<IndicatorCode>", methods=["POST"])
@login_required
def load(IndicatorCode):
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
    print(indicator_details.head())
    print(intermediate_details.head())
    metadata = build_metadata(indicator_details, intermediate_details)
    print(metadata)
    return local_path

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

def build_metadata(indicator_details, intermediate_details):
    metadata = []
    ### Build metadata for PillarCodes
    pillar_codes = indicator_details["PillarCode"].unique()
    metadata.append({"DocumentType": "PillarCodes", "PillarCodes": pillar_codes})
    ### Build metadata for CategoryCodes
    category_codes = indicator_details["CategoryCode"].unique()
    metadata.append({"DocumentType": "CategoryCodes", "CategoryCodes": category_codes})
    ### Build metadata for IndicatorCodes
    indicator_codes = indicator_details["IndicatorCode"].unique()
    metadata.append({"DocumentType": "CategoryCodes", "IndicatorCode": indicator_cdoes})
    ### Build metadata for IntermediateCodes
    intermediate_codes = intermediate_details["IntermediateCode"].unique()
    metadata.append({"DocumentType": "IntermediateCodes", "IntermediateCodes": intermediate_codes})
    ## Build metadata for IntermediateDetails
    intermediate_details_list = json.loads(intermediate_details.to_json(orient="records"))
    for intermediate_detail in intermediate_details_list:
        intermediate_detail["DocumentType"] = "IntermediateDetail"
        metadata.append(intermediate_detail)
    ### Build metadata for IndicatorDetail
    indicator_details = json.loads(indicator_details.to_json(orient="records"))
    for indicator_detail in indicator_details:
        indicator_detail["DocumentType"] = "IndicatorDetail"
        # Link intermediate_details to their corresponding indicator_detail
        if indicator_detail["IntermediateCodes"] is not None:
            intermediate_codes = re.findall(r"[A-Z0-9]{6}", indicator_detail["IntermediateCodes"])
            indicator_detail["IntermediateCodes"] = intermediate_codes
            intermediate_details = intermediate_details.loc[intermediate_details["IndicatorCode"] == indicator_detail["IndicatorCode"]].to_json(orient="records")
            indicator_detail["IntermediateDetails"] = intermediate_details
        metadata.append(indicator_detail)
    return jsonify(metadata)
