---
ItemType: Indicator
ItemCode: GINIPT
ItemName: Gini-coefficient After Taxes
Policy: Income Inequality and Redistribution
Description: GINI Coefficient for post-tax-and-transfer income distribution.
Footnote: null
Indicator: Gini-coefficient After Taxes
IndicatorCode: GINIPT
DatasetCodes:
  - WB_GINIPT
LowerGoalpost: 70
UpperGoalpost: 20
ScoreFunction: >
    Score = goalpost(WB_GINIPT, 70, 20)
---

