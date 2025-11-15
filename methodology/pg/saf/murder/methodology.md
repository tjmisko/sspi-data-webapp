---
ItemType: Indicator
ItemCode: MURDER
DatasetCodes:
  - WB_MURDER
ItemName: Intentional Homicide
Policy: Gun control. Police Enforcement
Description: Intentional homicides per 100,000 people.
Footnote: null
Indicator: Intentional Homicide
IndicatorCode: MURDER
Inverted: true
LowerGoalpost: 20
UpperGoalpost: 0
ScoreFunction: >
    Score = goalpost(WB_MURDER, 20, 0)
SourceOrganizationURL: https://databank.worldbank.org/
---

