---
DatasetType: Intermediate
DatasetName: Personal Carbon Footprint - Consumption (Full Distribution)
DatasetCode: WID_CARBON_CONS_P0P100
Description: Average per capita carbon emissions from consumption across full income distribution. Represents emissions from individual consumption and government collective expenditures. Excludes investment-related emissions. Provides comprehensive view of consumption-based carbon inequality across all income percentiles.
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wid/wid_carbon_cons_p0p100.py
---

# Personal Carbon Footprint - Consumption (Full Distribution)

## Overview

This dataset provides comprehensive carbon inequality data from the World Inequality Database (WID), specifically measuring personal carbon footprints from consumption activities across the complete income distribution. The data represents one of the four core distributional carbon indicators identified as essential for studying carbon inequality research.

## Variable Details

- **WID Variable Code**: `lcfghgi999`
- **Unit**: tonnes CO2 equivalent per capita (tCO2 equivalent/cap)
- **Scope**: Greenhouse gas emissions (CO2 + other greenhouse gases)
- **Coverage**: Full income distribution (p0p100)
- **Population**: All ages (999)

## Methodology

The estimates are based on modeled calculations that systematically combine:

- Survey and tax data
- National accounts
- Environmental Input-Output tables

The methodology includes emissions embedded in imports and exports of goods and services, providing a consumption-based accounting approach that captures the full carbon footprint of consumption patterns across income percentiles.

## Emissions Scope

This indicator specifically measures emissions associated with:

- **Individual consumption**: Personal spending on goods and services
- **Government collective expenditures**: Public services and infrastructure

**Exclusions**: This indicator does NOT include emissions associated with individual investments or capital formation.

## Research Applications

### Carbon Inequality Analysis
- Study how consumption-based carbon footprints vary across income percentiles
- Analyze distributional impacts of carbon pricing policies
- Examine consumption-driven climate justice issues

### Policy Relevance
- **Carbon Tax Design**: Understanding distributional impacts of consumption-based carbon pricing
- **Climate Justice**: Quantifying consumption emission inequality for equity considerations
- **Mitigation Strategies**: Targeting high-consumption groups for behavioral change initiatives

## Data Quality and Limitations

### Quality Assessment
The authors note that data quality is "low to very low" due to:
- Limited pollution data availability in most countries
- Methodological challenges in attribution across income groups
- Reliance on modeling rather than direct measurement

### Methodological Considerations
- Results are sensitive to different carbon footprint measurement approaches
- Consumption-only measures show lower inequality than when including investment emissions
- Represents the best available global effort despite quality limitations

## Geographic and Temporal Coverage

- **Countries**: Available for 169+ countries globally
- **Time Period**: Generally 1990-2019 with some extrapolation to 2020
- **Update Frequency**: Based on availability of underlying survey, tax, and environmental data

## Technical References

- **Primary Source**: Chancel, L. (2021). "Global Carbon Inequality, 1990-2019". WID Working Paper 2021/22
- **Methodology**: Available at [WID.world carbon documentation](http://wordpress.wid.world/document/global-carbon-inequality-1990-2019-wid-world-working-paper-2021-22/)
- **Aggregate Methods**: Burq and Chancel (2021). "Aggregate carbon footprints on WID.world"

## Research Priority

**HIGH** - This is a core indicator for consumption-based carbon inequality analysis and is essential for understanding how carbon footprints vary across income distributions without the confounding effects of investment-related emissions.