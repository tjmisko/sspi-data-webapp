---
ItemType: Indicator
ItemCode: WATMAN
ItemName: Water Management
Policy: Water Conservation
Description: >
  An index computed as the average of the following two metrics: (1) Change in
    Water Use Efficiency (WUE), 2018 compared with 2010-2015 average: WUE is
    the value added of a given major sector divided by the volume of water
    used. WUE at the national level is the sum of the efficiencies in the major
    economic sectors weighted according to the proportion of water withdrawn by
    each sector over the total withdrawals; (2) Level of Water Stress:
    Freshwater withdrawal as a proportion of available freshwater resources is
    the ratio between total freshwater withdrawal by major economic sectors and
    total renewable freshwater resources, after taking into account
    environmental water requirements. This indicator is also known as water
    withdrawal intensity.
Footnote: null
Indicator: Water Management
IndicatorCode: WATMAN
DatasetCodes:
  - UNSDG_CWUEFF
  - UNSDG_WTSTRS
ScoreFunction: >
    Score = average(
        goalpost(UNSDG_CWUEFF, -20, 50),
        goalpost(UNSDG_WTSTRS, 100, 0)
    )
Inverted: false
LowerGoalpost: null
SourceOrganization: UN SDG
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://unstats.un.org/sdgapi/swagger/
UpperGoalpost: null
---

