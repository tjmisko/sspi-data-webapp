---
DatasetType: Intermediate
DatasetName: Waste Generated Per Capita
DatasetCode: EPI_MSWGEN
Description: EPI indicator score (WPC) for total municipal solid waste generated per
  person each year, scaled 0 to 100 where higher scores mean less waste per person.
Unit: Index
Source:
  OrganizationCode: EPI
  OrganizationSeriesCode: WPC
  QueryCode: epi2024indicators
DatasetProcessorFile: sspi_flask_app/api/core/datasets/epi/epi_mswgen.py
---
Currently, this dataset pulls the indicator index value. Ideally we would change this to look at the underlying data instead, but for now this is fine. TODO: Update EPI_MSWGEN to pull from EPI Raw Data instead of EPI indicators.
