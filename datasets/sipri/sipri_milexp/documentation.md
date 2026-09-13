---
DatasetType: Indicator
DatasetCode: SIPRI_MILEXP
DatasetName: Military Expenditure
Description: Military expenditure (local currency at current prices) according to
  the calendar year as a percentage of GDP.
Unit: Percent of GDP
Source:
  OrganizationCode: SIPRI
  OrganizationSeriesCode: milex
  QueryCode: milex
DatasetProcessorFile: sspi_flask_app/api/core/datasets/sipri/sipri_milexp.py
---

# Military Expenditure (SIPRI_MILEXP)

## Overview

SIPRI Military Expenditure Database, "Share of GDP" sheet: military
expenditure in local currency at current prices, calendar year, as a share of
GDP. The collector requests the 1990-2024 export from the SIPRI Milex backend
(`https://backend.sipri.org/api/p/excel-export/preview`) and stores the whole
workbook as one raw document; the cleaner reads only the "Share of GDP"
section.

## Parsing

- **Years come from the header row.** The sheet header is `Country`, `Notes`,
  then one column per year labelled `1990.0` ... `2024.0`. Each value is
  assigned the year of its column label; `Notes` and any other non-year column
  are skipped by label, never by position.
- **Unit.** The sheet stores shares as fractions of GDP (USA 2023 = 0.0330).
  Every value is multiplied by 100, including shares above 1 (Kuwait 1991 =
  1.17, i.e. 117% of GDP). The cleaner raises if the median share exceeds 0.5,
  which would mean the export has switched to percentages.
- **Missing values.** `. .` (shown as `...` in the export, data unavailable),
  `xxx` (country did not exist or was not independent), blanks, and any cell
  that does not parse as a number are treated as missing, not zero.
- **Rows.** One-cell region and subregion headings are skipped. Historical
  states and aggregates with no current ISO code (Czechoslovakia, German
  Democratic Republic, USSR, Yemen North, Yugoslavia, European Union) are
  dropped. SIPRI labels that pycountry cannot resolve are mapped explicitly:
  Brunei (BRN), Congo, Republic (COG), Cote d'Ivoire (CIV), Gambia, The (GMB),
  Korea, North (PRK), Korea, South (KOR).
- **Notes markers.** The `Notes` column flags budget rather than actual
  spending, exclusion of pensions or paramilitary forces, and currency
  redenominations. These flags are not carried into the clean data.
