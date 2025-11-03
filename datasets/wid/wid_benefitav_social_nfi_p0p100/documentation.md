---
DatasetType: Intermediate
DatasetName: Social Benefits Averages (NFI) - Full Population
DatasetCode: WID_BENEFITAV_SOCIAL_NFI_P0P100
Description: Average social benefits other than social transfers in kind across all population percentiles for NFI (Net Factor Income) groups. Social benefits represent government transfers to individuals and households, excluding in-kind transfers. Shows the average benefit distribution patterns across net factor income groups.
Source:
  OrganizationCode: WID
  QueryCode: wid_all_data
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wid/wid_benefitav_social_nfi_p0p100.py
---
# Social Benefits From Private Employer Social Insurance

## Overview

This dataset from the World Inequality Database (WID) measures **social benefits from private employer social insurance** across income and wealth distributions. Average income or wealth between two percentiles. When the associated percentile is of the form 'pX', intermediary average returns the average between percentile pX and the next consecutive percentile. When the associated percentile is of the form 'pXpY', the variable returns the average between percentiles pX and pY.

## Variable Details

- **WID Variable Code**: `assbnfi992`
- **Measurement Category**: Social Benefits / Transfers
- **Unit**: USD
- **Measurement Type**: Average
- **Population Coverage**: The base unit is the individual (rather than the household). This is equivalent to assuming no sharing of resources within couples.. The population is comprised of individuals over age 20.

## Technical Description

Average income or wealth between two percentiles. When the associated percentile is of the form 'pX', intermediary average returns the average between percentile pX and the next consecutive percentile. When the associated percentile is of the form 'pXpY', the variable returns the average between percentiles pX and pY.

## Methodology

WID.world estimations as a proportion of GDP based on the following; 1970–2018: OECD. These estimates are then anchored to GDP (see GDP variable for details). The estimates of national accounts subcomponents in the WID are based on official country data and use the methodology presented in the DINA guidelines. We stress that these subcomponents estimates are more fragile than those of main aggregates such as national income. Countries may use classifications used are not always fully consistent with other countries or over time. Series breaks with no real economic significance can appear as a result. The WID include these estimates to provide a centralized source for this official data, so that it can be exploited more directly. We encourage users of this data to be careful and to pay attention to the source of the data, which we systematically indicate.

## Data Sources and References

See DINA guidelines for methodological explanations. The sources used are: OECD.

## Population and Demographic Details

### Coverage
- **Population Base**: The base unit is the individual (rather than the household). This is equivalent to assuming no sharing of resources within couples.
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
- **Variable Code**: assbnfi992
- **SSPI Integration**: Part of comprehensive inequality measurement framework
- **Documentation**: See WID.world for detailed methodological documentation

## Related Indicators

This indicator is part of WID's comprehensive distributional database and can be analyzed alongside other SSPI inequality measures for holistic understanding of social and economic patterns.