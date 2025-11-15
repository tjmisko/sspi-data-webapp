---
ItemType: Indicator
ItemCode: ALTNRG
ItemName: Alternative Energy Generation
Policy: Renewable Energy Incentives
Description: >
  Total energy supply (excluding exports) from "renewable sources" (nuclear,
  hydroelectric, geothermal, solar, wind, and biofuels) minus half of total
  final energy supply from biofuel sources to penalize countries for
  unsustainable overreliance on biofuels.
LowerGoalpost: 0
UpperGoalpost: 60
ScoreFunction: >
    Score = goalpost(((IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS) - 0.5 * IEA_BIOWAS) / (IEA_TLCOAL + IEA_NATGAS + IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS + IEA_FSLOIL) * 100, 0, 60)
Footnote: null
Indicator: Alternative Energy Generation
IndicatorCode: ALTNRG
DatasetCodes:
  - IEA_TLCOAL
  - IEA_NATGAS
  - IEA_NCLEAR
  - IEA_HYDROP
  - IEA_GEOPWR
  - IEA_BIOWAS
  - IEA_FSLOIL
Inverted: false
SourceOrganization: IEA
SourceOrganizationIndicatorCode: TESbySource
SourceOrganizationURL: https://www.iea.org/
---

