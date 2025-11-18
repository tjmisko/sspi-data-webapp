---
ItemType: Indicator
ItemCode: INTRNT
ItemName: Internet Access and Quality
Policy: Connectivity Policy
Description: >
  Arithmetic mean of two measures:
  1) Percentage of households with internet access
  2) Fixed broadband download speed in Mbps.
Footnote: null
Indicator: Internet Access and Quality
IndicatorCode: INTRNT
DatasetCodes:
  - UNSDG_AVINTR
  - CABLE_QUINTR
LowerGoalpost: null
UpperGoalpost: null
ScoreFunction: >
    Score = average(
        goalpost(UNSDG_INTRNT, 0, 100),
        goalpost(WB_INTRNT, 0, 100)
    )
---

