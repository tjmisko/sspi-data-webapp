import json
from sspi_flask_app.api.datasource.ilo import collect_ilo_data, extract_ilo, filter_ilo
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("ILO_EMPLOY_TO_POP_MALE")
def collect_ilo_employ_to_pop_male(**kwargs):
    yield from collect_ilo_data(
        "DF_EMP_DWAP_SEX_AGE_RT",
        QueryParams=".A..SEX_M.AGE_YTHADULT_Y15-64",
        URLParams=["startPeriod=2000"],
        **kwargs
    )


@dataset_cleaner("ILO_EMPLOY_TO_POP_MALE")
def clean_ilo_employ_to_pop_male():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_EMPLOY_TO_POP_MALE"})
    source_info = sspi_metadata.get_source_info("ILO_EMPLOY_TO_POP_MALE")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_ilo(raw_data)
    obs_list = filter_ilo(extracted_data, "ILO_EMPLOY_TO_POP_MALE", SEX="SEX_M", AGE="AGE_YTHADULT_Y15-64")
    sspi_clean_api_data.insert_many(obs_list)
    sspi_metadata.record_dataset_range(obs_list, "ILO_EMPLOY_TO_POP_MALE")
    return parse_json(obs_list)
