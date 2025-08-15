---
DatasetType: Intermediate
DatasetName: Post-tax National Income Averages (Equal-split Adults)
DatasetCode: WID_NINCAV_POSTTAX_EQUALSPLIT_P0P50
Description: Average post-tax national income for the bottom 50% of earners for equal-split adults. Resources are split equally within couples while the base unit remains the individual. Post-tax national income is the sum of primary incomes from all sectors minus taxes, reflecting income distribution after the operation of the tax and transfer system.
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
---
# Post-Tax National Income

## Overview

This dataset from the World Inequality Database (WID) measures **post-tax national income** across income and wealth distributions. Average income or wealth between two percentiles. When the associated percentile is of the form 'pX', intermediary average returns the average between percentile pX and the next consecutive percentile. When the associated percentile is of the form 'pXpY', the variable returns the average between percentiles pX and pY.

## Variable Details

- **WID Variable Code**: `adiincj992`
- **Measurement Category**: Income Distribution
- **Unit**: USD
- **Measurement Type**: Average
- **Population Coverage**: The base unit is the individual (rather than the household) but resources are split equally within couples.. The population is comprised of individuals over age 20.

## Technical Description

[Post-tax national income]=[Post-tax disposable income]+[Public spending]

## Methodology

Methodological details follow WID.world standards for distributional analysis. Specific methodology details not available in metadata.

## Data Sources and References

After 1962, Piketty, Thomas; Saez, Emmanuel and Zucman, Gabriel (2016). Distributional National Accounts: Methods and Estimates for the United States; Before 1962, Fisher-Post, Matthew (2020). Examining the Great Leveling: New Evidence on Midcentury American Inequality; Saez, Emmanuel and Zucman, Gabriel (2020). The Rise of Income and Wealth Inequality in America: Evidence from Distributional Macroeconomic Accounts; Zucman, Gabriel (2020). Technical Note “US Distributional National Accounts: Updates” Blanchet, Thomas, Saez, Emmanuel and Zucman, Gabriel (2022). “Real-Time Inequality"

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
- **Variable Code**: adiincj992
- **SSPI Integration**: Part of comprehensive inequality measurement framework
- **Documentation**: See WID.world for detailed methodological documentation

## Related Indicators

This indicator is part of WID's comprehensive distributional database and can be analyzed alongside other SSPI inequality measures for holistic understanding of social and economic patterns.