---
ItemType: Indicator
ItemCode: RULELW
DatasetCodes:
  - VDEM_RULELW
ItemName: Rule of Law Index
Policy: Judicial System
Description: >
  Rule of Law Index measures extent to which laws are transparently, independently,
  predictably, impartially, equally enforced, and extent to which the actions of government
  officials comply with the law. Measured from low to high (0-1).
Footnote: >
  To view the Rule of Law Index data, download the V-Dem data set and view
  the column "v2x_rule".
  Years after a country's last V-Dem observation, up to 2023, are
  carried forward from that observation and stored as imputed rows
  (ImputationMethod "Forward Extrapolation", ImputationDistance = years
  since the last observation, no distance cap); observed V-Dem years are
  never overwritten.
Indicator: Rule of Law Index
IndicatorCode: RULELW
LowerGoalpost: 0
UpperGoalpost: 1
ScoreFunction: >
  Score = goalpost(VDEM_RULELW, 0, 1)
---

