---
ItemType: Indicator
ItemCode: DEFRST
ItemName: Deforestation
Policy: Forest Management
Description: >
  Percentage change in naturally regenerating forests from a 1990’s average to 2018.
Footnote: null
Indicator: Deforestation
IndicatorCode: DEFRST
DatasetCodes:
  - UNFAO_FRSTLV
  - UNFAO_FRSTAV
Inverted: false
LowerGoalpost: -20.0
UpperGoalpost: 40.0
ScoreFunction: >
    Score = goalpost((UNFAO_FRSTLV - UNFAO_FRSTAV) / UNFAO_FRSTAV, -20, 40)
SourceOrganization: UN FAO
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://www.fao.org/faostat/en/#data/RL
---

