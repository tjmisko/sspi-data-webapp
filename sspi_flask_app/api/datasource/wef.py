from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import io
import pandas as pd
from pycountry import countries
# from ..resources.utilities import string_to_float


import requests
import io
import pandas as pd
from sspi_flask_app.models.database import sspi_raw_api_data

def collectWEFdata(IndicatorCode, IndName, **kwargs):
    """
    Downloads an Excel file from a predefined URL, converts it into CSV format, 
    and inserts the CSV data into the database.

    Parameters:
      IndicatorCode (str): The data source identifier (e.g., "WEF.GCIHH.EOSQ064").
      IndName (str): The 6-character indicator code to use in the database (e.g., "AQELEC").
      **kwargs: Additional keyword arguments (e.g., Username) to be passed to the insertion function.

    Expected Excel columns include:
      - "Country Name" (or similar; if missing, the code will attempt a lookup using countryiso3code)
      - "countryiso3code"
      - "Indicator Name"
      - "Indicator Code"
      - One column per year (e.g., "2007", "2008", etc.)
    """
    yield f"Collecting Excel data for data source {IndicatorCode} with indicator {IndName}\n"
    
    # Fixed URL for the Excel file
    url = "https://thedocs.worldbank.org/en/doc/cf8eee7ff5029398f75e897b342e7320-0050122023/related/WEF-GCIHH.xlsx"
    yield f"Downloading Excel file from: {url}\n"
    
    response = requests.get(url)
    if response.status_code != 200:
        yield f"Failed to download Excel file. Status code: {response.status_code}\n"
        return

    try:
        excel_file = io.BytesIO(response.content)
        df = pd.read_excel(excel_file)
    except Exception as e:
        yield f"Error reading Excel file: {e}\n"
        return

    yield f"Excel file downloaded successfully. Found {len(df)} rows.\n"
    
    # Convert the DataFrame to CSV format (without index)
    csv_string = df.to_csv(index=False)
    
    try:
        sspi_raw_api_data.insert_one({"csv": csv_string}, IndicatorCode, **kwargs)
        yield f"Inserted CSV data for {IndicatorCode} into database.\n"
    except Exception as e:
        yield f"Database insert failed for {IndicatorCode}: {str(e)}\n"
        return

    yield f"Collection complete for {IndicatorCode}."

   


    # cleaned_data = []

    # # Loop over each row and then over each year column to create one observation per year.
    # for row in raw_data:
    #     # Extract country metadata
    #     country_iso3 = row.get("countryiso3code", "").strip()  # remove extra spaces if any
    #     country_name = row.get("Country Name", "").strip()
    #     # If country name is missing and iso code is present, attempt lookup using pycountry.
    #     if not country_name and country_iso3:
    #         try:
    #             country_obj = countries.get(alpha_3=country_iso3)
    #             if country_obj:
    #                 country_name = country_obj.name
    #         except Exception:
    #             country_name = ""
    #     country_field = {"id": country_iso3, "value": country_name}

    #     # Extract indicator metadata from the row
    #     indicator_field = {
    #         "id": row.get("Indicator Code", "").strip(),
    #         "value": row.get("Indicator Name", "").strip()
    #     }

    #     # For every column whose header is a year, create a record
    #     for col, cell_value in row.items():
    #         if col.isdigit():
    #             # Skip if the value is NaN (or cannot be converted to a float)
    #             if pd.isna(cell_value):
    #                 continue
    #             try:
    #                 numeric_val = float(cell_value)
    #             except Exception:
    #                 continue
    #             record = {
    #                 "IntermediateCode": kwargs.get("IntermediateCode", ""),
    #                 "IndicatorCode": IndName,
    #                 "Raw": {
    #                     "country": country_field,
    #                     "countryiso3code": country_iso3,
    #                     "date": col,
    #                     "decimal": 1,
    #                     "indicator": indicator_field,
    #                     "obs_status": "",
    #                     "unit": "",
    #                     "value": numeric_val,
    #                 }
    #             }
    #             cleaned_data.append(record)

    # yield f"Transformed into {len(cleaned_data)} observation records.\n"

    # # Insert the cleaned data into the database using the 6-character indicator code
    # count = sspi_raw_api_data.raw_insert_many(cleaned_data, IndName, **kwargs)
    # yield f"Inserted {count} new observations into sspi_raw_api_data\n"
    # yield f"Collection complete for data source {IndicatorCode} with indicator {IndName}"
