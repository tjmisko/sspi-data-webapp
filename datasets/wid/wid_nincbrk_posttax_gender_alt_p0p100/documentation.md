---
DatasetType: Intermediate
DatasetName: Post - Full Population
DatasetCode: WID_NINCBRK_POSTTAX_GENDER_ALT_P0P100
Description: Alternative gender breakdown coefficients for post-tax national income distribution. Uses beta coefficients (inverted Pareto-Lorenz coefficient) to analyze gender differences in post-tax income distribution using an alternative methodology. Post-tax national income is the sum of primary incomes from all sectors minus taxes, reflecting income distribution after the operation of the tax and transfer system.
Unit: >
    nan; percentile p0p100; gdiincj992
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wid/wid_nincbrk_posttax_gender_alt_p0p100.py
---
# Post-Tax National Income

## Overview

This dataset from the World Inequality Database (WID) measures **post-tax national income** across income and wealth distributions. The Gini coefficient is a measure of statistical dispersion. A coefficient of zero expresses perfect equality between individuals. A coefficient of one expresses maximal inequality, where only one person owns all the income or wealth of the economy.

## Variable Details

- **WID Variable Code**: `gdiincj992`
- **Measurement Category**: Income Distribution
- **Unit**: Not specified
- **Measurement Type**: Gini coefficient
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
- **Type**: Gini coefficient
- **Description**: The Gini coefficient is a measure of statistical dispersion. A coefficient of zero expresses perfect equality between individuals. A coefficient of one expresses maximal inequality, where only one person owns all the income or wealth of the economy.

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
- **Variable Code**: gdiincj992
- **SSPI Integration**: Part of comprehensive inequality measurement framework
- **Documentation**: See WID.world for detailed methodological documentation

## Related Indicators

This indicator is part of WID's comprehensive distributional database and can be analyzed alongside other SSPI inequality measures for holistic understanding of social and economic patterns.