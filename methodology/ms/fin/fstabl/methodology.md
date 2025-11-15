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
Inverted: true
LowerGoalpost: 10
UpperGoalpost: 0
ScoreFunction: >
    Score = goalpost(IMF_FSTABL, 10, 0)
SourceOrganization: IMF
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://data.imf.org/?sk=51b096fa-2cd2-40c2-8d09-0699cc1764da
---


