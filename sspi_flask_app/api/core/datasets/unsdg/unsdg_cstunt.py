from sspi_flask_app.api.core.datasets import dataset_cleaner, dataset_collector
from sspi_flask_app.api.datasource.unsdg import (
    collect_sdg_indicator_data,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_metadata,
    sspi_raw_api_data,
)


@dataset_collector("UNSDG_CSTUNT")
def collect_unsdg_cstunt(**kwargs):
    yield from collect_sdg_indicator_data("2.2.1", **kwargs)

@dataset_cleaner("UNSDG_CSTUNT")
def clean_unsdg_cstunt():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_CSTUNT"})
    source_info = sspi_metadata.get_source_info("UNSDG_CSTUNT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_cstunt = extract_sdg(raw_data)
    idcode_map = {
        "SH_STA_STNT": "UNSDG_CSTUNT",
    }
    rename_map = {"units": "Unit", "seriesDescription": "Description"}
    drop_list = [
        "goal",
        "indicator",
        "series",
        "seriesCount",
        "target",
        "geoAreaCode",
        "geoAreaName",
    ]
    unsdg_cstunt = filter_sdg(
        extracted_unsdg_cstunt,
        idcode_map,
        rename_map,
        drop_list,
        sex="BOTHSEX",
        age="<5Y"
    )
    count = sspi_clean_api_data.insert_many(unsdg_cstunt)
    sspi_metadata.record_dataset_range(unsdg_cstunt, "UNSDG_CSTUNT")
    return unsdg_cstunt
