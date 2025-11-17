---
ItemType: Indicator
ItemCode: MSWGEN
ItemName: Municipal Solid Waste Generation
Policy: Wasteful Consumption
Description: >
  Annual amount of per capita Municipal Solid Waste (kg/capita/year), which
  is defined as residential, commercial, and institutional waste (Industrial,
  medical, hazardous, electronic, and construction and demolition waste are
  not included).
Footnote: null
Indicator: Municipal Solid Waste Generation
IndicatorCode: MSWGEN
DatasetCodes:
  - EPI_MSWGEN
LowerGoalpost: 100
UpperGoalpost: 0
ScoreFunction: >
  Score = goalpost(EPI_MSWGEN, 100, 0)
---
Current goalposts are set to take in index data from EPI. TODO: Pull Raw EPI Data for Indicators to Get Actual Values.
