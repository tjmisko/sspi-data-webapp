import csv
import logging
import requests
import time
import pycountry
from bs4 import BeautifulSoup
from io import StringIO
from typing import Callable
from ..resources.utilities import string_to_float
from sspi_flask_app.models.database import sspi_raw_api_data
import urllib3
import ssl

log = logging.getLogger(__name__)

# Generic OECD SDMX REST API (sdmx.oecd.org) constants shared by every
# OECD dataset collected through collect_oecd_sdmx_csv below.
OECD_ORGANIZATION_NAME = "Organisation for Economic Co-operation and Development"
OECD_ORGANIZATION_CODE = "OECD"
OECD_SDMX_DATA_BASE_URL = "https://sdmx.oecd.org/public/rest/data/"
# SDMX-CSV 2.0 with labels=name adds a human-readable label column next to
# every coded column (e.g. MEASURE -> "Measure", UNIT_MEASURE -> "Unit of
# measure", UNIT_MULT -> "Unit multiplier"), so cleaners can take Unit and
# Description from the source's own metadata instead of hardcoding them.
OECD_SDMX_CSV_LABELS_ACCEPT_HEADER = "application/vnd.sdmx.data+csv;version=2.0.0;labels=name"
OECD_SDMX_DEFAULT_QUERY_PARAMETERS = "startPeriod=1990&dimensionAtObservation=AllDimensions"
OECD_SDMX_REQUEST_TIMEOUT_SECONDS = 120
OECD_SDMX_NO_RESULTS_STATUS_CODE = 404
OECD_SDMX_UNIT_LABEL_COLUMNS = ("Unit of measure", "Unit multiplier", "Price base")

def collect_oecd_indicator(oecd_indicator_code, **kwargs):
    """
    The CustomHTTPAdapter class and the legacy session are necessary to connect to the OECD SDMX API
    because OECD does not support RFC 5746 secure renegotiation, which is the default for OpenSSL 3

    See Harry Mallon's answer and ahmkara's elaboration on StackOverflow:
    https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled/71646353#71646353
    """
    class CustomHttpAdapter(requests.adapters.HTTPAdapter):
        # "Transport adapter" that allows us to use custom ssl_context.

        def __init__(self, ssl_context=None, **kwargs):
            self.ssl_context = ssl_context
            super().__init__(**kwargs)

        def init_poolmanager(self, connections, maxsize, block=False):
            self.poolmanager = urllib3.poolmanager.PoolManager(
                num_pools=connections, maxsize=maxsize,
                block=block, ssl_context=self.ssl_context)

    def get_legacy_session():
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        session = requests.session()
        session.mount('https://', CustomHttpAdapter(ctx))
        return session

    sdmx_url_oecd_metadata = f"https://stats.oecd.org/RestSDMX/sdmx.ashx/GetKeyFamily/{
        oecd_indicator_code}"
    sdmx_url_oecd = f"https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/{
        oecd_indicator_code}"
    yield "Sending Metadata Request to OECD SDMX API\n"
    metadata_obj = get_legacy_session().get(sdmx_url_oecd_metadata)
    metadata = str(metadata_obj.content)
    yield "Metadata Received from OECD SDMX API.  Sending Data Request to OECD SDMX API\n"
    yield "Sending Data Request to OECD SDMX API\n"
    response_obj = get_legacy_session().get(sdmx_url_oecd)
    observation = str(response_obj.content)
    yield "Data Received from OECD SDMX API.  Storing Data in SSPI Raw Data\n"
    source_info = {
        "OrganizationName": "Organisation for Economic Development and Coorperation",
        "OrganizationCode": "OECD",
        "OrganizationSeriesCode": oecd_indicator_code,
        "QueryCode": oecd_indicator_code,
        "MetadataURL": sdmx_url_oecd_metadata,
        "URL": sdmx_url_oecd,
    }
    sspi_raw_api_data.raw_insert_one(
        observation, source_info, Metadata=metadata, **kwargs
    )
    yield "Data Stored in SSPI Raw Data.  Collection Complete\n"

