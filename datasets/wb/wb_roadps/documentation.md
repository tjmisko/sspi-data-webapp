---
DatasetType: Intermediate
DatasetName: Roads, passengers carried
DatasetCode: WB_ROADPS
Description: Passengers carried by road (million passenger-km)
Unit: Million passenger-km
Source:
  OrganizationCode: WB
  OrganizationSeriesCode: IS.ROD.PSGR.K6
  QueryCode: IS.ROD.PSGR.K6
DatasetProcessorFile: sspi_flask_app/api/core/datasets/wb/wb_roadps.py
---
This data is unusable for the SSPI because it only covers low- and middle-income countries. Almost none of the SSPI67 countries are included in the coverage.

Passengers carried by road are the number of passengers transported by road times kilometers traveled.

The unit "Passenger-km" represents "the transport of one passenger over a distance of one kilometre. The distance to be taken into consideration should be the distance actually travelled by the passenger and only on the national network."

The road transport industry is "a vital engine of global socio-economic growth. It is of vital importance for economic development, creating direct and indirect employment, supporting tourism and local businesses." However, "traffic congestion in urban areas constrains economic productivity, damages people's health, and degrades the quality of life."

Data Source: International Road Federation, World Road Statistics

Data Limitations: "National road associations are the primary source of International Road Federation (IRF) data. As a result, definitions and data collection methods and quality differ, and the compiled data are of uneven quality." Additionally, "Data for transport sectors are not always internationally comparable. Unlike for demographic statistics, national income accounts, and international trade data, the collection of infrastructure data has not been 'internationalized'."

Safety Context: "IRF estimates that every six seconds someone is killed or seriously injured on the world's roads. Nine in ten of these casualties occur in low-income and middle-income countries."

License: "Use and distribution of these data are subject to IRF terms and conditions" with restricted use requiring agreement with IRF Geneva.
