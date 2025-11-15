---
ItemType: Indicator
ItemCode: CHMPOL
ItemName: Chemical Pollution Convention Compliance
Policy: Chemical Waste Management
Description: Compliance with three treaties
Footnote: null
Indicator: Chemical Pollution Convention Compliance
IndicatorCode: CHMPOL
DatasetCodes:
  - UNSDG_STKHLM
  - UNSDG_BASELA
  - UNSDG_MONTRL
  - UNSDG_MINMAT
  - UNSDG_ROTDAM
ScoreFunction: >
    Score = average(
        goalpost(UNSDG_STKHLM, 0, 1),
        goalpost(UNSDG_BASELA, 0, 1),
        goalpost(UNSDG_MONTRL, 0, 1),
        goalpost(UNSDG_MINMAT, 0, 1),
        goalpost(UNSDG_ROTDAM, 0, 1)
    )
LowerGoalpost: 0.0
UpperGoalpost: 100.0
---
This policy indicator measures compliance with the core UN treaties regarding hazardous waste.

## Issues
- "The Country Score depends on the amount of information that is sent to the Convention's Secretariat"
- Currently, we're looking at evaluations of reporting procedure. It is good that we are looking directly at policy, but there is uncertainty about implementation.
- EPI has several series that track ozone, lead exposure, and others that look at it from the outcome side, evaluating exposure by "the number of age-standardized disability-adjusted life-years lost per 100,000 due to lead exposure," for example
 
