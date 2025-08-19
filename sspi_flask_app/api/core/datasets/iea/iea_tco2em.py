import pycountry
from sspi_flask_app.api.datasource.iea import collect_iea_data, clean_IEA_data_GTRANS
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("IEA_TCO2EM")
def collect_iea_tco2em(**kwargs):
    yield from collect_iea_data("CO2BySector", **kwargs)


@dataset_cleaner("IEA_TCO2EM")
def clean_iea_tco2em():
    sspi_clean_api_data.delete_many({"DatasetCode": "IEA_TCO2EM"})
    source_info = sspi_metadata.get_source_info("IEA_TCO2EM")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    clean_list = []
    for obs in raw_data:
        iso3 = obs["Raw"]["country"]
        country_data = pycountry.countries.get(alpha_3=iso3)
        value = obs["Raw"]['value']
        series_label = obs["Raw"]["seriesLabel"]
        if series_label != "Transport Sector":
            continue
        if not country_data:
            continue
        if not value and (type(value) is not float or type(value) is not int):
            continue
        clean_obs = {
            "CountryCode": iso3,
            "DatasetCode": "IEA_TCO2EM",
            "Year": int(obs["Raw"]["year"]),
            "Value": obs["Raw"]["value"] * 10**9,
            "Unit": "Tonnes C02 per inhabitant",
        }
        clean_list.append(clean_obs)
    sspi_clean_api_data.insert_many(clean_list)
    sspi_metadata.record_dataset_range(clean_list, "IEA_TCO2EM")
    return parse_json(clean_list)
