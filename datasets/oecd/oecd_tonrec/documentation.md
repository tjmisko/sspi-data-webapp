---
DatasetType: Intermediate
DatasetCode: OECD_TONREC
DatasetName: Net ODA Received by Recipient
Description: >
  Total net official development assistance (ODA) received by each recipient
  country from all official donors (bilateral and multilateral), in millions
  of current US dollars (OECD DAC2A, donor ALLD, measure 206).
Unit: >
  US dollar, Millions, Current prices
Source:
  OrganizationCode: OECD
  QueryCode: "DSD_DAC2@DF_DAC2A(ALLD..206.USD.V)"
DatasetProcessorFile: sspi_flask_app/api/core/datasets/oecd/oecd_tonrec.py
---

### Source query

Collected from the OECD SDMX REST API, dataflow `OECD.DCD.FSD,DSD_DAC2@DF_DAC2A`
(DAC2A: Aid (ODA) disbursements to countries and regions), key
`ALLD..206.USD.V`:

| Dimension     | Code   | Label                                               |
|---------------|--------|-----------------------------------------------------|
| DONOR         | `ALLD` | Official donors (DAC + non-DAC + multilateral)      |
| RECIPIENT     | (all)  | every recipient country, region and income group    |
| MEASURE       | `206`  | Official development assistance (ODA), disbursements |
| UNIT_MEASURE  | `USD`  | US dollar                                           |
| PRICE_BASE    | `V`    | Current prices                                      |

`FLOW_TYPE` is an attribute in DAC2A and is always `D` (Disbursements); measure
206 is the net figure (gross ODA is measure 240, net excluding debt relief is
250). The response is requested as SDMX-CSV 2.0 with labels
(`Accept: application/vnd.sdmx.data+csv;version=2.0.0;labels=name`) and stored
verbatim as one raw document. `UNIT_MULT` is `6` (Millions), so values are USD
millions and are not rescaled.

The raw document is stamped with `Source.OrganizationCode = OECD`,
`Source.OrganizationSeriesCode = OECD.DCD.FSD,DSD_DAC2@DF_DAC2A`,
`Source.QueryCode = DSD_DAC2@DF_DAC2A(ALLD..206.USD.V)` and the request URL.
The `Source` block above is an exact subset of that stamp, which is what
`sspi_raw_api_data.build_source_query` matches on.

### Cleaning

- `CountryCode` is the `RECIPIENT` code; only ISO 3166-1 alpha-3 codes known to
  `pycountry` are kept. Regional and income-group aggregates (`A`, `E`, `F`,
  `O`, `S`, `DPGC`, `LDC`, `LMIC`, `UMIC`, multilateral-agency codes such as
  `5WB001`, and non-ISO `XKV` Kosovo) are dropped and counted in the cleaner's
  drop report.
- Rows are additionally filtered to `DONOR=ALLD`, `MEASURE=206`,
  `UNIT_MEASURE=USD`, `PRICE_BASE=V`, `UNIT_MULT=6`; anything else is counted.
  Only the `ALLD` donor row is used: summing over every `DONOR` code would
  double count, because `DAC`, `ALLM`, `WXDAC` and the individual donors all
  roll up into `ALLD`.
- `Year` is `TIME_PERIOD` as an integer; `Value` is `OBS_VALUE` as a float.
- `Unit` and `Description` are composed from the source's own label columns
  (`Unit of measure`, `Unit multiplier`, `Price base`; `Measure`, `Flow type`,
  `Donor`, dataflow name).
- **Negative values are kept as published.** Net ODA received is negative when
  a recipient's repayments exceed new disbursements (CHN every year 2011-2023,
  THA 2005-2012 and 2018-2019, IDN, MYS, PER, PHL, ARG, MEX, SAU, CHL in
  scattered years). The cleaner does not clamp; the indicator score function
  (`goalpost`) clamps to zero, so net repayers score zero on the recipient arm.

### Donor-scope choice

`ALLD` (all official donors) is used so the dataset describes total ODA
received, including multilateral ODA. DAC-country-only ODA (`DONOR=DAC`) is
40-50% lower for large recipients such as IND and ETH. The dataflow already
contains 2024; the collector does not cap `endPeriod`.

Coverage: 29 of the SSPI67 countries are DAC2A recipients (25 complete
2000-2023; CHL and URY graduate from the ODA recipient list in 2018; SVN is a
recipient only 2000-2002 before becoming a donor; SGP's recipient data ends in
1995 and RUS never appears).

### Open decisions

See `docs/data-source-tasklist.md`:

- **D-9** (price basis): current USD here; the per-capita recipient arm of
  FORAID divides by population, so it is unaffected by the GDP-denominator
  choice, but the price year still matters if constant-price series are
  preferred.
- **D-10** (FORAID design): (ii) `ALLD` versus `DAC` donor scope — `ALLD`
  implemented and documented above; (iii) how to score RUS, SGP and
  post-graduation CHL/URY (2018-2023), which have no recipient data; (iv)
  negative net ODA received — kept net and clamped by the score function
  rather than switching to gross ODA (measure 240) or net excluding debt relief
  (measure 250).
