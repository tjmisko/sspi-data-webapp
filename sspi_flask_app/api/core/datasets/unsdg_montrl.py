from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("UNSDG_MONTRL")
def collect_unsdg_montrl(**kwargs):
    yield from collect_sdg_indicator_data("12.4.1", **kwargs)

@dataset_cleaner("UNSDG_MONTRL")
def clean_unsdg_montrl():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_MONTRL"})
    source_info = sspi_metadata.get_source_info("UNSDG_MONTRL")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_montrl = extract_sdg(raw_data)
    idcode_map = {"SG_HAZ_CMRMNTRL": "UNSDG_MONTRL"}
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
    unsdg_montrl = filter_sdg(
        extracted_unsdg_montrl,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(unsdg_montrl)
    sspi_metadata.record_dataset_range(unsdg_montrl, "UNSDG_MONTRL")
    return unsdg_montrl
