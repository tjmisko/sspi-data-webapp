from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import io
import pandas as pd


def collect_wef_data(world_bank_indicator_code, **kwargs):
    """
    Downloads an Excel file from a predefined URL, converts it into CSV format,
    and inserts the CSV data into the database.
    Parameters:
      IndName (str): The 6-character indicator code to use in the database (e.g., "AQELEC").
      **kwargs: Additional keyword arguments (e.g., Username) to be passed to the insertion function.
    Expected Excel columns include:
      - "Country Name" (or similar; if missing, the code will attempt a lookup using countryiso3code)
      - "countryiso3code"
      - "Indicator Name"
      - "Indicator Code"
      - One column per year (e.g., "2007", "2008", etc.)
    """
    yield f"Collecting WEF-WorldBank data {world_bank_indicator_code}\n" 
    url = "https://thedocs.worldbank.org/en/doc/cf8eee7ff5029398f75e897b342e7320-0050122023/related/WEF-GCIHH.xlsx"
    yield f"Downloading Excel file from: {url}\n"
    response = requests.get(url)
    if response.status_code != 200:
        yield f"Failed to download Excel file. Status code: {response.status_code}\n"
        return
    excel_file = io.BytesIO(response.content)
    df = pd.read_excel(excel_file)
    yield f"Excel file opened successfully. Found {len(df)} rows.\n"
    csv_string = df.to_csv(index=False)
    source_info = {
        "OrganizationName": "World Economic Forum",
        "OrganizationCode": "WEF",
        "OrganizationSeriesCode": world_bank_indicator_code,
        "QueryCode": "WEF-GCIHH",
        "URL": url,
    }
    sspi_raw_api_data.raw_insert_one(
        {"csv": csv_string}, source_info, **kwargs
    )