# ghg (total), ghg (index1990), ghg (ghg cap), co2 (total)


def extract_all_oecd_series(oecd_XML):
    xml_soup = bs.BeautifulSoup(oecd_XML, "lxml")
    series_list = xml_soup.find_all("series")
    return series_list


def filter_oecd_series_list(series_list, filterVAR, oecd_indicator_code, IndicatorCode):
    # Return a list of series that match the filterVAR variable name
    document_list = []
    for i, series in enumerate(series_list):
        series_key, series_attributes = series.find(
            "serieskey"), series.find("attributes")
        VAR = series_key.find("value", attrs={"concept": "VAR"}).get("value")
        if VAR != filterVAR:
            continue
        id_info = {
            "CountryCode": series_key.find("value", attrs={"concept": "COU"}).get("value"),
            "VariableCodeOECD": VAR,
            "IndicatorCodeOECD": oecd_indicator_code,
            "Source": "OECD",
            "IndicatorCode": IndicatorCode,
            "Unit": series_attributes.find("value", attrs={"concept": "UNIT"}).get("value"),
            "Pollutant": series_key.find("value", attrs={"concept": "POL"}).get("value"),
        }
        new_documents = [{"Year": obs.find("time").text, "Value": obs.find(
            "obsvalue").get("value")} for obs in series.find_all("obs")]
        for doc in new_documents:
            doc.update(id_info)
        document_list.extend(new_documents)
    return document_list


def filterSeriesListSeniors(series_list, filterIND, oecd_indicator_code, IndicatorCode):
    # Return a list of series that match the filterVAR variable name
    document_list = []
    for i, series in enumerate(series_list):
        series_key, series_attributes = series.find(
            "serieskey"), series.find("attributes")
        IND = series_key.find("value", attrs={"concept": "IND"}).get("value")
        if IND != filterIND:
            continue
        id_info = {
            "IndicatorCode": IndicatorCode,
            "CountryCode": series_key.find("value", attrs={"concept": "COU"}).get("value"),
            "Unit": series_attributes.find("value", attrs={"concept": "UNIT"}).get("value"),
            "VariableCodeOECD": IND,
            "IndicatorCodeOECD": oecd_indicator_code,
            "Source": "OECD",
        }
        new_documents = [{"Year": obs.find("time").text, "Value": obs.find(
            "obsvalue").get("value")} for obs in series.find_all("obs")]
        for doc in new_documents:
            doc.update(id_info)
        document_list.extend(new_documents)
    return document_list


def organizeOECDdata(series_list):
    listofdicts = []
    for series in series_list:
        SeriesKeys = series.findall(
            ".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}SeriesKey/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Attributes = series.findall(
            ".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Attributes/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Observation_time = series.findall(
            ".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Obs/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Time")
        Observation_value = series.findall(
            ".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Obs/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}ObsValue")
        relevant_attribute = [
            True for x in Attributes if x.attrib["value"] == "T_CO2_EQVT"]
        relevant_key = [True for y in SeriesKeys if y.attrib["value"] == "CO2"]
        if relevant_attribute and relevant_key:
            year_lst = [year.text for year in Observation_time]
            obs_lst = [obs.attrib["value"] for obs in Observation_value]
            for value in SeriesKeys:
                if value.attrib["concept"] == "COU":
                    cou = value.attrib["value"]
                    i = 0
                    while i <= (len(year_lst) - 1):
                        new_observation = {
                            "CountryCode": cou,
                            "IndicatorCode": "GTRANS",
                            "Source": "OECD",
                            "YEAR": int(year_lst[i]),
                            "RAW": string_to_float(obs_lst[i])
                        }
                        listofdicts.append(new_observation)
                        i += 1
    return listofdicts


