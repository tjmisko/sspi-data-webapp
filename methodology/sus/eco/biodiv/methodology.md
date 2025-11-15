---
ItemType: Indicator
ItemCode: BIODIV
ItemName: Biodiversity Protection
Description: > 
  Arithmetic average of three measures: the percentage of important sites for
  terrestrial, freshwater, and marine biodiversity that are covered by
  protected areas, by ecosystem type.
Footnote: null
Indicator: Biodiversity Protection
IndicatorCode: BIODIV
DatasetCodes:
  - UNSDG_MARINE
  - UNSDG_TERRST
  - UNSDG_FRSHWT
ScoreFunction: >
    Score = average(
        goalpost(UNSDG_MARINE, 0, 100),
        goalpost(UNSDG_TERRST, 0, 100),
        goalpost(UNSDG_FRSHWT, 0, 100)
    )
Inverted: false
LowerGoalpost: null
Policy: "Protection of Biodiversity"
SourceOrganization: UN SDG
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://unstats.un.org/sdgapi/swagger/
UpperGoalpost: null
---

