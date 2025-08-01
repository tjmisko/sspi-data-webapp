I'm in the middle of a large refactor of the codebase in order to eliminate the concept of intermediates and to replace them with the concept of datasets.

Use 49735703d54fbf57ddf31ee6ca392663e53239cb as the base commit, and use `git diff` off that commit to see how files have changed throughout the refactor.

I would like to transform the commented blocks of old collect routes into the new format, in which datasets are collected separately in dataset files (@sspi_flask_app/api/core/datasets) and documented in @datasets/[dataset_code]/documentation.md.

## Key Information for the Refactor

### Dataset Structure Analysis
- **@dataset_collector** and **@dataset_cleaner** decorators register functions in registries
- Dataset files follow `{source}_{series}.py` naming (e.g., `epi_nitrog.py` for `EPI_NITROG`)
- Documentation follows YAML frontmatter format in `@datasets/{dataset_code}/documentation.md`

### Extraction Sources
You need to extract code from **two places**:
1. **Commented collect routes**: Look for `# @collect_bp.route` patterns in compute files
2. **Active compute routes**: Look for `@compute_bp.route` functions that contain cleaning logic

Under the pre-refactor structure, cleaning and computing were combined. The refactor separates:
- **Dataset cleaners**: Handle raw data → clean data transformation
- **Compute routes**: Handle clean data → scored indicators

### Tool Usage for Mappings
Use SSPI CLI commands to understand relationships:
- `sspi metadata indicator {INDICATOR_CODE}` - shows dataset dependencies via `"DatasetCodes"`
- `sspi metadata dataset {DATASET_CODE}` - shows source organization and series codes
- `sspi query sspi_metadata` - shows complete metadata structure
- `sspi metadata --help` - shows available subcommands

### Critical Source Information Requirements
The `Source` field in documentation.md YAML must contain `OrganizationCode` and `OrganizationSeriesCode`:
```yaml
Source:
  OrganizationCode: "UIS"
  OrganizationSeriesCode: "NERT.1.CP"
```

This is enforced by `@sspi_flask_app/models/database/sspi_raw_api_data.py` validation and used as primary keys for:
- `sspi_metadata.get_source_info(dataset_code)` returns this dict
- `sspi_raw_api_data.fetch_raw_data(source_info)` uses it to query raw data
- `build_source_query()` creates MongoDB queries using `"Source.OrganizationCode"` etc.

### Workflow Steps
1. Extract collection logic from commented `# @collect_bp.route` patterns
2. Extract cleaning logic from active `@compute_bp.route` functions
3. Create `{org}_{series}.py` files with `@dataset_collector` and `@dataset_cleaner` functions
4. Create `@datasets/{DATASET_CODE}/documentation.md` with correct Source YAML
5. Run `sspi metadata reload` after documentation changes
6. Verify with `sspi metadata dataset {DATASET_CODE}`

### Pattern Template
```python
@dataset_collector("UIS_ENRPRI")
def collect_uis_enrpri(**kwargs):
    yield from collect_uis_data("NERT.1.CP", **kwargs)

@dataset_cleaner("UIS_ENRPRI") 
def clean_uis_enrpri():
    sspi_clean_api_data.delete_many({"DatasetCode": "UIS_ENRPRI"})
    source_info = sspi_metadata.get_source_info("UIS_ENRPRI")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_uis_data(raw_data, "UIS_ENRPRI", "Percent", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    return cleaned_data
```
