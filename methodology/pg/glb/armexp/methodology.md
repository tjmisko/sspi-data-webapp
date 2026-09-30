---
ItemType: Indicator
ItemCode: ARMEXP
DatasetCodes:
  - SIPRI_ARMEXP
ItemName: Arms Transfers
Policy: Arms Policy
Description: >
  Arm transfers: the supply of military weapons through sales, aid, gifts,
  and those made through manufacturing licenses.
Footnote: >
  Source: SIPRI Arms Transfers Database, exporter table of delivered major
  arms in millions of SIPRI trend-indicator values (TIV). SIPRI prints "0"
  for deliveries below 0.5 million TIV and leaves a cell empty when no
  delivery was identified. Per owner ruling (2026-09-13) an empty cell, and
  every reported year for an SSPI country absent from the exporter table
  (Bangladesh and Iraq in the 2025 download), is recorded as an observed
  0 TIV value with the note "No recorded transfers (0 TIV)"; these rows are
  observations, not imputations. SIPRI's non-ISO label "UAE" is mapped to
  ARE (likewise Brunei to BRN and Bosnia-Herzegovina to BIH). Only years
  SIPRI has published (a non-empty world total) are recorded. No world-mean
  or reference-class fill and no carry across gaps is applied; a year is
  extrapolated only if the SIPRI table ends before 2023 or starts after
  2000, and such rows are flagged Imputed with their ImputationDistance.
Indicator: Arms Transfers
IndicatorCode: ARMEXP
LowerGoalpost: 500
UpperGoalpost: 0
ScoreFunction: >
  Score = goalpost(SIPRI_ARMEXP, 500, 0)
---

