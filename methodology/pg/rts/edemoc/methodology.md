---
ItemType: Indicator
ItemCode: EDEMOC
DatasetCodes:
  - VDEM_EDEMOC
ItemName: Electoral Democracy Index
Policy: Political Participation and Influence
Description: >
  Electoral Democracy Index seeks to embody the core values that make rulers
  responsive to citizens through elections and freedom of expression.
Footnote: >
  To view the Electoral Democracy Index data, download the V-Dem data set
  and view the column "v2x_polyarchy".
  Years after a country's last V-Dem observation, up to 2023, are
  carried forward from that observation and stored as imputed rows
  (ImputationMethod "Forward Extrapolation", ImputationDistance = years
  since the last observation, no distance cap); observed V-Dem years are
  never overwritten.
Indicator: Electoral Democracy Index
IndicatorCode: EDEMOC
LowerGoalpost: 0
UpperGoalpost: 1
ScoreFunction: >
  Score = goalpost(VDEM_EDEMOC, 0, 1)
---