def OECD_country_list(series_list):
    country_lst = []
    for series in series_list:
        SeriesKeys = series.findall(
            ".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}SeriesKey/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Attributes = series.findall(
            ".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Attributes/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        relevant_attribute = [
            True for x in Attributes if x.attrib["value"] == "T_CO2_EQVT"]
        relevant_key = [True for y in SeriesKeys if y.attrib["value"] == "CO2"]
        if relevant_attribute and relevant_key:
            for value in SeriesKeys:
                if value.attrib["concept"] == "COU":
                    cou = value.attrib["value"]
                    country_lst.append(cou)
    print("this is the oecd country list:" + str(country_lst))
    return country_lst


def collect_oecd_sdmx_data(oecd_series_code, query_parameters="", metadata_url="", **kwargs):
    metadata = None
    if metadata_url:
        yield f"Sending Metadata Request to OECD SDMX API ({metadata_url})\n"
        meta_res = requests.get(metadata_url)
        metadata = str(meta_res.content)
    yield "Sending Data Request to OECD SDMX API\n"
    base_url = "https://sdmx.oecd.org/public/rest/data/"
    if not query_parameters:
        query_parameters = "startPeriod=1990&dimensionAtObservation=AllDimensions"
    url = f"{base_url}{oecd_series_code}?{query_parameters}"
    res = requests.get(url)
    raw_data = str(res.content)
    source_info = {
        "OrganizationName": "Organisation for Economic Development and Coorperation",
        "OrganizationCode": "OECD",
        "OrganizationSeriesCode": oecd_series_code,
        "QueryCode": oecd_series_code,
        "MetadataURL": metadata_url,
        "URL": url,
    }
    sspi_raw_api_data.raw_insert_one(
        raw_data, source_info, Metadata=metadata, **kwargs
    )
    yield f"Data collection complete for OECD series {oecd_series_code}\n"


def collect_oecd_sdmx_data_foraid(oecd_series_code, filter_parameters="....", query_parameters="", metadata_url="", **kwargs):
    """
    Code had to be specially adapted to foreign aid data to iterate through countries one by one
    """
    metadata = None
    g_size = 20
    all_country_codes = [cou.alpha_3 for cou in pycountry.countries]
    country_groups = ["+".join(all_country_codes[i:i + g_size])
                      for i in range(0, len(all_country_codes), g_size)]
    for g in country_groups:
        yield f"Processing group of countries: {g}\n"
    if metadata_url:
        yield f"Sending Metadata Request to OECD SDMX API ({metadata_url})\n"
        meta_res = requests.get(metadata_url)
        metadata = str(meta_res.content)
    for cou_g in country_groups:
        yield f"Sending Data Request to OECD SDMX API for {cou_g}\n"
        base_url = "https://sdmx.oecd.org/public/rest/data/"
        cou_filter_parameters = filter_parameters[0] + \
            cou_g + filter_parameters[1:]
        if not query_parameters:
            query_parameters = "startPeriod=1990&dimensionAtObservation=AllDimensions"
        url = f"{base_url}{
            oecd_series_code}/{cou_filter_parameters}?{query_parameters}"
        res = requests.get(url)
        source_info = {
            "OrganizationName": "Organisation for Economic Development and Coorperation",
            "OrganizationCode": "OECD",
            "OrganizationSeriesCode": oecd_series_code,
            "QueryCode": oecd_series_code,
            "MetadataURL": metadata_url,
            "URL": url,
            "BaseURL": f"{base_url}/{oecd_series_code}",
        }
        raw_data = str(res.content)
        if raw_data == "NoRecordsFound":
            print(f"No records found for {cou_g}! Skipping Insertion")
            continue
        sspi_raw_api_data.raw_insert_one(
            raw_data, source_info, Metadata=metadata, **kwargs
        )
        time.sleep(15)
    yield f"Data collection complete for OECD series {oecd_series_code}\n"


def parse_oecd_observations(xml_string) -> list[dict]:
    soup = BeautifulSoup(xml_string, "lxml-xml")
    observations = soup.find_all("Obs")
    formatted_observations = []
    for obs in observations:
        formatted_obs = {}
        value = obs.find("ObsValue")
        if value:
            formatted_obs["Value"] = value.attrs.get("value")
        for value in obs.find_all("Value"):
            id = value.attrs.get("id")
            if id == "TIME_PERIOD":
                formatted_obs["Year"] = value.attrs.get("value")
            else:
                formatted_obs[id] = value.attrs.get("value")
        formatted_observations.append(formatted_obs)
    return formatted_observations


