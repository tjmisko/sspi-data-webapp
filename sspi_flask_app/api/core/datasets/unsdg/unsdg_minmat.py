###############################################################
# Documentation: datasets/unsdg/unsdg_minmat/documentation.md #
###############################################################
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("UNSDG_MINMAT")
def collect_unsdg_terrst(**kwargs):
    yield from collect_sdg_indicator_data("12.4.1", **kwargs)

@dataset_cleaner("UNSDG_MINMAT")
def clean_unsdg_terrst():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_MINMAT"})
    source_info = sspi_metadata.get_source_info("UNSDG_MINMAT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_terrst = extract_sdg(raw_data)
    idcode_map = {"SG_HAZ_CMRMNMT": "UNSDG_MINMAT"}
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
    unsdg_minmat = filter_sdg(
        extracted_unsdg_terrst,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(unsdg_minmat)
    sspi_metadata.record_dataset_range(unsdg_minmat, "UNSDG_MINMAT")
    return unsdg_minmat
