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
        goalpost(OECD_TOTDON * pow(10, 8) / WB_GDPMKT, 0, 1),
        goalpost(OECD_TONREC * pow(10, 6) / WB_POPULN, 0, 500)
    )
ScoreFunctionDescription: >
  Countries are scored as donors or recipients, not both. If total donations
  exceed total receipts (OECD_TOTDON > OECD_TONREC) the score is
  goalpost(OECD_TOTDON * 10^8 / WB_GDPMKT, 0, 1), otherwise it is
  goalpost(OECD_TONREC * 10^6 / WB_POPULN, 0, 500). The runnable ScoreFunction
  takes the larger of the two goalposted terms because the DSL has no
  conditional.
---

