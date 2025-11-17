---
ItemType: Indicator
ItemCode: TXRDST
ItemName: Tax Redistribution
Policy: Tax Redistribution
Description: >
  Tax Redistribution measures the percentage change in the income share ratio
  (a measure of the inequality of the income distribution) induced by the tax
  code.
LowerGoalpost: -10
UpperGoalpost: 100
ScoreFunction: >
    Score = goalpost((WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50 / WID_NINCSH_POSTTAX_EQUALSPLIT_P90P100 -  WID_NINCSH_PRETAX_P0P50 / WID_NINCSH_PRETAX_P90P100 ) / ( WID_NINCSH_PRETAX_P0P50 / WID_NINCSH_PRETAX_P90P100 ) * 100, -10, -100)
Footnote: null
Indicator: Tax Redistribution
IndicatorCode: TXRDST
DatasetCodes:
  - WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50
  - WID_NINCSH_POSTTAX_EQUALSPLIT_P90P100
  - WID_NINCSH_PRETAX_P0P50
  - WID_NINCSH_PRETAX_P90P100
---

