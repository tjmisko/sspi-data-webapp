import requests
import io
import pandas as pd
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json



@dataset_collector("UNODC_PRIPOP")
def collect_unodc_pripop(**kwargs):
    yield "Requesting UNODC Prison Population data...\n"
    url = "https://dataunodc.un.org/sites/dataunodc.un.org/files/data_cts_prisons_and_prisoners.xlsx"
    res = requests.get(url) 
    if res.status_code != 200:
        yield f"Error! Request returned status code {res.status_code}\n"
        return
    excel_file = io.BytesIO(res.content)
    df = pd.read_excel(excel_file)
    yield f"Excel file opened successfully. Found {len(df)} rows.\n"
    csv_string = df.to_csv(index=False)
    source_info = {
        "OrganizationName": "United Nations Office on Drugs and Crime",
        "OrganizationCode": "UNODC",
        "QueryCode": "data_cts_prisons_and_prisoners",
        "URL": url,
    }
    sspi_raw_api_data.raw_insert_one(
        csv_string, source_info, **kwargs
    )
    yield "Inserted UNODC Prison Population raw data\n"


@dataset_cleaner("UNODC_PRIPOP")
def clean_unodc_pripop():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNODC_PRIPOP"})
    source_info = sspi_metadata.get_source_info("UNODC_PRIPOP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    unodc_df = pd.read_csv(io.StringIO(raw_data[0]["Raw"]), skiprows=2)
    
    # Apply filters for the specified field values
    filtered_df = unodc_df[
        (unodc_df["Age"] == "Total") &
        (unodc_df["Category"] == "Total") &
        (unodc_df["Dimension"] == "Total") &
        (unodc_df["Indicator"] == "Persons held") &
        (unodc_df["Sex"] == "Total") &
        (unodc_df["Unit of measurement"] == "Rate per 100,000 population")
    ].copy()
    
    # Handle special case for GBR - aggregate UK regions
    gbr_regions = unodc_df[
        (unodc_df["Age"] == "Total") &
        (unodc_df["Category"] == "Total") &
        (unodc_df["Dimension"] == "Total") &
        (unodc_df["Indicator"] == "Persons held") &
        (unodc_df["Sex"] == "Total") &
        (unodc_df["Unit of measurement"] == "Rate per 100,000 population") &
        (unodc_df["Iso3_code"].isin(["GBR_NI", "GBR_E_W", "GBR_S"]))
    ].copy()
    
    if len(gbr_regions) > 0:
        # For population-weighted average of rates, we'll use simple average for now
        # since we don't have population data for each region
        gbr_aggregated = gbr_regions.groupby("Year").agg({
            "VALUE": "mean"  # Simple average of the three rates
        }).reset_index()
        
        # Create GBR entries
        gbr_aggregated["Iso3_code"] = "GBR"
        gbr_aggregated["Country"] = "United Kingdom"
        gbr_aggregated["Region"] = "Europe"
        gbr_aggregated["Subregion"] = "Northern Europe"
        gbr_aggregated["Indicator"] = "Persons held"
        gbr_aggregated["Dimension"] = "Total"
        gbr_aggregated["Category"] = "Total"
        gbr_aggregated["Sex"] = "Total"
        gbr_aggregated["Age"] = "Total"
        gbr_aggregated["Unit of measurement"] = "Rate per 100,000 population"
        gbr_aggregated["Source"] = "CTS"
        
        # Add to main filtered data
        filtered_df = pd.concat([filtered_df, gbr_aggregated], ignore_index=True)
    
    # Rename columns to match SSPI format
    filtered_df["DatasetCode"] = "UNODC_PRIPOP"
    filtered_df["CountryCode"] = filtered_df["Iso3_code"]
    filtered_df["Value"] = filtered_df["VALUE"]
    filtered_df["Unit"] = filtered_df["Unit of measurement"]
    
    # Select only required columns
    clean_df = filtered_df[["DatasetCode", "CountryCode", "Year", "Value", "Unit"]]
    
    # Remove rows with missing or invalid CountryCode
    clean_df = clean_df.dropna(subset=["CountryCode", "Year", "Value"])
    clean_df = clean_df[clean_df["CountryCode"].str.len() == 3]
    
    # Convert to records and clean up
    unodc_pripop = parse_json(clean_df.to_dict(orient="records"))
    
    # Insert cleaned data
    count = sspi_clean_api_data.insert_many(unodc_pripop)
    sspi_metadata.record_dataset_range(unodc_pripop, "UNODC_PRIPOP")
    return unodc_pripop


