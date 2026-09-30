---
ItemType: Indicator
ItemCode: BEEFMK
ItemName: Beef Market
Policy: Methane Emissions
Description: >
  The average of two measures: beef and buffalo meat produced in kilograms
  per person per year, and beef and buffalo meat consumed in kilograms per
  person per year. FAO production is reported in thousands of tonnes and is
  converted to kilograms (1000 t = 1,000,000 kg) before dividing by World Bank
  population. Both measures score 0 at 50 kg per person per year or more and
  1 at 0 kg.
Footnote: null
Indicator: Beef Market
IndicatorCode: BEEFMK
DatasetCodes:
  - UNFAO_BFPROD
  - UNFAO_BFCONS
  - WB_POPULN
LowerGoalpost: 50
UpperGoalpost: 0
ScoreFunction: >
    Score = average(
        goalpost(UNFAO_BFPROD * 1000000 / WB_POPULN, 50, 0),
        goalpost(UNFAO_BFCONS, 50, 0)
    )
---

