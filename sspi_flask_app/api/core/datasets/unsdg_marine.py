from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata


@dataset_collector("UNSDG_MARINE")
def collect_unsdg_marine(**kwargs):
    yield from collect_sdg_indicator_data("14.5.1", **kwargs)

@dataset_cleaner("UNSDG_MARINE")
def clean_unsdg_marine():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_MARINE"})
    source_info = sspi_metadata.get_source_info("UNSDG_MARINE")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_marine = extract_sdg(raw_data)
    idcode_map = {
        "ER_MRN_MPA": "UNSDG_MARINE",
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
    unsdg_freshwt = filter_sdg(
        extracted_unsdg_marine,
        idcode_map,
        rename_map,
        drop_list,
    )
    count = sspi_clean_api_data.insert_many(unsdg_freshwt)
    return unsdg_freshwt
