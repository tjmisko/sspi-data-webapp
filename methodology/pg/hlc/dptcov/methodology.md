---
ItemType: Indicator
ItemCode: DPTCOV
ItemName: Infant DTP Vaccine Coverage
Policy: Preventative Health
Description: The estimated percentage of children aged 12–23 months who received three
  doses of the combined diphtheria, tetanus toxoid and pertussis vaccine time before
  the survey.
Footnote: null
Indicator: Infant DTP Vaccine Coverage
IndicatorCode: DPTCOV
DatasetCodes:
  - WHO_DPTCOV
Inverted: false
LowerGoalpost: 75
UpperGoalpost: 100
ScoreFunction: >
    Score = goalpost(WHO_DPTCOV, 75, 100)
SourceOrganization: WHO
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://www.who.int/data/gho
---

