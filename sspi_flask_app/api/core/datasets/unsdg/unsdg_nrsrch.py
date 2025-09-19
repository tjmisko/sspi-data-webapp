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


@dataset_collector("UNSDG_NRSRCH")
def collect_unsdg_nrsrch(**kwargs):
    yield from collect_sdg_indicator_data("9.5.2", **kwargs)

@dataset_cleaner("UNSDG_NRSRCH")
def clean_unsdg_nrsrch():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_NRSRCH"})
    source_info = sspi_metadata.get_source_info("UNSDG_NRSRCH")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_nrsrch = extract_sdg(raw_data)
    idcode_map = {
        "GB_POP_SCIERD": "UNSDG_NRSRCH",
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
    unsdg_nrsrch = filter_sdg(
        extracted_unsdg_nrsrch,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(unsdg_nrsrch)
    sspi_metadata.record_dataset_range(unsdg_nrsrch, "UNSDG_NRSRCH")
    return unsdg_nrsrch
