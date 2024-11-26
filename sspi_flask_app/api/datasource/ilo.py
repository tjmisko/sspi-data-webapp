import requests
from sspi_flask_app.models.database import sspi_raw_api_data
from io import BytesIO
import zipfile

# def collectILOData(ILOIndicatorCode, IndicatorCode, QueryParams="....", **kwargs):
#     yield "Sending Data Request to ILO API\n"
#     response_obj = requests.get(f"https://www.ilo.org/sdmx/rest/data/ILO,{ILOIndicatorCode}/{QueryParams}")
#     print(str(response_obj.content))
#     observation = str(response_obj.content)
#     yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
#     count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
#     yield f"Inserted {count} observations into the database."


def collectILOData(ILOIndicatorCode, IndicatorCode, **kwargs):
    yield "Sending Data Request to ILO API\n"
    response_obj = requests.get("https://sdmx.ilo.org/rest/data/ILO,DF_ILR_CBCT_NOC_RT/?format=csv&startPeriod=1990-01-01&endPeriod=2024-12-31")
    print(response_obj.headers.get('Content-Type'))
    if response_obj.status_code != 200:
        err = f"(HTTP Error {response_obj.status_code})"
        yield "Failed to fetch data from source" + err
        return
    csv_string = response_obj.content.decode("utf-8")
    print(csv_string[:500])
    count = sspi_raw_api_data.raw_insert_one(
                {"csv": csv_string}, IndicatorCode, **kwargs
        )
    print("Inserted count:", count)
    yield f"Inserted {count} observations into the database."
    yield f"Collection complete for {IndicatorCode} (ILO {ILOIndicatorCode})"
   # print(str(response_obj.content))
   # observation = str(response_obj.content)
   # print("Content-Type:", response_obj.headers.get('Content-Type')) #Content-Type: application/vnd.sdmx.data+json; version=2; charset=utf-8
   # observation = response_obj.json()
   # print(type(observation))
   # response_text = response_obj.content.decode('utf-8')  # Decode bytes to string
   # observation = json.loads(response_text)  # Parse JSON from the decoded string
#     yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
#     count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
#     print("Inserted count:", count)
#     yield f"Inserted {count} observations into the database."
#     retrieved_data = sspi_raw_api_data.find_one({"IndicatorCode": 'COLBAR'})
#    # print("Retrieved data:", retrieved_data)
#     print("Type of 'Raw' field:", type(retrieved_data.get("Raw", None)))
