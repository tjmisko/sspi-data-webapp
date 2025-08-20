from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("UNSDG_PBTACC")
def collect_unsdg_pbtacc(**kwargs):
    yield from collect_sdg_indicator_data("11.2.1", **kwargs)

@dataset_cleaner("UNSDG_PBTACC")
def clean_unsdg_pbtacc():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_PBTACC"})
    source_info = sspi_metadata.get_source_info("UNSDG_PBTACC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_pbtacc = extract_sdg(raw_data)
    idcode_map = {
        "SP_TRN_PUBL": "UNSDG_PBTACC",
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
    unsdg_pbtacc = filter_sdg(
        extracted_unsdg_pbtacc,
        idcode_map,
        rename_map,
        drop_list,
        age="ALLAGE",
        sex="BOTHSEX",
        disability_status="_T"
    )
    for document in unsdg_pbtacc:
        document["AdditionalIdentifiers"] = {
            "CityCode": document.get("cities")
        }
    count = sspi_clean_api_data.insert_many(unsdg_pbtacc)
    sspi_metadata.record_dataset_range(unsdg_pbtacc, "UNSDG_PBTACC")
    return unsdg_pbtacc
