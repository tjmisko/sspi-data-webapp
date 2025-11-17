---
ItemType: Indicator
ItemCode: AQELEC
ItemName: Availability and Quality of Electricity
Policy: Electrification
Description: >
  Arithmetic mean of two measures:
  1) The percentage of the population with access to electricity
  2) Executive opinion survey responses to the question: "In your country, how would you assess the reliability of the electricity supply?"
Footnote: null
Indicator: Availability and Quality of Electricity
IndicatorCode: AQELEC
DatasetCodes:
  - WB_AVELEC
  - WEF_QUELEC
LowerGoalpost: null
UpperGoalpost: null
ScoreFunction: >
  Score = average(
      goalpost(WB_AVELEC, 0, 100),
      goalpost(WEF_QUELEC, 1, 7)
  )
---

