---
DatasetType: Intermediate
DatasetName: Change in Water Use Efficiency
DatasetCode: UNSDG_CWUEFF
Description: >
  Change in Water Use Efficiency (WUE) from 2000-2005 average: WUE is
  the value added of a given major sector divided by the volume of water
  used. WUE at the national level is the sum of the efficiencies in the major
  economic sectors weighted according to the proportion of water withdrawn by
  each sector over the total withdrawals. This dataset provides percentage
  change values from 2006 onward.'
Unit: Percent
Source:
  OrganizationCode: UNSDG
  QueryCode: 6.4.1
DatasetProcessorFile: sspi_flask_app/api/core/datasets/unsdg/unsdg_cwueff.py
---
This dataset is computed from the same data as UNSDG_WUSEFF, using a 2000-2005 average as the baseline and computing percentage change for all years from 2006 onward.

