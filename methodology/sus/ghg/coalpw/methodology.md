---
ItemType: Indicator
ItemCode: COALPW
DatasetCodes:
  - IEA_TLCOAL
  - IEA_NATGAS
  - IEA_NCLEAR
  - IEA_HYDROP
  - IEA_GEOPWR
  - IEA_BIOWAS
  - IEA_FSLOIL
ItemName: Energy From Coal
Description: Percentage of a country's total energy supply generated from coal and
  coal derived sources, computed as the ratio of coal energy to total energy supply.
Footnote: Computed as IEA_TLCOAL / (IEA_TLCOAL + IEA_NATGAS + IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS + IEA_FSLOIL)
Indicator: Energy From Coal
IndicatorCode: COALPW
Inverted: true
LowerGoalpost: 0.40
Policy: Fossil Fuel and Air Pollution
SourceOrganization: IEA
SourceOrganizationIndicatorCode: TESbySource
SourceOrganizationURL: https://www.iea.org/data-and-statistics/data-tools/energy-statistics-data-browser?country=WORLD&fuel=Energy%20supply&indicator=TESbySource
UpperGoalpost: 0.0
---
The COALPW indicator is computed by taking the ratio of coal energy
(IEA_TLCOAL) to the total energy supply, where total energy supply is the sum
of all constituent energy sources:
  
COALPW = goalpost(IEA_TLCOAL / (IEA_TLCOAL + IEA_NATGAS + IEA_NCLEAR + IEA_HYDROP +
IEA_GEOPWR + IEA_BIOWAS + IEA_FSLOIL), 0, 0.4)
  
This produces a value between 0 and 1 representing the percentage of total
energy supply from coal sources. The score is then calculated using goalpost
transformation with lower goalpost of 0.40 and upper goalpost of 0.0
(inverted indicator).

