---
DatasetType: Computed
DatasetCode: IEA_COALPW
DatasetName: Energy From Coal
Description: Percentage of a country's total energy supply generated from coal and
  coal derived sources. This dataset is computed from constituent IEA energy datasets
  rather than collected directly from the IEA API.
Dependencies:
  - IEA_TLCOAL
  - IEA_NATGAS
  - IEA_NCLEAR
  - IEA_HYDROP
  - IEA_GEOPWR
  - IEA_BIOWAS
  - IEA_FSLOIL
ComputeMethod: Sum of constituent energy datasets to create TTLSUM and component values
Source:
  OrganizationCode: IEA
  OrganizationName: International Energy Agency
  Note: Computed from constituent datasets, not directly collected
DatasetProcessorFile: sspi_flask_app/api/core/datasets/iea/iea_coalpw.py
---

