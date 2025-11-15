---
DatasetType: Intermediate
DatasetName: Public Transportation Access
DatasetCode: UNSDG_PBTACC
Description: Proportion of population that has convenient access to public transport
Unit: PERCENT
Source:
  OrganizationCode: UNSDG
  OrganizationSeriesCode: 11.2.1
  QueryCode: 11.2.1
DatasetProcessorFile: sspi_flask_app/api/core/datasets/unsdg/unsdg_pbtacc.py
---
Unfortunately, this dataset is not useable. It is identified at the city level, and has only one year of data (2020) for almost all countries. Certainly not for dynamic data.

It does suggest a minor redesign for the ID, since technically this cannot be a dataset according to the current definition because it is identified at the city, not the country, level. Ideally, we would be able to collect this as a dataset and supply extra ID variables (perhaps as a sub-dictionary called AdditionalId or something) to be able to make this happen.
