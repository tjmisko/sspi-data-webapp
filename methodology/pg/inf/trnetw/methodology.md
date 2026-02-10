---
ItemType: Indicator
ItemCode: TRNETW
ItemName: National Transport Network Intensity
Policy: Transport Infrastructure
Description: >
  The average of two measures: the natural log of rail lines per square
  kilometer (millions) per capita (millions) and the natural log of roadways per square
  kilometer per capita.
Footnote: null
Indicator: National Transport Network Intensity
IndicatorCode: TRNETW
DatasetCodes:
  - WB_RAILNT
  - CIA_ROADNT
LowerGoalpost: null
UpperGoalpost: null
ScoreFunction: >
  Score = average(goalpost(WB_RAILNT, 0, 100), goalpost(CIA_ROADNT, 0, 100))
---

