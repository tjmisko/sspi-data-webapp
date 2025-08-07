from sspi_flask_app.api.datasource.wid import collect_wid_data, filter_wid_csv
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json
import pycountry
from io import StringIO
import pandas as pd

@dataset_collector("WID_FINCSH_PRETAX")
def collect_wid_fincs_pretax(**kwargs):
    yield from collect_wid_data(**kwargs)


@dataset_cleaner("WID_FINCSH_PRETAX")
def clean_wid_fincs_pretax():
    sspi_clean_api_data.delete_many({"DatasetCode": "WID_FINCSH_PRETAX"})
    source_info = sspi_metadata.get_source_info("WID_FINCSH_PRETAX")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    # Target WID variables for pre-tax factor income shares
    target_variables = ["sfaincj992", "sfaincj999"]  # equal-split adults (adults, all ages)
    target_percentiles = ["p0p100", "p0p50", "p50p90", "p90p100", "p99p100"]
    
    cleaned_data = []
    
    for raw_record in raw_data:
        raw_csv = raw_record["Raw"]
        filename = raw_record.get("filename", "")
        
        # Skip if no filename
        if not filename:
            continue
            
        # Extract country code from filename (e.g., WID_data_US.csv)
        filename_parts = filename.split("_")
        if len(filename_parts) != 3:
            continue
            
        country_alpha2 = filename_parts[2].split(".")[0]
        
        # Convert to ISO3
        try:
            country = pycountry.countries.get(alpha_2=country_alpha2)
            if not country:
                continue
            country_code = country.alpha_3
        except:
            continue
            
        # Parse CSV
        try:
            df = pd.read_csv(StringIO(raw_csv), delimiter=';')
        except:
            continue
            
        # Filter for our target variables and percentiles
        for variable in target_variables:
            var_data = df[df['variable'] == variable]
            if var_data.empty:
                continue
                
            # Filter for target percentiles and years > 1990
            var_data = var_data[
                (var_data['percentile'].isin(target_percentiles)) &
                (var_data['year'] > 1990)
            ]
            
            for _, row in var_data.iterrows():
                if pd.isna(row['value']):
                    continue
                    
                record = {
                    "DatasetCode": "WID_FINCSH_PRETAX",
                    "CountryCode": country_code,
                    "Year": int(row['year']),
                    "Value": float(row['value']),
                    "Percentile": row['percentile'],
                    "Unit": "Share"
                }
                cleaned_data.append(record)
    
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WID_FINCSH_PRETAX")
    return parse_json(cleaned_data)
