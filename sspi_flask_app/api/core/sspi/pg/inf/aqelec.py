from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
)
from sspi_flask_app.api.datasource.worldbank import (
    collectWorldBankdata,
    clean_wb_data
)
from sspi_flask_app.api.datasource.wef import collectWEFQUELEC
from io import StringIO
import pandas as pd



@collect_bp.route("/AQELEC", methods=['GET'])
@login_required
def aqelec():
    def collect_iterator(**kwargs):
        yield from collectWorldBankdata("EG.ELC.ACCS.ZS", "AQELEC", IntermediateCode="AVELEC", **kwargs)
        yield from collectWEFQUELEC("WEF.GCIHH.EOSQ064", "AQELEC", IntermediateCode="QUELEC", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')



@compute_bp.route("/AQELEC")
@login_required
def compute_aqelec():
    app.logger.info("Running /api/v1/compute/AQELEC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "AQELEC"})
    quality_data = sspi_raw_api_data.fetch_raw_data("AQELEC", IntermediateCode="QUELEC")[0]
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
    df_sorted["IntermediateCode"] = "QUELEC"
    df_sorted["CountryCode"] = df_sorted["Economy ISO3"]
    df_sorted["Unit"] = df_sorted["Indicator"].apply(
        lambda x: x.split(",")[1].strip() if "," in x else ""
    )
    df_final = df_sorted[["IntermediateCode", "CountryCode", "Year", "Value", "Unit"]]
    df_final = df_final.to_dict(orient="records")
    wb_raw = sspi_raw_api_data.fetch_raw_data("AQELEC", IntermediateCode="AVELEC")
    wb_clean = clean_wb_data(wb_raw, "AQELEC", unit="Percent")
    for d in wb_clean:
        d.pop("Description", None)
        d.pop("IndicatorCode", None)
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "AQELEC", IntermediateCode="AVELEC"
    )
    wb_clean = clean_wb_data(wb_raw, "AQELEC", unit="Percent")
    for d in wb_clean:
        d.pop("Description", None)
        d.pop("IndicatorCode", None)
    combined_list = wb_clean + df_final
    clean_list, incomplete_list = zip_intermediates(
        combined_list, "AQELEC",
        ScoreFunction=lambda AVELEC, QUELEC: 0.5 * AVELEC + 0.5 * QUELEC,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)
