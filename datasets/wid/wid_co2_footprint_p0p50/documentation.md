---
DatasetType: Intermediate
DatasetName: Personal CO2 Footprint (Bottom 50%)
DatasetCode: WID_CO2_FOOTPRINT_P0P50
Description: Average per capita CO2 emissions across bottom 50% income percentiles. CO2-only version of personal carbon footprint that excludes other greenhouse gases. Provides focused analysis of carbon dioxide inequality for climate policy design.
Unit: >
    tCO2 equivalent/cap; percentile p0p50; lpfcari999
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wid/wid_co2_footprint_p0p50.py
---
# Personal Co2 Footprint

## Overview

This dataset provides personal co2 footprint from the World Inequality Database (WID). Average per capita group emissions for percentile pXpX+1 or PXpY

## Variable Details

- **WID Variable Code**: `lpfcari999`
- **Unit**: tCO2 equivalent/cap
- **Measurement Type**: Average per capita group emissions
- **Population**: The base unit is the individual (rather than the household). This is equivalent to assuming no sharing of resources within couples.. The population is comprised of individuals of all ages.

## Methodology

Methodology details not available in WID metadata.

## Data Sources

Distributional estimates: see Chancel (2021) “Global Carbon Inequality, 1990-2019“ and updates; Aggregates: see Burq and Chancel (2021) “Aggregate carbon footprints on WID.world“

## Technical Notes

### Population and Age Groups
- **Population Base**: The base unit is the individual (rather than the household). This is equivalent to assuming no sharing of resources within couples.
- **Age Coverage**: The population is comprised of individuals of all ages.

### Measurement Approach
- **Type**: Average per capita group emissions
- **Description**: Average per capita group emissions for percentile pXpX+1 or PXpY

## Data Availability

Data availability and temporal coverage depend on the underlying sources and methodological approach used by WID for this indicator.

## Usage Notes

This dataset is part of the World Inequality Database collection and follows WID's methodological standards and data quality protocols. Users should refer to WID documentation for detailed methodological explanations and data limitations.

## References

- **Source**: World Inequality Database (WID.world)
- **Variable**: lpfcari999
- **Documentation**: See WID.world for complete methodological documentation