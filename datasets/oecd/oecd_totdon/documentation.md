---
DatasetType: Intermediate
DatasetCode: OECD_TOTDON
DatasetName: Net ODA Disbursed by Donor
Description: >
  Total net official development assistance (ODA) disbursed by each donor
  country to all recipients, in millions of current US dollars (OECD DAC1,
  measure 1010, flow type 1140).
Unit: >
  US dollar, Millions, Current prices
Source:
  OrganizationCode: OECD
  QueryCode: "DSD_DAC1@DF_DAC1(._Z.1010._Z.1140.USD.V)"
DatasetProcessorFile: sspi_flask_app/api/core/datasets/oecd/oecd_totdon.py
---

### Source query

Collected from the OECD SDMX REST API, dataflow `OECD.DCD.FSD,DSD_DAC1@DF_DAC1`
(DAC1: Flows by provider (ODA+OOF+Private)), key `._Z.1010._Z.1140.USD.V`:

| Dimension     | Code   | Label                                  |
|---------------|--------|----------------------------------------|
| DONOR         | (all)  | every donor reporting to DAC1          |
| SECTOR        | `_Z`   | Not applicable                         |
| MEASURE       | `1010` | Official Development Assistance (ODA)  |
| TYING_STATUS  | `_Z`   | Not applicable                         |
| FLOW_TYPE     | `1140` | Disbursements, net                     |
| UNIT_MEASURE  | `USD`  | US dollar                              |
| PRICE_BASE    | `V`    | Current prices                         |

The response is requested as SDMX-CSV 2.0 with labels
(`Accept: application/vnd.sdmx.data+csv;version=2.0.0;labels=name`) and stored
verbatim as one raw document. `UNIT_MULT` is `6` (Millions), so values are USD
millions and are not rescaled. `SECTOR=_Z` and `TYING_STATUS=_Z` are required:
the intuitive `1000`/`_T` key returns HTTP 404 (`NoResultsFound`).

The raw document is stamped with `Source.OrganizationCode = OECD`,
`Source.OrganizationSeriesCode = OECD.DCD.FSD,DSD_DAC1@DF_DAC1`,
`Source.QueryCode = DSD_DAC1@DF_DAC1(._Z.1010._Z.1140.USD.V)` and the request
URL. The `Source` block above is an exact subset of that stamp, which is what
`sspi_raw_api_data.build_source_query` matches on.

### Cleaning

- `CountryCode` is the `DONOR` code; only ISO 3166-1 alpha-3 codes known to
  `pycountry` are kept. DAC aggregates (`DAC`, `DACEU`, `DAC_EC`, `G7`,
  `WXDAC`, `ALLM`, `4EU001` EU Institutions) are dropped and counted in the
  cleaner's drop report.
- Rows are additionally filtered to `MEASURE=1010`, `FLOW_TYPE=1140`,
  `UNIT_MEASURE=USD`, `PRICE_BASE=V`, `UNIT_MULT=6`; anything else is counted.
- `Year` is `TIME_PERIOD` as an integer; `Value` is `OBS_VALUE` as a float.
- `Unit` and `Description` are composed from the source's own label columns
  (`Unit of measure`, `Unit multiplier`, `Price base`; `Measure`, `Flow type`,
  dataflow name).
- Net disbursements can be negative (repayments exceed new disbursements); they
  are kept as published. Clamping is left to the indicator score function.

### Measure and flow-type choice

Net disbursements (1010/1140) are the cash-flow ODA measure published
consistently for all years. The DAC headline moved to grant-equivalent ODA
(measure 11010, flow type 1160) in 2018, but that series does not exist before
2018, so it is not usable for a 2000-2023 panel. The dataflow already contains
2024 and preliminary 2025 values; the collector does not cap `endPeriod`, so
the most recent year should be expected to revise.

Coverage: 39 of the SSPI67 countries are DAC1 donors (33 complete 2000-2023;
ROU from 2008, HUN from 2003, LVA from 2002, LTU from 2001, SVN from 2005).

### Open decisions

See `docs/data-source-tasklist.md`:

- **D-9** (price basis): this dataset is in current USD. The FORAID score
  divides it by WB_GDPMKT, which is currently constant 2015 USD
  (`NY.GDP.MKTP.KD`); the recommendation is to switch the denominator to
  current USD (`NY.GDP.MKTP.CD`) rather than switch this dataset to constant
  prices (`PRICE_BASE=Q`, base 2024).
- **D-10** (FORAID design): (i) simple DAC1 totals now versus a CRS-derived
  "good aid" sector exclusion, which lives on a different base path and cannot
  be applied uniformly to all 39 donors; (iii) RUS and SGP have neither donor
  nor recipient data 2000-2023, and CHL/URY stop being recipients in 2018 —
  scoring them as zero donors, imputing, or excluding is a methodology call.
