###############################################################
# Documentation: datasets/oecd/oecd_tonrec/documentation.md #
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

# DAC2A "Aid (ODA) disbursements to countries and regions":
# DONOR.RECIPIENT.MEASURE.UNIT_MEASURE.PRICE_BASE (FLOW_TYPE is an attribute, always D).
# DONOR ALLD = Official donors (bilateral + multilateral); MEASURE 206 = ODA disbursements (net);
# USD current prices (V). RECIPIENT is wildcarded so one call returns every recipient.
OECD_TONREC_DATAFLOW = "OECD.DCD.FSD,DSD_DAC2@DF_DAC2A"
OECD_TONREC_KEY = "ALLD..206.USD.V"
OECD_TONREC_QUERY_PARAMETERS = "startPeriod=1990&dimensionAtObservation=AllDimensions"
OECD_TONREC_QUERY_CODE = "DSD_DAC2@DF_DAC2A(ALLD..206.USD.V)"
OECD_TONREC_COUNTRY_CODE_COLUMN = "RECIPIENT"
OECD_TONREC_ROW_FILTERS = {
    "DONOR": "ALLD",
    "MEASURE": "206",
    "UNIT_MEASURE": "USD",
    "PRICE_BASE": "V",
    "UNIT_MULT": "6",
}


def describe_oecd_tonrec_row(row: dict) -> str:
    return (
        f"{row['Measure']}: {row['Flow type']} from {row['Donor']} to recipient "
        f"({row['STRUCTURE_NAME']})"
    )


@dataset_collector("OECD_TONREC")
def collect_oecd_tonrec(**kwargs):
    yield from collect_oecd_sdmx_csv(
        OECD_TONREC_DATAFLOW,
        OECD_TONREC_KEY,
        OECD_TONREC_QUERY_PARAMETERS,
        OECD_TONREC_QUERY_CODE,
        **kwargs
    )


@dataset_cleaner("OECD_TONREC")
def clean_oecd_tonrec():
    sspi_clean_api_data.delete_many({"DatasetCode": "OECD_TONREC"})
    source_info = sspi_metadata.get_source_info("OECD_TONREC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    rows = []
    for raw_document in raw_data:
        rows.extend(parse_oecd_sdmx_csv(raw_document["Raw"]))
    cleaned_data, drop_report = clean_oecd_sdmx_observations(
        rows,
        "OECD_TONREC",
        OECD_TONREC_COUNTRY_CODE_COLUMN,
        describe_oecd_tonrec_row,
        row_filters=OECD_TONREC_ROW_FILTERS,
    )
    log.info(f"OECD_TONREC clean drop report: {drop_report}")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "OECD_TONREC")
    return parse_json(cleaned_data)
