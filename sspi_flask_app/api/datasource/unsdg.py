from pycountry import countries
from sspi_flask_app.models.database import sspi_raw_api_data
from sspi_flask_app.api.resources.utilities import (
    format_m49_as_string,
    string_to_float,
)
import json
import logging
import time
import requests
import math


log = logging.getLogger(__name__)

SDG_PIVOT_URL_SOURCE = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/PivotData?"
SDG_PIVOT_PAGE_SIZE = 500
SDG_PIVOT_REQUEST_TIMEOUT_SECONDS = 120
SDG_PIVOT_PAGE_MAX_ATTEMPTS = 3
SDG_PIVOT_RETRY_DELAY_SECONDS = 5
SDG_PIVOT_PAGE_DELAY_SECONDS = 1


class SDGCollectionError(RuntimeError):
    """Raised when a paged SDG pull cannot be proven complete."""


def fail_sdg_collection(message: str):
    log.error(message)
    raise SDGCollectionError(message)


def read_sdg_pivot_count(page: dict, field: str, url: str) -> int:
    value = page.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        fail_sdg_collection(f"SDG response from {url} has invalid {field}: {value!r}")
    return value


def fetch_sdg_pivot_page(url: str) -> dict:
    """
    GETs one PivotData page and checks its shape. Transport errors, HTTP
    errors and undecodable bodies are retried; a body that decodes but lacks
    the paging fields fails at once.
    """
    last_error = None
    for attempt in range(1, SDG_PIVOT_PAGE_MAX_ATTEMPTS + 1):
        try:
            response = requests.get(url, timeout=SDG_PIVOT_REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            page = response.json()
        except (requests.RequestException, ValueError) as error:
            last_error = error
            log.warning(
                "SDG request %s failed (attempt %s of %s): %s",
                url, attempt, SDG_PIVOT_PAGE_MAX_ATTEMPTS, error
            )
            if attempt < SDG_PIVOT_PAGE_MAX_ATTEMPTS:
                time.sleep(SDG_PIVOT_RETRY_DELAY_SECONDS)
            continue
        if not isinstance(page, dict) or not isinstance(page.get("data"), list):
            fail_sdg_collection(f"SDG response from {url} has no data list")
        read_sdg_pivot_count(page, "totalElements", url)
        read_sdg_pivot_count(page, "totalPages", url)
        return page
    fail_sdg_collection(
        f"SDG request {url} failed after {SDG_PIVOT_PAGE_MAX_ATTEMPTS} attempts: {last_error}"
    )


def collect_sdg_indicator_data(sdg_indicator_code: str, **kwargs):
    """
    Collects every page of the PivotData pull for one SDG indicator, e.g.
    https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=14.5.1

    All pages are fetched and the record count is checked against the API's
    totalElements before anything is written, so a failed or truncated pull
    raises SDGCollectionError and never leaves a partial RawDocumentSet.
    """
    sdg_series_url = SDG_PIVOT_URL_SOURCE + f"indicator={sdg_indicator_code}"  # identifies RawDocumentSets for SDG
    sdg_series_url_w_options = sdg_series_url + f"&pageSize={SDG_PIVOT_PAGE_SIZE}"
    first_page_url = f"{sdg_series_url_w_options}&page=1"
    first_page = fetch_sdg_pivot_page(first_page_url)
    total_elements = first_page["totalElements"]
    total_pages = first_page["totalPages"]
    if total_elements == 0:
        fail_sdg_collection(f"SDG {sdg_indicator_code} reports no records (totalElements=0)")
    minimum_pages = math.ceil(total_elements / SDG_PIVOT_PAGE_SIZE)
    if total_pages < minimum_pages:
        fail_sdg_collection(
            f"SDG {sdg_indicator_code} reports {total_pages} pages for "
            f"{total_elements} records at pageSize {SDG_PIVOT_PAGE_SIZE}"
        )
    yield f"Iterating through {total_pages} pages of source data for SDG {sdg_indicator_code}\n"
    fetched_pages = []
    fetched_count = 0
    for page_number in range(1, total_pages + 1):
        page_url = f"{sdg_series_url_w_options}&page={page_number}"
        yield "Fetching data for page {0} of {1}\n".format(page_number, total_pages)
        if page_number == 1:
            page = first_page
        else:
            time.sleep(SDG_PIVOT_PAGE_DELAY_SECONDS)
            page = fetch_sdg_pivot_page(page_url)
        if page["totalElements"] != total_elements:
            fail_sdg_collection(
                f"SDG {sdg_indicator_code} totalElements changed from {total_elements} "
                f"to {page['totalElements']} on page {page_number}; source updated mid-pull"
            )
        reported_page_number = page.get("pageNumber")
        if reported_page_number is not None and reported_page_number != page_number:
            fail_sdg_collection(
                f"SDG {sdg_indicator_code} returned pageNumber {reported_page_number} "
                f"when page {page_number} was requested"
            )
        data_list = page["data"]
        if not data_list and fetched_count < total_elements:
            fail_sdg_collection(
                f"SDG {sdg_indicator_code} page {page_number} of {total_pages} is empty "
                f"with {fetched_count} of {total_elements} records fetched"
            )
        fetched_count += len(data_list)
        fetched_pages.append((page_url, data_list))
    if fetched_count != total_elements:
        fail_sdg_collection(
            f"SDG {sdg_indicator_code} fetched {fetched_count} records across "
            f"{total_pages} pages but the API reports totalElements={total_elements}"
        )
    for page_url, data_list in fetched_pages:
        source_info = {
            "OrganizationName": "United Nations Sustainable Development Goals",
            "OrganizationCode": "UNSDG",
            "OrganizationSeriesCode": sdg_indicator_code,
            "QueryCode": sdg_indicator_code,
            "BaseURL": sdg_series_url,
            "URL": page_url
        }
        count = sspi_raw_api_data.raw_insert_many(
            data_list, source_info, **kwargs
        )
        yield f"Inserted {count} new observations into SSPI Raw Data\n"
    yield f"Collection complete for SDG {sdg_indicator_code}: {fetched_count} of {total_elements} records\n"


def extract_sdg(raw_sdg_pivot_data):
    """
    Takes in a list of observations from the sdg_pivot_data_api and returns a
    nested dictionary with only the relevant information extracted
    """
    observations_list = []
    for country_obs in raw_sdg_pivot_data:
        geoAreaCode = format_m49_as_string(country_obs["Raw"]["geoAreaCode"])
        series_identifiers = {}
        for field, value in country_obs["Raw"].items():
            if not value:
                continue
            if isinstance(value, str) and len(value) > 500:
                continue
            valid_identifier = isinstance(value, (str, float, int))
            if valid_identifier:
                series_identifiers[field] = value
        country_data = countries.get(numeric=geoAreaCode)
        if not country_data:
            continue
        sdg_series = country_obs["Raw"]["series"]
        sdg_indicator = country_obs["Raw"]["indicator"]
        annual_data_list = json.loads(country_obs["Raw"]["years"])
        CountryCode = country_data.alpha_3
        for year_obs in annual_data_list:
            value = string_to_float(year_obs["value"])
            if not isinstance(value, float) or math.isnan(value):
                continue
            extracted_obs = {
                "CountryCode": CountryCode,
                "Year": int(year_obs["year"][1:5]),
                "Value": value,
                "SDGIndicator": sdg_indicator,
                "SDGSeriesCode": sdg_series,
            }
            extracted_obs.update(series_identifiers)
            observations_list.append(extracted_obs)
    return observations_list


def filter_sdg(observations: list[dict], idcode_map: dict, rename_map={}, drop_keys=[], **kwargs):
    """
    observations - the list of observations returned by extract_sdg
    Arguments are used in this order:
    idcode_map - a dictionary specifying how to map an SDGSeriesCode to an DatasetCode
    kwargs - Use keyword arguments to filter based on fields
        - Pass a string, float, or int to retain only observations with the field
        - Pass a list of strings, floats, or ints
    rename_map - a dictionary how to rename fields in the data
    drop_keys - a list specifying keys/fields to drop from the final data
    """
    if not rename_map:  # default rename map
        rename_map = {
            "units": "Unit",
            "seriesDescription": "Description"
        }
    if not drop_keys:  # default drop list
        drop_keys = [
            "goal", "indicator", "series", "seriesCount", "target",
            "geoAreaCode", "geoAreaName"
        ]
    filtered_list = []
    for obs in observations:
        if obs["SDGSeriesCode"] not in idcode_map:
            continue
        obs["DatasetCode"] = idcode_map[obs["SDGSeriesCode"]]
        drop_obs = False
        for k, v in kwargs.items():
            if k not in obs:
                continue
            list_test = type(v) is list and obs[k] not in v
            value_test = type(v) in (str, int, float) and obs[k] != v
            if list_test or value_test:
                drop_obs = True
                break
        if drop_obs:
            continue
        for k, v in rename_map.items():
            if k in obs:
                obs[v] = obs[k]
                del obs[k]
        for k in drop_keys:
            if k in obs:
                del obs[k]
        filtered_list.append(obs)
    return filtered_list

def sdg_indicator_list():
    url = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List"
    return requests.get(url).json()

