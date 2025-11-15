---
ItemType: Indicator
ItemCode: PRISON
ItemName: Incarceration Rates
Policy: Criminal Justice Policy
Description: >
  Prison population rate per 100,000 of the national population. Population
  sourced from the WorldBank.
Footnote: null
Indicator: Incarceration Rates
IndicatorCode: PRISON
DatasetCodes:
  - UNODC_PRIPOP
Inverted: true
LowerGoalpost: 540
UpperGoalpost: 40
ScoreFunction: >
  Score = goalpost(UNODC_PRIPOP, 540, 40)
---

