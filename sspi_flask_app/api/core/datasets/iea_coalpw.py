from sspi_flask_app.api.datasource.iea import collect_iea_data, clean_iea_data_altnrg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import pandas as pd
import json


@dataset_collector("IEA_COALPW")
def collect_iea_coalpw(**kwargs):
    yield from collect_iea_data("TESbySource", **kwargs)


@dataset_cleaner("IEA_COALPW")
def clean_iea_coalpw():
    sspi_clean_api_data.delete_many({"DatasetCode": "IEA_COALPW"})
    source_info = sspi_metadata.get_source_info("IEA_COALPW")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    metadata_code_map = {
        "COAL": "TLCOAL",
        "NATGAS": "NATGAS",
        "NUCLEAR": "NCLEAR",
        "HYDRO": "HYDROP",
        "GEOTHERM": "GEOPWR",
        "COMRENEW": "BIOWAS",
        "MTOTOIL": "FSLOIL",
    }
    
    intermediate_data = pd.DataFrame(clean_iea_data_altnrg(raw_data, "IEA_COALPW"))
    intermediate_data.drop(
        intermediate_data[
            intermediate_data["CountryCode"].map(lambda s: len(s) != 3)
        ].index.tolist(),
        inplace=True,
    )
    intermediate_data["IntermediateCode"] = intermediate_data["IntermediateCode"].map(
        lambda x: metadata_code_map[x]
    )
    intermediate_data.astype({"Year": "int", "Value": "float"})
    
    # adding sum of available intermediates as an intermediate, in order to complete data
    sums = (
        intermediate_data.groupby(["Year", "CountryCode"])
        .agg({"Value": "sum"})
        .reset_index()
    )
    sums["IntermediateCode"], sums["Unit"], sums["DatasetCode"] = (
        "TTLSUM",
        "TJ",
        "IEA_COALPW",
    )
    intermediate_list = pd.concat([intermediate_data, sums])
    
    # Assign DatasetCode to all records
    intermediate_list["DatasetCode"] = "IEA_COALPW"
    
    intermediate_document_list = json.loads(
        str(intermediate_list.to_json(orient="records")),
        parse_int=int,
        parse_float=float,
    )
    
    sspi_clean_api_data.insert_many(intermediate_document_list)
    return parse_json(intermediate_document_list)