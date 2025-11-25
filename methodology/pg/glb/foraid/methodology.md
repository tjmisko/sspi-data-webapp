---
ItemType: Indicator
ItemCode: FORAID
ItemName: Foreign Aid
Policy: Quality and Quantity of Foreign Aid
Description: >
  Countries grouped as "Donors" or "Recipients" based on their reported
  status in the OECD CRS database. Good foreign aid excludes investments in fossil
  fuel extraction and energy systems, livestock, and military aid.
  1) Donors: Total Good Foreign Aid as a Percentage of GDP
  2) Recipients: Total Good Foreign Aid per Capita reflects the extent to which recipient countries solicit foreign
  aid for their population.
Footnote: null
Indicator: Foreign Aid
IndicatorCode: FORAID
DatasetCodes:
  - OECD_TOTDON
  - OECD_TONREC
  - WB_POPULN
  - WB_GDPMKT
LowerGoalpost: null
UpperGoalpost: null
ScoreFunction: >
    Score = max(
        goalpost(TOTDON * pow(10, 8) / GDPMKT, 0, 1),
        goalpost(TOTREC * pow(10, 6) / POPULN, 0, 500)
    )
---

