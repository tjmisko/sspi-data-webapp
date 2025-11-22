---
ItemType: Indicator
ItemCode: ISHRAT
ItemName: Income Share Ratio
Policy: Income Inequality and Redistribution
Description: The pre-tax national income share of the bottom 50% of households divided
  by the pre-tax national income share of the top 10% of households.
Footnote: null
Indicator: Income Share Ratio
IndicatorCode: ISHRAT
DatasetCodes:
  - WID_NINCSH_PRETAX_P90P100
  - WID_NINCSH_PRETAX_P0P50
LowerGoalpost: 0.2
UpperGoalpost: 1.25
ScoreFunction: >
    Score = goalpost(WID_NINCSH_PRETAX_P0P50 / WID_NINCSH_PRETAX_P90P100, 0.2, 1.25)
---

