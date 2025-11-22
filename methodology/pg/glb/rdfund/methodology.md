---
ItemType: Indicator
ItemCode: RDFUND
ItemName: Research and Development
Policy: Public R&D
Description: >
  Arithmetic mean of two datasets:
  1. Proportion of GDP spent on R&D.
  2. Number of researchers per 1 million people (weight 0.50).
Footnote: null
Indicator: Research and Development
IndicatorCode: RDFUND
DatasetCodes:
  - UNSDG_RDPGDP
  - UNSDG_NRSRCH
LowerGoalpost: 0
UpperGoalpost: 4
ScoreFunction: >
    Score = average(
        goalpost(UNSDG_RDPGDP, 0, 4),
        goalpost(UNSDG_NRSRCH, 0, 5000)
    )
---

