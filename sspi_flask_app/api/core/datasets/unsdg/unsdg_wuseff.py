from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("UNSDG_WUSEFF")
def collect_unsdg_wuseff(**kwargs):
    yield from collect_sdg_indicator_data("6.4.1", **kwargs)

@dataset_cleaner("UNSDG_WUSEFF")
def clean_unsdg_wuseff():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_WUSEFF"})
    source_info = sspi_metadata.get_source_info("UNSDG_WUSEFF")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_wuseff = extract_sdg(raw_data)
    idcode_map = {
        "ER_H2O_WUEYST": "UNSDG_WUSEFF",
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
    unsdg_wuseff = filter_sdg(
        extracted_unsdg_wuseff,
        idcode_map,
        rename_map,
        drop_list,
        activity="TOTAL"
    )
    count = sspi_clean_api_data.insert_many(unsdg_wuseff)
    sspi_metadata.record_dataset_range(unsdg_wuseff, "UNSDG_WUSEFF")
    return unsdg_wuseff
