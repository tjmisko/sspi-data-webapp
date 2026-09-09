###############################################################
# Documentation: datasets/oecd/oecd_totdon/documentation.md #
###############################################################
import logging
from sspi_flask_app.api.datasource.oecdstat import (
    collect_oecd_sdmx_csv,
    parse_oecd_sdmx_csv,
    clean_oecd_sdmx_observations,
)
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

log = logging.getLogger(__name__)

# DAC1 "Flows by provider": DONOR.SECTOR.MEASURE.TYING_STATUS.FLOW_TYPE.UNIT_MEASURE.PRICE_BASE
# MEASURE 1010 = Official Development Assistance (ODA); FLOW_TYPE 1140 = Disbursements, net;
# USD current prices (V). SECTOR and TYING_STATUS must be _Z (1000/_T return 404).
OECD_TOTDON_DATAFLOW = "OECD.DCD.FSD,DSD_DAC1@DF_DAC1"
OECD_TOTDON_KEY = "._Z.1010._Z.1140.USD.V"
OECD_TOTDON_QUERY_PARAMETERS = "startPeriod=1990&dimensionAtObservation=AllDimensions"
OECD_TOTDON_QUERY_CODE = "DSD_DAC1@DF_DAC1(._Z.1010._Z.1140.USD.V)"
OECD_TOTDON_COUNTRY_CODE_COLUMN = "DONOR"
OECD_TOTDON_ROW_FILTERS = {
    "MEASURE": "1010",
    "FLOW_TYPE": "1140",
    "UNIT_MEASURE": "USD",
    "PRICE_BASE": "V",
    "UNIT_MULT": "6",
}


def describe_oecd_totdon_row(row: dict) -> str:
    return (
        f"{row['Measure']}: {row['Flow type']} from donor "
        f"({row['STRUCTURE_NAME']})"
    )


@dataset_collector("OECD_TOTDON")
def collect_oecd_totdon(**kwargs):
    yield from collect_oecd_sdmx_csv(
        OECD_TOTDON_DATAFLOW,
        OECD_TOTDON_KEY,
        OECD_TOTDON_QUERY_PARAMETERS,
        OECD_TOTDON_QUERY_CODE,
        **kwargs
    )


@dataset_cleaner("OECD_TOTDON")
def clean_oecd_totdon():
    sspi_clean_api_data.delete_many({"DatasetCode": "OECD_TOTDON"})
    source_info = sspi_metadata.get_source_info("OECD_TOTDON")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    rows = []
    for raw_document in raw_data:
        rows.extend(parse_oecd_sdmx_csv(raw_document["Raw"]))
    cleaned_data, drop_report = clean_oecd_sdmx_observations(
        rows,
        "OECD_TOTDON",
        OECD_TOTDON_COUNTRY_CODE_COLUMN,
        describe_oecd_totdon_row,
        row_filters=OECD_TOTDON_ROW_FILTERS,
    )
    log.info(f"OECD_TOTDON clean drop report: {drop_report}")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "OECD_TOTDON")
    return parse_json(cleaned_data)
