---
DatasetType: Intermediate
DatasetName: Personal Carbon Footprint - Total (Full Distribution)
DatasetCode: WID_CARBON_TOT_P0P100
Description: Average per capita total carbon emissions across full income distribution. Combines both consumption and investment-related emissions for comprehensive personal carbon footprint. Provides complete assessment of carbon inequality across all income percentiles.
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wid/wid_carbon_tot_p0p100.py
---

# Personal Carbon Footprint - Total (Full Distribution)

## Overview

This dataset provides the most comprehensive carbon inequality data from the World Inequality Database (WID), measuring total personal carbon footprints that combine both consumption and investment activities across the complete income distribution. This represents the flagship indicator for studying complete personal carbon responsibility and inequality.

## Variable Details

- **WID Variable Code**: `lpfghgi999`
- **Unit**: tonnes CO2 equivalent per capita (tCO2 equivalent/cap)
- **Scope**: Greenhouse gas emissions (CO2 + other greenhouse gases)
- **Coverage**: Full income distribution (p0p100)
- **Population**: All ages (999)

## Methodology

The estimates are based on modeled calculations that systematically combine:

- Survey and tax data
- National accounts
- Environmental Input-Output tables

The methodology includes emissions embedded in imports and exports of goods and services, providing a comprehensive accounting approach that captures the full carbon footprint from both consumption patterns and capital ownership across income percentiles.

## Emissions Scope

This indicator comprehensively measures emissions associated with:

- **Individual consumption**: Personal spending on goods and services
- **Government collective expenditures**: Public services and infrastructure
- **Individual investments**: Capital formation attributed to individual firm owners
- **Business ownership**: Emissions from productive assets owned by individuals

**Complete Coverage**: This indicator provides the most comprehensive measure of personal carbon responsibility by including both lifestyle and wealth-driven emissions.

## Research Applications

### Comprehensive Carbon Inequality Analysis
- Study total personal carbon footprints across income distributions
- Analyze complete distributional impacts of climate policies
- Examine holistic climate justice and responsibility patterns
- Understand the full spectrum of carbon inequality drivers

### Policy Relevance
- **Comprehensive Carbon Pricing**: Understanding total distributional impacts of economy-wide carbon policies
- **Climate Justice**: Complete assessment of carbon responsibility across income groups
- **Holistic Mitigation Strategies**: Targeting both consumption and investment behaviors
- **Progressive Climate Policy**: Designing policies that account for total carbon footprint inequality

## Consumption vs Investment Components

This total measure is crucial because it reveals that carbon inequality is significantly higher when including investment emissions alongside consumption. Key insights:

- **Consumption-only measures**: Show lower levels of carbon inequality
- **Investment component**: Substantially increases measured inequality
- **Total measure**: Provides complete picture of carbon responsibility
- **Policy implications**: Different interventions needed for consumption vs investment emissions

## Data Quality and Limitations

### Quality Assessment
The authors note that data quality is "low to very low" due to:
- Limited pollution data availability in most countries
- Complex attribution challenges for both consumption and investment emissions
- Methodological difficulties in comprehensive carbon footprint measurement

### Methodological Considerations
- Represents the most ambitious attempt at comprehensive carbon inequality measurement
- Results show highest inequality levels when both components are included
- Methodological sensitivity requires careful interpretation of results
- Pioneering approach despite acknowledged limitations

## Comparative Analysis

This dataset enables comparison of:
- **Total vs consumption-only footprints**: Understanding investment contribution to inequality
- **Cross-country inequality patterns**: Standardized methodology across 169+ countries
- **Temporal trends**: Changes in comprehensive carbon inequality over time
- **Policy scenario modeling**: Impact assessment for different intervention approaches

## Geographic and Temporal Coverage

- **Countries**: Available for 169+ countries globally
- **Time Period**: Generally 1990-2019 with some extrapolation to 2020
- **Update Frequency**: Based on availability of underlying survey, tax, and environmental data

## Technical References

- **Primary Source**: Chancel, L. (2021). "Global Carbon Inequality, 1990-2019". WID Working Paper 2021/22
- **Methodology**: Available at [WID.world carbon documentation](http://wordpress.wid.world/document/global-carbon-inequality-1990-2019-wid-world-working-paper-2021-22/)
- **Aggregate Methods**: Burq and Chancel (2021). "Aggregate carbon footprints on WID.world"

## Research Priority

**HIGH** - This is the flagship indicator for comprehensive carbon inequality analysis, providing the most complete measure of personal carbon responsibility by combining both consumption and investment-based emissions. Essential for holistic climate policy analysis and climate justice research.