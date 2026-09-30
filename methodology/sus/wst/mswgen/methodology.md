---
ItemType: Indicator
ItemCode: MSWGEN
ItemName: Municipal Solid Waste Generation
Policy: Wasteful Consumption
Description: >
  Environmental Performance Index (EPI) indicator score for municipal solid
  waste generated per capita, on a 0 to 100 scale where higher scores mean
  less waste generated per person. Municipal solid waste is defined as
  residential, commercial, and institutional waste (Industrial, medical,
  hazardous, electronic, and construction and demolition waste are not
  included).
Footnote: null
Indicator: Municipal Solid Waste Generation
IndicatorCode: MSWGEN
DatasetCodes:
  - EPI_MSWGEN
LowerGoalpost: 0
UpperGoalpost: 100
ScoreFunction: >
  Score = goalpost(EPI_MSWGEN, 0, 100)
---
Current goalposts are set to take in index data from EPI: EPI_MSWGEN is the EPI
indicator score (0 to 100, higher is better), not kilograms of waste per capita,
so the goalposts run from 0 to 100. TODO: Pull Raw EPI Data for Indicators to Get Actual Values.
