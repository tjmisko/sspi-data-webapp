---
DatasetType: Intermediate
DatasetName: Personal Carbon Footprint - Total (Top 10%)
DatasetCode: WID_CARBON_TOT_P90P100
Description: Average per capita total carbon emissions across top 10% income percentiles. Combines both consumption and investment-related emissions for comprehensive personal carbon footprint. Includes emissions from individual consumption, government expenditures, and individual investments.
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
---
# Personal Carbon Footprint

## Overview

This dataset provides personal carbon footprint from the World Inequality Database (WID). Average per capita group emissions for percentile pXpX+1 or PXpY

## Variable Details

- **WID Variable Code**: `lpfghgi999`
- **Unit**: tCO2 equivalent/cap
- **Measurement Type**: Average per capita group emissions
- **Population**: The base unit is the individual (rather than the household). This is equivalent to assuming no sharing of resources within couples.. The population is comprised of individuals of all ages.

## Methodology

Modeled estimates based on the systematic combination of survey and tax data, national accounts and Environment Input-Output tables. Estimates include emissions embedded in imports and exports of goods and services. This indicator represents emissions associated with individual consumption and government collective expenditures. This indicator also includes a component representing emissions associated with individuals' investments. While these estimates provide WID.world's best efforts to measure emissions inequality across the world, it should be noted that estimates quality is “low to very low“ given poor data quality and availability on pollution inequality in most countries. It should also be noted that there are different ways to measure carbon footprints, which can lead to different takes on the issue (inequality in emissions is lower when looking at consumption-related emissions only and increases when factoring in investment-related emissions). See sources for more details.

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
- **Variable**: lpfghgi999
- **Documentation**: See WID.world for complete methodological documentation