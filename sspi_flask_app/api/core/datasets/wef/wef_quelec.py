###########################################################
# Documentation: datasets/wef/wef_quelec/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.wef import collect_wef_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from io import StringIO
import pandas as pd


@dataset_collector("WEF_QUELEC")
def collect_wef_quelec(**kwargs):
    yield from collect_wef_data("WEF.GCIHH.EOSQ064", **kwargs)


@dataset_cleaner("WEF_QUELEC")
def clean_wef_quelec():
    sspi_clean_api_data.delete_many({"DatasetCode": "WEF_QUELEC"})
    source_info = sspi_metadata.get_source_info("WEF_QUELEC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    quality_data = raw_data[0]
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
    df_sorted["DatasetCode"] = "WEF_QUELEC"
    df_sorted["CountryCode"] = df_sorted["Economy ISO3"]
    df_sorted["Unit"] = df_sorted["Indicator"].apply(
        lambda x: x.split(",")[1].strip() if "," in x else ""
    )
    df_final = df_sorted[["DatasetCode", "CountryCode", "Year", "Value", "Unit"]]
    # drop if Value is NaN
    dropna_df = df_final.dropna(subset=["Value"])
    cleaned_data = dropna_df.to_dict(orient="records")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WEF_QUELEC")
    return parse_json(cleaned_data)
