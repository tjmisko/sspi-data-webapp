---
allowed-tools: Bash(sspi metadata:*), Bash(sspi compute:*), Bash(sspi query:*), Read, Write, Edit, MultiEdit, Glob, Grep
description: Create a new SSPI indicator by implementing methodology files, Python computation logic, and integration with the Flask application
---

You will be provided an **Indicator Code** (6-character alphanumeric), and you will be asked to help fill in the @impute_bp route for that indicator. When computing the indicator in the associated @compute_bp, there may be "incomplete" observations inserted into `sspi_incomplete_indicator_data`.

## Incremental Development Process
The easiest way to develop this kind of route is to use "intermediate return" statements, placing the return in the middle of your impute route to see the intermediate state of the JSON as you work (you must return any json-like python structure wrapped in a `parse_json` utility). 

For example, you're writing an impute route. You need to see the structure of the data you have after you've sliced out the dataset data from both `sspi_incomplete_indicator_data` and `sspi_indicator_data` and joined the lists together. The best way to do this is to place a return statement inside the impute route in which you return that joined list, then examine it with jq on the command line by running `sspi impute indicator [IDCODE] | jq [your filter]`. Then move to the next step and move the return statement down as needed. Remember to clean up the return statement and format it properly when you are finished coding.

## Get Indicator Documentation
```
sspi metadata indicator [IDCODE]
```

## Get Coverage Report
We are aiming for perfect coverage from 2000-2023 across the 66 countries in `sspi metadata country group sspi67`.

You can run `sspi coverage report [IDCODE]` to receive a summary of the coverage status. The imputation is complete when this command returns `Indicator code [IDCODE] has complete coverage over SSPI67 from 2000 to 2023.`

## Imputation Functions
You will primarily use `extrapolate_forward`, `extrapolate_backward`, and `interpolate_linear` to fill in missing observations. These are defined in @sspi_flask_app/api/resources/utilities.py, and the behavior of each is tested in @tests/unit/utilties. 

If a country has no observations at all, you will need to ask the user what to do. There are typically two options, in order of preference:
1. Impute a Regression Based Estimate Based on Another Dataset
2. Impute the Global Average for the Missing Country

## Producing Imputations
Imputations should be stored in `sspi_imputed_data`. The observations are structured exactly like those in `sspi_indicator_data`, except that the values for at least one of the datasets are imputed. Imputed data is recorded with the `"Imputed": True` flag and the `ImputationMethod: [method]`, which is taken care of by default inside the imputation utilties.

### Dataset vs. Indicator Level Imputation
The question you will need to think hard about is whether you will need to do this at the indicator level or the dataset level. If an indicator depends on multiple datasets, then it is likely that you have some of those datasets but not all for a given year and country. By running `sspi query sspi_incomplete_indicator_data [IDCODE] | jq [your filter here]`, you can examine which datasets are available. 

Usually, you will be doing imputations at the dataset level. You will need to pull both the complete and incomplete data, slice out each of the datasets using the `slice_dataset` utility, then run the imputations to fill out the data. Next you can recompute indicator scores for the whole series with imputations, then finally filter down to only the indicator documents which contain an imputed value with the `filter_imputations` utility. You can see an example of how to do a routine like this in the impute process of @sspi_flask_app/api/core/sspi/sus/lnd/watman.py .

