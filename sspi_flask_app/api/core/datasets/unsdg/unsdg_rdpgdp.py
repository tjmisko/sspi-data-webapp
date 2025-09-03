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


@dataset_collector("UNSDG_RDPGDP")
def collect_unsdg_rdpgdp(**kwargs):
    yield from collect_sdg_indicator_data("9.5.1", **kwargs)

@dataset_cleaner("UNSDG_RDPGDP")
def clean_unsdg_rdpgdp():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_RDPGDP"})
    source_info = sspi_metadata.get_source_info("UNSDG_RDPGDP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_rdpgdp = extract_sdg(raw_data)
    idcode_map = {
        "GB_XPD_RSDV": "UNSDG_RDPGDP",
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
    unsdg_rdpgdp = filter_sdg(
        extracted_unsdg_rdpgdp,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(unsdg_rdpgdp)
    sspi_metadata.record_dataset_range(unsdg_rdpgdp, "UNSDG_RDPGDP")
    return unsdg_rdpgdp
