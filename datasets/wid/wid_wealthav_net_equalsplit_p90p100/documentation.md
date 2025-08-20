---
DatasetType: Intermediate
DatasetName: Net Personal Wealth Averages (Equal - Top 10%
DatasetCode: WID_WEALTHAV_NET_EQUALSPLIT_P90P100
Description: Average net personal wealth for the top 10% of earners for equal-split adults. Resources are split equally within couples while the base unit remains the individual. Net personal wealth is the total value of non-financial and financial assets (housing, land, deposits, bonds, equities, etc.) held by households, minus their debts.
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
---
# Net Personal Wealth

## Overview

This dataset from the World Inequality Database (WID) measures **net personal wealth** across income and wealth distributions. Average income or wealth between two percentiles. When the associated percentile is of the form 'pX', intermediary average returns the average between percentile pX and the next consecutive percentile. When the associated percentile is of the form 'pXpY', the variable returns the average between percentiles pX and pY.

## Variable Details

- **WID Variable Code**: `ahwealj992`
- **Measurement Category**: Wealth Distribution
- **Unit**: USD
- **Measurement Type**: Average
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
- **Type**: Average
- **Description**: Average income or wealth between two percentiles. When the associated percentile is of the form 'pX', intermediary average returns the average between percentile pX and the next consecutive percentile. When the associated percentile is of the form 'pXpY', the variable returns the average between percentiles pX and pY.

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
- **Variable Code**: ahwealj992
- **SSPI Integration**: Part of comprehensive inequality measurement framework
- **Documentation**: See WID.world for detailed methodological documentation

## Related Indicators

This indicator is part of WID's comprehensive distributional database and can be analyzed alongside other SSPI inequality measures for holistic understanding of social and economic patterns.