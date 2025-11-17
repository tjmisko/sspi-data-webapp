---
ItemType: Indicator
ItemCode: REDLST
DatasetCodes:
  - UNSDG_REDLST
ItemName: IUCN Red List Index
Description: Measures the level of extinction risk across species within a country.
  Index values of 1 represent all species qualifying as having an extinction risk
  of "least concern," while values of 0 represent all species having gone extinct.
Footnote: null
Indicator: IUCN Red List Index
LowerGoalpost: 0
UpperGoalpost: 1
ScoreFunction: >
    Score = goalpost(UNSDG_REDLST, 0, 1)
IndicatorCode: REDLST
Policy: Endangered Species Protection
---

