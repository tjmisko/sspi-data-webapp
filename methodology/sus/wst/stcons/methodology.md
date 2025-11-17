---
ItemType: Indicator
ItemCode: STCONS
ItemName: Status Consumption
Policy: Reduction of Unsustainable Consumption Among Elites
Description: >
  Proportion of CO2 Emissions attributable to the Top 10% of earners.
Footnote: null
Indicator: Status Consumption
IndicatorCode: STCONS
DatasetCodes:
  - WID_CARBON_TOT_P0P100
  - WID_CARBON_TOT_P90P100
  - FPI_ECOFPT_PER_CAP
LowerGoalpost: 30
UpperGoalpost: 1.6
ScoreFunction: >
    Score = goalpost(FPI_ECOFPT_PER_CAP * WID_CARBON_TOT_P90P100 / WID_CARBON_TOT_P0P100, 30, 1.6)
---
## Interpretation
The footprint of consumption among the richest people in society represents an outsized impact from a small group on the environment. The richest individuals consume at a rate many multiples higher than the average individuals in most societies, and a still higher multiple above the rate among the poorest in society. As constructed, the indicator measures country policies across two dimensions:
1. Policies which encourage a more equitable distribution of carbon emissions (proxying for equitable distribution in global footprint). Policies which might discourage overconsumption at the top may include TODO: Provide real policy examples.
2. Policies which decrease the average per capita footprint. Examples might include policies encouraging the adoption of and invention of technologies and business practices which decrease the environmental impact caused by various kinds of consumption.

Note that the structure of the indicator covers the perverse case in which the equitability of consumption is achieved through short-sighted policies that raise consumption at the low end of the distribution to unsustainable levels. In such a case, the reductions in the distributional factor will be offset by a higher average footprint, resulting in a poor score.

## Goalposting
The upper goalpost for this indicator was set by finding a supportable level of consumption and assuming equality of the footprint per capita across the income distribution, so that the consumption in the top-decile matches the average. Based on the data and the levels of footprint suggested by the Global Footprint Index as sustainable targets, we set the Goalpost at TODO: SET GOALPOST.

To set the Lower Goalpost, we examine the tail of the distribution, among the countries which consume the most, and pick a value which best captures the range of policy outcomes we observe in the distribution.


## Motivation and Construction
The Global Footprint Index measures the footprint of consumption in Global Hectares, reflecting the amount of land area needed to support the level of consumption in the economy. This metric provides a comprehensive and wholistic measurement of the impact of consumption on the environment. It does not, however, capture the outsized affect that elite consumption has on the environment.

To capture the distributional effect in our policy indicator, we supplement the Footprint Index's measurement of Environmental Footprint with estimates of the distribution of Carbon Emissions from the World Inequality Database. In particular, we compute a multiplier that captures how much more individuals in the Top 10% of the income distribution emit (as a per capita average among the top decile) than the average across per-capita consumption across the whole distribution. These multiples range from a bit over 2 to over 5, as shown in the Chart below.

TODO: Implement the SeriesPanelChart for the Computed Series Here.

To construct the status consumption indicator, we make the following assumption: the distribution of CO2 emissions from consumption by income is a good proxy for the distribution of Environmental Footprint by income. If this is assumption holds, then we can use the multiplier from CO2 distribution to estimate the Environmental Footprint of Consumption per Capita *among the top decile of the income distribution*. This should be seen as a crude estimate.

TODO: Test the validity of this assumption: what should be true if this assumption true, and is it true? In particular, test whether the p0p100s are correlated as a crude test of validity. If this test works out, we still don't know whether the distributions are the same, but we know that across countries they're at least similar at the average, which gives us some hope.
- TODO: Is this estimate conservative? We'd want to know that on average a rich person's consumption will have a greater effect on Footprint than on 
- TODO: Analyze the Quotient Series FPI_ECOFPT_PER_CAP / WID_CARBON_TOT_P0P100. Is this roughly constant over time? How much that is not tracked in Carbon Emissions gets captured by ECOFPT? If these are constant, then it is not important to include Footprint at all. If they are not constant, what does that mean for our assumtion that these two items have roughly the same distribution by income? Does that have any implications?

---

This indicator measures the extent to which country policies effectively limit overconsumption among elites.
- Inequality in the generation of waste and harmful byproducts like CO2 is a major problem
