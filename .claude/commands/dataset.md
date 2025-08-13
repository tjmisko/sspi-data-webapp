---
allowed-tools: Bash(sspi metadata:*), Bash(sspi clean:*), Bash(sspi query:*)
description: Conduct data processing and cleaning on a raw dataset to prepare a dataset for use in the SSPI
---
You will be provided a **Dataset Code**, which will help you identify relevant files. For example, if the **Dataset Code**
is `UNSDG_MARINE`, then the two most important files to understand will be:
1. @datasets/unsdg_marine/documentation.md: Contains the documentation and the key-value pairs as YAML frontmatter which are used to load the metadata. This must be kept in sync with the Python files.
2. @sspi_flask_app/api/core/datasets/unsdg_marine.py: contains the code used to clean the datasets. In particular, it contains two indicators marked and registerd via two decorators `@dataset_collector` and `@dataset_cleaner`. These work to implement the functionality exposed by the routes defined in @sspi_flask_app/api/core/dataset.py by creating a registry of valid cleaner functions.

You may need to create these files if they do not already exist. Look in the @datasets/ and @@sspi_flask_app/api/core/datasets/ directories and pattern when creating new files.

## Task
1. Be sure to check the live metadata by running the following command
```bash
sspi metadata dataset [DATASET_CODE]
```
If it does not yet exist, you may have to edit or create documentation.md then reload the metadata with `sspi metadata reload` for the change to take effect.
2. Understand the shape of the raw data. Raw data is stored inside of MongoDB, and accessed via database wrappers. All database wrappers are defined at @sspi_flask_app/models/database/. In particular, raw data is stored inside `sspi_raw_api_data` and should be queried via special methods defined in the wrapper script at @sspi_flask_app/models/database/sspi_raw_api_data. These files may be very large, so you may need to think hard and get creative in order to run them.
3. Parse, load, reshape, and clean the raw data in python.
4. Insert the cleaned data into `sspi_clean_api_data`.
