---
DatasetType: Intermediate
DatasetName: Net Personal Wealth Gender Breakdown - Top 10%
DatasetCode: WID_WEALTHBRK_NET_GENDER_P90P100
Description: Gender breakdown coefficients for net personal wealth distribution. Uses beta coefficients (inverted Pareto-Lorenz coefficient) to analyze gender differences in wealth distribution. Net personal wealth is the total value of non-financial and financial assets (housing, land, deposits, bonds, equities, etc.) held by households, minus their debts. Shows how wealth distribution varies by gender.
Unit: >
    nan; percentile p90p100; bhwealj992
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wid/wid_wealthbrk_net_gender_p90p100.py
---
# Net Personal Wealth

## Overview

This dataset from the World Inequality Database (WID) measures **net personal wealth** across income and wealth distributions. The beta coefficient corresponds to the inverted Pareto-Lorenz coefficient. It is equal to mean income over a certain income level divided by this level. A coefficient b=2=200% for an income level 100 000 EUR means that the average income above 100 000 EUR is 200 000 EUR, a coefficient of 3 or 300% at income level 1 000 000 EUR means that the average income level above 1 000 000 EUR in a given population is 3 000 000 EUR.

## Variable Details

- **WID Variable Code**: `bhwealj992`
- **Measurement Category**: Wealth Distribution
- **Unit**: Not specified
- **Measurement Type**: Beta coefficient
- **Population Coverage**: The base unit is the individual (rather than the household) but resources are split equally within couples.. The population is comprised of individuals over age 20.

## Technical Description

[Net personal wealth]=[Personal non-financial assets]+[Personal financial assets]-[Personal debt]

## Methodology

Methodological details follow WID.world standards for distributional analysis. Specific methodology details not available in metadata.

## Data Sources and References

Saez, E., Zucman, G. (2020), The Rise of Income and Wealth Inequality in America: Evidence from Distributional Macroeconomic Accounts;

## Population and Demographic Details

### Coverage
- **Population Base**: The base unit is the individual (rather than the household) but resources are split equally within couples.
- **Age Groups**: The population is comprised of individuals over age 20.

### Measurement Approach
- **Type**: Beta coefficient
- **Description**: The beta coefficient corresponds to the inverted Pareto-Lorenz coefficient. It is equal to mean income over a certain income level divided by this level. A coefficient b=2=200% for an income level 100 000 EUR means that the average income above 100 000 EUR is 200 000 EUR, a coefficient of 3 or 300% at income level 1 000 000 EUR means that the average income level above 1 000 000 EUR in a given population is 3 000 000 EUR.

## Usage in SSPI Context

This WID indicator contributes to the SSPI's comprehensive analysis of social and economic inequality patterns. The distributional nature of this data enables:

- Cross-country inequality comparisons
- Temporal analysis of distribution changes
- Policy impact assessment across income/wealth percentiles
- Integration with other SSPI indicators for multi-dimensional analysis

## Data Quality and Limitations

### Methodology Notes
- Data follows WID.world collection and estimation standards
- Quality varies by country based on available source data
- Distributional estimates may involve modeling and imputation
- Users should consult WID documentation for country-specific notes

### Temporal Coverage
- Coverage varies by country and indicator
- Generally focuses on post-2000 period for SSPI integration
- Some historical data available depending on source availability

## Technical References

- **Primary Source**: World Inequality Database (WID.world)
- **Variable Code**: bhwealj992
- **SSPI Integration**: Part of comprehensive inequality measurement framework
- **Documentation**: See WID.world for detailed methodological documentation

## Related Indicators

This indicator is part of WID's comprehensive distributional database and can be analyzed alongside other SSPI inequality measures for holistic understanding of social and economic patterns.