---
ItemType: Indicator
ItemCode: SANSRV
DatasetCodes:
  - WB_SANSRV
ItemName: Basic Sanitation Services
Policy: Sanitation Infrastructure
Description: >
  The percentage of people using at least basic sanitation services, that
  is, improved sanitation facilities that are not shared with other households.
Footnote: null
Indicator: Basic Sanitation Services
IndicatorCode: SANSRV
LowerGoalpost: 50
UpperGoalpost: 100
ScoreFunction: >
  Score = goalpost(WB_SANSRV, 50, 100)
---

Imputations for Safely Managed Water:

Credible sources found:
https://sdg6data.org/en/indicator/6.1.1
https://washdata.org/data

Note: the sdg data relies on some datasets from Unicef Wash’s JMP datasets 

Methodology for imputation: 

As JMP dataset is the source for the sdg dataset, the JMP dataset is the primary source. Imputations used are fo the most recent year.
If the JMP datasets do not have available data, the next most credible sources to go to would be specific national level datasets or global level datasets(like the sdg). 
If Safely Managed data was available, that was entered. If not, there was only basic data available and that was used.

Documentation:
Each imputed DRKWAT value for each country will have
A source dataset mentioned(JMP/national/etc.)
Year (range if applicable) of estimate
Whether the figure is “safely managed” or “basic”

Definitions:
Safely Managed: 
- Improved: the water comes from a protected source (i.e. piped, public taps, protected wells, etc.)
- Accessibility: The Water is accessible within homes
- Available when needed: Water is available at any given time
- Contamination free: the water is free of e. Coli and priority chemicals like arsenic and/or fluoride when consumed

Basic: 
Improved source: same definition as above
Accessibility: Accessible within 30 minutes, including waiting if necessary.

*Note: All SDG below are technically also JMP data, as the data for SDG is derived from JMP


Interpolation of Safely Managed using Basic:
- As safely managed water is a subset of Basic water, a method we can use is the ratio of safely managed to basic water with countries depending on their level of income. This gets us a range of values, or we can choose a specific r, (median/mean) prior for our interpolation. We have these ratios from the 2022 JMP data.

Region ratios:
Typical range High-income (OECD, Gulf states): 

Median range 0.98 – 1.00 
Total range: 0.95–1.00

Upper-middle income (e.g. China, Thailand) 

Median Range: 0.90 – 0.98 
Total Range: 0.85–1.00

Lower-middle income (e.g. India, Kenya)

Median Range: 0.70 – 0.90 
Total Range: 0.60–0.95

Low income (Sub-Saharan Africa, rural areas)
 
Median Range: 0.50 – 0.80 
Total Range: 0.30–0.90



Interpolated values for countries without Safely Managed:

For consistency, I will use the median of the median ranges for each corresponding group. Using the median of median range to avoid dealing with skew for values as much as possible.


