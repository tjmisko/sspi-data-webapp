---
ItemType: Indicator
ItemCode: FDEPTH
ItemName: Financial Depth
Description: >
    This measure is an aggregation using the simple mean of the following
    measures: 
    
    1) The financial resources provided to the private sector by financial\
    corporations as a percentage of GDP. 
    2) Deposited money in banks and other financial\
    institutions as a percentage of GDP.
Footnote: null
Indicator: Depth
IndicatorCode: FDEPTH
DatasetCodes:
  - WB_CREDIT
  - WB_DPOSIT
Inverted: false
LowerGoalpost: null
Policy: >
    Access to and Engagement with the Formal Financial Sector
SourceOrganization: World Bank
SourceOrganizationIndicatorCode: null
SourceOrganizationURL: https://databank.worldbank.org/
UpperGoalpost: null
---

### The Government's Role in Encouraging the Depth of Finanical Markets

Governments play an important role in creating, structuring, and regulating the
deep financial markets crucial for provision of credit and access to banking
services to citizens.

The **Financial Depth** indicator proxies for government policies encouraging
the private provision of credit and widespread public use of the formal banking
sector.

The indicator is computed as arithmetic mean of two series:

1. Domestic Credit in the Private Sector (WB_CREDIT):
2. Financial System Deposits (WB_DPOSIT): 

#### Proxy
Governments with a high levels of **Domenstic Credit in the Private
Sector** and high levels of **Financial System Deposit** must have 
policy packages which encourage these outcomes.

#### Specific Policies to Encourage Deep Finanicial Markets.
...

#### Potential Counfounding Factors in Policy Proxy: Other Factors
...


### Data Coverage and Imputations

Comprehensive data is available for <span id="good-percent"></span> of
country-year pairs. When either WB_CREDIT or WB_DPOSIT data is missing (<span
    id="warning-percent"></span> of pairs), we impute the missing data for the
particular intermediate, then compute the overall indicator by averaging the
imputed value with the available value for the other series.

When neither WB_CREDIT nor DEPOSIT data is available for a given year (<span
    id="bad-percent"></span> of country-year pairs), we impute the value for
the FDEPTH directly using the most proximate value(s) of FDEPTH.

#### Imputation Methods

For all countries except United Kingdom (**GBR**), all SSPI countries have an
observation in at least one year for both series, so all imputations are
anchored to a valid observation in the dataset. The United Kingdom has no 
observations for WB_DPOSIT

- *Backward Extrapolation*: We use backward extrapolation when there exist no
observation prior to the year imputed. The imputed value is equal to the first
observed value in the dataset (i.e. the most proximate value).
- *Forward Extrapolation*: We use forward extrapolation when there exist no
observation after the year to be imputed. The imputed value is equal to the
last observed value in the dataset (i.e. the most proximate value).
- *Linear Interpolation*: We use linear interpolation when there exist
observations in sample on either side of the missing observation (i.e. the two
most proximate values).

<div id="imputation-chart-fdepth"></div>
<script>
window.addEventListener("load", (event) => {
    window.SSPICharts.push(
        new ItemCoverageMatrixChart(
            document.getElementById("imputation-chart-fdepth"), "FDEPTH", 
            {
                callbacks: [
                    (res) => {
                        const span = document.getElementById("good-percent")
                        const goodPercentString = res.summary[0]
                        const start = goodPercentString.indexOf('(');
                        const end = goodPercentString.indexOf(')', start);
                        const goodPercent = (start > -1 && end > -1) ? goodPercentString.slice(start + 1, end) : null;
                        span.innerHTML = goodPercent
                    },
                    (res) => {
                        const span = document.getElementById("warning-percent")
                        const warningPercentString = res.summary[1]
                        const start = warningPercentString.indexOf('(');
                        const end = warningPercentString.indexOf(')', start);
                        const warningPercent = (start > -1 && end > -1) ? warningPercentString.slice(start + 1, end) : null;
                        span.innerHTML = warningPercent
                    },
                    (res) => {
                        const span = document.getElementById("bad-percent")
                        const badPercentString = res.summary[3]
                        const start = badPercentString.indexOf('(');
                        const end = badPercentString.indexOf(')', start);
                        const badPercent = (start > -1 && end > -1) ? badPercentString.slice(start + 1, end) : null;
                        span.innerHTML = badPercent
                    }
                ]
            }
        )
    )
})
</script>
