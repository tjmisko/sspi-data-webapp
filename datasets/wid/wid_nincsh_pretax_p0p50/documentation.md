---
DatasetType: Intermediate
DatasetName: Pre-tax National Income Share of Bottom 50%
DatasetCode: WID_NINCSH_PRETAX_P0P50
Description: Share of total pre-tax national income received by the bottom 50% of earners
Unit: >
    share; percentile p0p50; sptincj992
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wid/wid_nincsh_pretax_p0p50.py
---
# Pre-Tax National Income

## Overview

This dataset from the World Inequality Database (WID) measures **pre-tax national income** across income and wealth distributions. Income or wealth shares. When the associated percentile is of the form 'pX', the raw data stores the share of total income or wealth detained by all the population between threshold pX and the top of the distribution. When the associated percentile is of the form 'pXpY', the raw data stores the share of the population between thresholds pX and pY.

## Variable Details

- **WID Variable Code**: `sptincj992`
- **Measurement Category**: Income Distribution
- **Unit**: share
- **Measurement Type**: Share
- **Population Coverage**: The base unit is the individual (rather than the household) but resources are split equally within couples.. The population is comprised of individuals over age 20.

## Technical Description

Pre-tax national income =Pre-tax labor income [total pre-tax income ranking]+Pre-tax capital income [total pre-tax income ranking]

## Methodology

Methodological details follow WID.world standards for distributional analysis. Specific methodology details not available in metadata.

## Data Sources and References

After 1962, Piketty, Thomas; Saez, Emmanuel and Zucman, Gabriel (2016). Distributional National Accounts: Methods and Estimates for the United States; Before 1962, Fisher-Post, Matthew (2020). Examining the Great Leveling: New Evidence on Midcentury American Inequality; Saez, Emmanuel and Zucman, Gabriel (2020). The Rise of Income and Wealth Inequality in America: Evidence from Distributional Macroeconomic Accounts; Zucman, Gabriel (2020). Technical Note “US Distributional National Accounts: Updates” Blanchet, Thomas, Saez, Emmanuel and Zucman, Gabriel (2022). “Real-Time Inequality" ; Chancel, L., Moshrif, R., Piketty, T., Xuereb, S., (2023), "Historical Inequality Series on WID.world - Updates"

## Population and Demographic Details

### Coverage
- **Population Base**: The base unit is the individual (rather than the household) but resources are split equally within couples.
- **Age Groups**: The population is comprised of individuals over age 20.

### Measurement Approach
- **Type**: Share
- **Description**: Income or wealth shares. When the associated percentile is of the form 'pX', the raw data stores the share of total income or wealth detained by all the population between threshold pX and the top of the distribution. When the associated percentile is of the form 'pXpY', the raw data stores the share of the population between thresholds pX and pY.

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
- **Variable Code**: sptincj992
- **SSPI Integration**: Part of comprehensive inequality measurement framework
- **Documentation**: See WID.world for detailed methodological documentation

## Related Indicators

This indicator is part of WID's comprehensive distributional database and can be analyzed alongside other SSPI inequality measures for holistic understanding of social and economic patterns.