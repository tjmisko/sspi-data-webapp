---
ItemType: Indicator
ItemCode: CRPTAX
ItemName: Corporate Tax Rate
Policy: Corporate Tax
DatasetCodes:
  - TF_CRPTAX
Description: Tax imposed on the net income of the company.
Footnote: null
Indicator: Corporate Tax Rate
IndicatorCode: CRPTAX
LowerGoalpost: 0
UpperGoalpost: 40
ScoreFunction: >
    Score = goalpost(TF_CRPTAX, 0, 40)
---

