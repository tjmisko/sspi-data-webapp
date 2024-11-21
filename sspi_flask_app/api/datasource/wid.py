import requests
import io
import zipfile


def bulkCollectWIDData(**kwargs):
    yield "Requesting WID data from source"
    res = requests.get("https://wid.world/bulk_download/wid_all_data.zip")
    res.raise_for_status()
    yield "Received WID data"
    zip_file = io.BytesIO(res.content)

    with zipfile.ZipFile(zip_file) as z:
        for file_name in z.namelist():
            yield f"Reading {file_name}"
