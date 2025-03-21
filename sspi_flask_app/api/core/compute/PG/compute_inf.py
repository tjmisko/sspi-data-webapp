from flask import redirect, url_for, jsonify
import json
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)

from collections import OrderedDict
from flask import current_app

from sspi_flask_app.api.resources.utilities import (
    parse_json,
    jsonify_df,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)
import pandas as pd
from io import StringIO


from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_intrnt,
)


@compute_bp.route("/INTRNT", methods=['GET'])
@login_required
def compute_intrnt():
    if not sspi_raw_api_data.raw_data_available("INTRNT"):
        return redirect(url_for("collect_bp.INTRNT"))
    # worldbank #
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="AVINTR")
    wb_clean = clean_wb_data(wb_raw, "INTRNT", unit="Percent")
    # sdg #
    sdg_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="QLMBPS")
    sdg_clean = extract_sdg_pivot_data_to_nested_dictionary(sdg_raw)
    sdg_clean = flatten_nested_dictionary_intrnt(sdg_clean)
    combined_list = wb_clean + sdg_clean
    cleaned_list = zip_intermediates(combined_list, "INTRNT",
                                     ScoreFunction=lambda AVINTR, QUINTR: 0.5 * AVINTR + 0.5 * QUINTR,
                                     ScoreBy="Score")
    filtered_list, incomplete_observations = filter_incomplete_data(
        cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)


@compute_bp.route("/AQELEC", methods=["GET"])
@login_required




def compute_aqelec():
    if not sspi_raw_api_data.raw_data_available("AQELEC"):
        return redirect(url_for("collect_bp.AQELEC"))
    quality_data = sspi_raw_api_data.fetch_raw_data("AQELEC", IntermediateCode="QUELCT")[0]
    quality_df = pd.read_csv(StringIO(quality_data["Raw"]["csv"]))
    filtered_df = quality_df[
        (quality_df["Indicator ID"] == "WEF.GCIHH.EOSQ064") &
        (quality_df["Attribute 1"] == "Value")
        ]
    year_columns = [col for col in filtered_df.columns if col.isdigit()]
    id_vars = [col for col in filtered_df.columns if col not in year_columns]
    df_melted = filtered_df.melt(
        id_vars=id_vars,
        value_vars=year_columns,
        var_name="Year",
        value_name="Value"
    )
    df_melted["Year"] = df_melted["Year"].astype(int)
    df_sorted = df_melted.sort_values(by=["Economy ISO3", "Year"])
    df_sorted["IntermediateCode"] = "QUELCT"
    df_sorted["CountryCode"] = df_sorted["Economy ISO3"]
    df_sorted["Unit"] = df_sorted["Indicator"].apply(lambda x: x.split(",")[1].strip() if "," in x else "")
    df_final = df_sorted[["IntermediateCode", "CountryCode", "Year", "Value", "Unit"]]
    ordered_entries = []
    for record in df_final.to_dict(orient="records"):
        ordered_entries.append(OrderedDict([
            ("IntermediateCode", record["IntermediateCode"]),
            ("CountryCode", record["CountryCode"]),
            ("Year", record["Year"]),
            ("Value", record["Value"]),
            ("Unit", record["Unit"])
        ]))
    response_json = json.dumps(ordered_entries, sort_keys=False)
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "AQELEC", IntermediateCode="QUELCT")
    wb_clean = clean_wb_data(wb_raw, "AQELEC", unit="Percent")

    availability_data = sspi_raw_api_data.fetch_raw_data("AQELEC", IntermediateCode="AVELEC")

    combined_list = wb_clean + response_json
    cleaned_list = zip_intermediates(combined_list, "INTRNT",
                                     ScoreFunction=lambda AVELEC, QUELCT: 0.5 * AVELEC + 0.5 * QUELCT,
                                     ScoreBy="Score")
    filtered_list, incomplete_observations = filter_incomplete_data(
        cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)

