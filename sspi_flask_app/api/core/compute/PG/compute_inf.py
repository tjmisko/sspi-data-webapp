from flask import current_app as app
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
    score_single_indicator
)
import pandas as pd
from io import StringIO


from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg,
    filter_sdg
)
import pandas as pd
from io import StringIO


@compute_bp.route("/INTRNT", methods=['GET'])
@login_required
def compute_intrnt():
    app.logger.info("Running /api/v1/compute/INTRNT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "INTRNT"})
    # AVINTR (WorldBank)
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="AVINTR"
    )
    clean_avintr = clean_wb_data(wb_raw, "INTRNT", unit="Percent")
    # QUINTR (SDG)
    sdg_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="QUINTR"
    )
    extracted_quintr = extract_sdg(sdg_raw)
    idcode_map = {"IT_NET_BBND": "QUINTR"}
    filtered_quintr = filter_sdg(
        extracted_quintr, idcode_map,
        type_of_speed="10MBPS"
    )
    for obs in filtered_quintr:
        obs["IntermediateCode"] = "QUINTR"
    clean_list, incomplete_list = zip_intermediates(
        clean_avintr + filtered_quintr, "INTRNT",
        ScoreFunction=lambda AVINTR, QUINTR: (AVINTR + QUINTR) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    print(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/DRKWAT")
@login_required
def compute_drkwat():
    app.logger.info("Running /api/v1/compute/DRKWAT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "DRKWAT"})
    raw_data = sspi_raw_api_data.fetch_raw_data("DRKWAT")
    cleaned = clean_wb_data(raw_data, "DRKWAT", "Percent")
    scored_list = score_single_indicator(cleaned, "DRKWAT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/SANSRV")
@login_required
def compute_sansrv():
    app.logger.info("Running /api/v1/compute/SANSRV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "SANSRV"})
    raw_data = sspi_raw_api_data.fetch_raw_data("SANSRV")
    cleaned = clean_wb_data(raw_data, "SANSRV", "Percent")
    scored_list = score_single_indicator(cleaned, "SANSRV")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/AQELEC")
@login_required
def compute_aqelec():
    app.logger.info("Running /api/v1/compute/AQELEC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "AQELEC"})
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
    df_final = df_final.to_dict(orient="records")
    wb_raw = sspi_raw_api_data.fetch_raw_data("AQELEC", IntermediateCode="AVELEC")
    wb_clean = clean_wb_data(wb_raw, "AQELEC", unit="Percent")
    for d in wb_clean:
        d.pop("Description", None)
        d.pop("IndicatorCode", None)
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "AQELEC", IntermediateCode="AVELEC")
    wb_clean = clean_wb_data(wb_raw, "AQELEC", unit="Percent")
    for d in wb_clean:
        d.pop("Description", None)
        d.pop("IndicatorCode", None)
    combined_list = wb_clean + df_final
    for intermediate in combined_list:
        print(type(intermediate))
    cleaned_list = zip_intermediates(combined_list, "AQELEC",
                                     ScoreFunction=lambda AVELEC, QUELCT: 0.5 * AVELEC + 0.5 * QUELCT,
                                     ScoreBy="Values")
    filtered_list, incomplete_observations = filter_incomplete_data(
         cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)
