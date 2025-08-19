from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("UNSDG_WTSTRS")
def collect_unsdg_wtstrs(**kwargs):
    yield from collect_sdg_indicator_data("6.4.2", **kwargs)

@dataset_cleaner("UNSDG_WTSTRS")
def clean_unsdg_wtstrs():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_WTSTRS"})
    source_info = sspi_metadata.get_source_info("UNSDG_WTSTRS")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_wtstrs = extract_sdg(raw_data)
    idcode_map = {
        "ER_H2O_STRESS": "UNSDG_WTSTRS",
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
    unsdg_wtstrs = filter_sdg(
        extracted_unsdg_wtstrs,
        idcode_map,
        rename_map,
        drop_list,
        activity="TOTAL"
    )
    count = sspi_clean_api_data.insert_many(unsdg_wtstrs)
    sspi_metadata.record_dataset_range(unsdg_wtstrs, "UNSDG_WTSTRS")
    return unsdg_wtstrs