# ---------------------------------------------------------------------------
# Generic OECD SDMX REST helpers (sdmx.oecd.org). New OECD datasets should use
# these rather than the legacy stats.oecd.org functions above.
# ---------------------------------------------------------------------------

def build_oecd_sdmx_data_url(dataflow: str, key: str, query_parameters: str = "") -> str:
    """
    Build the SDMX REST data URL for a dataflow reference and series key.

    :param dataflow: agency,id[,version] reference, e.g. "OECD.DCD.FSD,DSD_DAC1@DF_DAC1"
        (omitting the version resolves to the latest one).
    :param key: dot-separated dimension key, e.g. "._Z.1010._Z.1140.USD.V"
        (an empty position is a wildcard).
    :param query_parameters: raw query string without the leading "?".
    """
    url = f"{OECD_SDMX_DATA_BASE_URL}{dataflow}/{key}"
    if not query_parameters:
        return url
    return f"{url}?{query_parameters}"


def collect_oecd_sdmx_csv(
    dataflow: str,
    key: str,
    query_parameters: str,
    dataset_query_code: str,
    accept_header: str = OECD_SDMX_CSV_LABELS_ACCEPT_HEADER,
    **kwargs
):
    """
    Collect one OECD SDMX data query as CSV text and store it as a single raw
    document (raw_insert_one fragments the string if it exceeds the BSON limit).

    HTTP 404 is the SDMX "NoResultsFound" status: nothing is inserted and a
    message is yielded. Any other non-200 status raises requests.HTTPError so a
    failed pull never masquerades as data.

    :param dataflow: agency,id[,version] reference, e.g. "OECD.DCD.FSD,DSD_DAC1@DF_DAC1".
        Stamped verbatim as Source.OrganizationSeriesCode.
    :param key: dot-separated dimension key selecting the series.
    :param query_parameters: raw query string, e.g. "startPeriod=2000".
        Pass "" to use OECD_SDMX_DEFAULT_QUERY_PARAMETERS.
    :param dataset_query_code: stable Source.QueryCode stamped on the raw
        document; the dataset documentation's Source must match it exactly.
    :param accept_header: SDMX media type; defaults to SDMX-CSV 2.0 with labels.
    """
    if not query_parameters:
        query_parameters = OECD_SDMX_DEFAULT_QUERY_PARAMETERS
    url = build_oecd_sdmx_data_url(dataflow, key, query_parameters)
    yield f"Sending Data Request to OECD SDMX API ({url})\n"
    response = requests.get(
        url,
        headers={"Accept": accept_header},
        timeout=OECD_SDMX_REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == OECD_SDMX_NO_RESULTS_STATUS_CODE:
        yield f"OECD SDMX API returned 404 NoResultsFound for {dataflow} key {key}; nothing inserted\n"
        return
    response.raise_for_status()
    raw_csv_string = response.text
    source_info = {
        "OrganizationName": OECD_ORGANIZATION_NAME,
        "OrganizationCode": OECD_ORGANIZATION_CODE,
        "OrganizationSeriesCode": dataflow,
        "QueryCode": dataset_query_code,
        "URL": url,
    }
    fragment_count = sspi_raw_api_data.raw_insert_one(raw_csv_string, source_info, **kwargs)
    yield (
        f"Stored {len(raw_csv_string)} characters of SDMX CSV for {dataset_query_code} "
        f"in {fragment_count} raw document(s)\n"
    )
    yield f"Data collection complete for OECD SDMX query {dataset_query_code}\n"


def parse_oecd_sdmx_csv(raw_csv_string: str) -> list[dict]:
    """
    Parse SDMX-CSV text into one dict per row keyed by the header columns.
    Tolerates a UTF-8 byte-order mark and trailing blank lines.
    """
    if not raw_csv_string:
        return []
    text = raw_csv_string.lstrip("\ufeff")
    reader = csv.DictReader(StringIO(text))
    return [row for row in reader if any(value for value in row.values())]


def oecd_sdmx_unit_from_row(row: dict, label_columns=OECD_SDMX_UNIT_LABEL_COLUMNS) -> str:
    """
    Compose a Unit string from the SDMX label columns present on a row, e.g.
    "US dollar, Millions, Current prices". Empty or absent labels are skipped.
    """
    labels = [row.get(column, "") for column in label_columns]
    return ", ".join(label for label in labels if label)


def clean_oecd_sdmx_observations(
    rows: list[dict],
    dataset_code: str,
    country_code_column: str,
    description: str | Callable[[dict], str],
    row_filters: dict[str, str] | None = None,
    unit: str | Callable[[dict], str] = oecd_sdmx_unit_from_row,
    value_column: str = "OBS_VALUE",
    time_period_column: str = "TIME_PERIOD",
) -> tuple[list[dict], dict]:
    """
    Turn parsed SDMX-CSV rows into SSPI clean observations.

    Returns (clean_observations, drop_report). Nothing is dropped silently:
    - rows failing ``row_filters`` (column -> required code) are counted per column;
    - rows whose ``country_code_column`` is not an ISO 3166-1 alpha-3 country in
      pycountry (DAC aggregates such as DAC, ALLD, DPGC, LDC, XKV) are counted
      per code;
    - rows with an empty or non-numeric value are counted;
    - rows whose time period is not a plain year are counted.

    Values are kept exactly as published (negative net flows included) and are
    not rescaled: the Unit string carries the source's own unit multiplier label.
    """
    row_filters = row_filters or {}
    clean_list = []
    drop_report = {
        "FilteredRows": {column: 0 for column in row_filters},
        "NonCountryCodes": {},
        "MissingValueRows": 0,
        "NonAnnualPeriodRows": 0,
    }
    for row in rows:
        failed_filter = next(
            (column for column, code in row_filters.items() if row.get(column) != code),
            None,
        )
        if failed_filter is not None:
            drop_report["FilteredRows"][failed_filter] += 1
            continue
        country_code = row.get(country_code_column, "")
        if not pycountry.countries.get(alpha_3=country_code):
            drop_report["NonCountryCodes"][country_code] = (
                drop_report["NonCountryCodes"].get(country_code, 0) + 1
            )
            continue
        value = string_to_float(row.get(value_column, ""))
        if not isinstance(value, float):
            drop_report["MissingValueRows"] += 1
            continue
        time_period = row.get(time_period_column, "")
        if not time_period.isdigit():
            drop_report["NonAnnualPeriodRows"] += 1
            continue
        clean_list.append({
            "CountryCode": country_code,
            "DatasetCode": dataset_code,
            "Description": description(row) if callable(description) else description,
            "Year": int(time_period),
            "Unit": unit(row) if callable(unit) else unit,
            "Value": value,
        })
    log_oecd_sdmx_drop_report(dataset_code, drop_report)
    return clean_list, drop_report


def log_oecd_sdmx_drop_report(dataset_code: str, drop_report: dict) -> None:
    filtered = {k: v for k, v in drop_report["FilteredRows"].items() if v}
    if filtered:
        log.warning(f"OECD {dataset_code}: dropped rows failing filters {filtered}")
    if drop_report["NonCountryCodes"]:
        log.warning(
            f"OECD {dataset_code}: dropped rows for non-country codes "
            f"{drop_report['NonCountryCodes']}"
        )
    if drop_report["MissingValueRows"]:
        log.warning(f"OECD {dataset_code}: dropped {drop_report['MissingValueRows']} rows with missing values")
    if drop_report["NonAnnualPeriodRows"]:
        log.warning(f"OECD {dataset_code}: dropped {drop_report['NonAnnualPeriodRows']} rows with non-annual periods")
