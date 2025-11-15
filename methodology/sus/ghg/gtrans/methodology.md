---
ItemType: Indicator
ItemCode: GTRANS
ItemName: Green Transport Index
Policy: CO2 Emissions from Transportation
Description: CO2 emissions from transport in tonnes per inhabitant, tonnes referring
  to thousands of kilograms. This includes domestic aviation, domestic navigation,
  road, rail and pipeline transport.
Footnote: null
Indicator: Green Transport Index
IndicatorCode: GTRANS
DatasetCodes:
  - IEA_TCO2EM
  - WB_POPULN
Inverted: true
LowerGoalpost: 7000
UpperGoalpost: 0
ScoreFunction: >
    Score = goalpost(IEA_TCO2EM / WB_POPULN, 7000, 0)
SourceOrganization: IEA
SourceOrganizationIndicatorCode: CO2BySector
SourceOrganizationURL: https://www.iea.org/data-and-statistics/data-tools/energy-statistics-data-browser?country=CANADA&fuel=CO2%20emissions&indicator=CO2BySector
---

