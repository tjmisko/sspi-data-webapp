---
ItemType: Indicator
ItemCode: FSTABL
ItemName: Stability
Policy: Regulation of Nonperforming Loans
Description: The percentage of loans that are nonperforming, meaning that the borrower
  is default due to not making the scheduled periods.
Footnote: null
Indicator: Stability
IndicatorCode: FSTABL
DatasetCodes:
  - IMF_FSTABL
LowerGoalpost: 10
UpperGoalpost: 0
ScoreFunction: >
    Score = goalpost(IMF_FSTABL, 10, 0)
---


