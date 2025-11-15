---
ItemType: Indicator
ItemCode: BEEFMK
ItemName: Beef Market
Policy: Methane Emissions
Description: >
  The average of two measures: beef and buffalo meat produced in kilograms
  per person, and per capita meat (beef) consumption. UN population estimates
  were used.
Footnote: null
Indicator: Beef Market
IndicatorCode: BEEFMK
DatasetCodes:
  - UNFAO_BFPROD
  - UNFAO_BFCONS
  - WB_POPULN
Inverted: true
LowerGoalpost: 50
UpperGoalpost: 0
ScoreFunction: >
    Score = average(
        goalpost(UNFAO_BFPROD / WB_POPULN, 50, 0),
        goalpost(UNFAO_BFCONS, 50, 0)
    )
SourceOrganization: UN FAO
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://www.fao.org/faostat/en/#home
---

