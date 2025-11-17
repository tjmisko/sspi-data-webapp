---
ItemType: Indicator
ItemCode: SENIOR
ItemName: Senior Wellbeing
Policy: Senior Welfare Programs
DatasetCodes:
  - OECD_POVNRT
  - OECD_YRSRTM
  - OECD_YRSRTW
Description: >
  Weighted average of three measures: 1) Years in retirement for males (25%),
  2) Years in retirement for females (25%), and 3) Old age income poverty (50%).
  Years in retirement calculated as life expectancy minus current retirement age.
Footnote: null
Indicator: Senior Wellbeing
IndicatorCode: SENIOR
LowerGoalpost: null
UpperGoalpost: null
ScoreFunction: >
  Score = average(
      average(
          goalpost(SENLEM - SENCRM, 0, 15),
          goalpost(SENLEF - SENCRF, 0, 20)
      ),
      goalpost(SENPVT, 0, 50)
  )
---

