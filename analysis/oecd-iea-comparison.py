r"""°°°
# Comparison of OECD and IEA Transport $\text{CO}_2$ Data

The SSPI currently uses Transport from $\text{CO}_2$ emissions data from the OECD, which has limited coverage. This notebook compares OECD data with IEA data, which has more complete coverage.  
°°°"""
# |%%--%%| <ifieeYNKPP|PPc5QgolMw>
r"""°°°
We start by importing packages and defining collector functions to be used in this notebook.
°°°"""
# |%%--%%| <PPc5QgolMw|DQuKx7NMKa>

import pandas as pd
import requests

# |%%--%%| <DQuKx7NMKa|RWRV3tDDzE>
r"""°°°
## Loading the Data

We load the OECD data from the `sspi_clean_api_data` database.  The `sspi_clean_api_data` database is a (very long) list of *observations*, where each observation corresponds to a unique combination of Country, Year, and IndicatorCode.  For every Country-Year-IndicatorCode key, there is at most one observation in the database containing the raw (i.e. not goalposted) value of the indicator and any intermediates used to compute it.  If we did not find data from our datasources, then there will be no record in the database.

Every observation takes the form of a dictionary of a JSON file, which is equivalent to a Python dictionary for our intents and purposes.  More on this below.

For OECD, Max has already written the collector function and cleaned via the compute function for the GTRANS indicator.  The particular data we want—$\text{CO}_2$ emissions from transit sources—is stored under the "intermediates" key in the JSON data, so we extract it from there for each observation returned from our database.
°°°"""
# |%%--%%| <RWRV3tDDzE|aKZicTOzkY>

oecd_res = requests.get("http://127.0.0.1:5000/api/v1/query/indicator/GTRANS?database=sspi_clean_api_data")
oecd = pd.DataFrame(oecd_res.json())
print(oecd.head())

# |%%--%%| <aKZicTOzkY|de318SbQe9>

iea_res = requests.get("http://127.0.0.1:5000/api/v1/query/indicator/GTRANS?database=sspi_clean_api_data")
