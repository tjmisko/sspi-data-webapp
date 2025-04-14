import requests
import io
import zipfile
import pycountry
from sspi_flask_app.models.database import sspi_bulk_data


def bulkCollectWIDData(**kwargs):
    yield "Requesting WID data from source\n"
    res = requests.get("https://wid.world/bulk_download/wid_all_data.zip")
    res.raise_for_status()
    yield "Received WID data\n"
    zip_file = io.BytesIO(res.content)

    with zipfile.ZipFile(zip_file) as z:
        doc_index = 0
        for file_name in z.namelist():
            yield f"Processing {file_name}\n"
            with z.open(file_name) as f:
                raw = f.read().decode('utf-8')
                file_name_fields = file_name.split(".")[0].split("_")
                if len(file_name_fields) != 3:
                    # Don't save state-level data
                    yield f"Skipping {file_name}\n"
                    continue
                dataset_type = file_name_fields[1]
                country_code_alpha2 = file_name_fields[2]
                country_code = ""
                try:
                    country_code = pycountry.countries.get(
                        alpha_2=country_code_alpha2).alpha_3
                except AttributeError:
                    country_code = ""
                if len(country_code) != 3:
                    # Don't save state-level data
                    continue
                sspi_bulk_data.bulk_insert_one({
                    "SourceOrganization": "WID",
                    "SourceOrganizationName": "World Inequality Database",
                    "SourceOrganizationURL": "https://wid.world/",
                    "SourceOrganizationDownloadURL": "https://wid.world/bulk_download/wid_all_data.zip",
                    "DatasetName": file_name,
                    "CountryCode": country_code,
                    "DatasetDescription": f"World Inequality Database All {dataset_type} for {country_code}",
                    "Raw": raw,
                    "RawPage": doc_index,
                    "RawFormat": "csv"
                })
