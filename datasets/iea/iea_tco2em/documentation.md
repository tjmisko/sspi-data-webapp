---
DatasetType: Intermediate
DatasetName: CO2 from Transport
DatasetCode: IEA_TCO2EM
Description: Total CO2 emissions from the transport sector, in kilograms of CO2. The
  IEA reports million tonnes (Mt CO2); the cleaner multiplies by 1e9 to convert to
  kilograms. Divide by population for kilograms per inhabitant.
Unit: kg CO2
Source:
  OrganizationCode: IEA
  QueryCode: CO2BySector
DatasetProcessorFile: sspi_flask_app/api/core/datasets/iea/iea_tco2em.py
---
