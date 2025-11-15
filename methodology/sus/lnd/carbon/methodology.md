---
ItemType: Indicator
ItemCode: CARBON
ItemName: Natural Carbon Capture
Policy: Carbon Sequestration in Forests
Description: >
  Percentage change in the ratio of carbon stock in living biomass over
  forestland from a 1990’s average to 2018.
Footnote: null
Indicator: Natural Carbon Capture
IndicatorCode: CARBON
DatasetCodes:
  - UNFAO_CRBNLV
  - UNFAO_CRBNAV
LowerGoalpost: -5
UpperGoalpost: 50
ScoreFunction: >
    Score = goalpost((UNFAO_CRBNLV - UNFAO_CRBNAV) / UNFAO_CRBNAV * 100, -5, 50)
SourceOrganization: UN FAO
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://www.fao.org/faostat/en/#data/RL
---

