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
Inverted: false
LowerGoalpost: 80
UpperGoalpost: 100
ScoreFunction: >
    Score = goalpost(WHO_ATBRTH, 80, 100)
SourceOrganization: WHO
SourceOrganizationIndicatorCode: MDG_0000000025
SourceOrganizationURL: https://apps.who.int/gho/data/node.main.SKILLEDBIRTHATTENDANTS?lang=en
---

