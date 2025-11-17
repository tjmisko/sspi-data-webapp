---
ItemType: Indicator
ItemCode: ATBRTH
ItemName: Attended Births by Skilled Personnel
Policy: Basic Healthcare
Description: The proportion of births attended by trained and/or skilled health personnel.
Footnote: null
Indicator: Attended Births by Skilled Personnel
IndicatorCode: ATBRTH
DatasetCodes:
  - WHO_ATBRTH
LowerGoalpost: 80
UpperGoalpost: 100
ScoreFunction: >
    Score = goalpost(WHO_ATBRTH, 80, 100)
---

