# SSPI Data Webapp - Claude Instructions

## Project Overview
The SSPI Data Webapp is a Flask application for building and serving the Social Policy and Progress Index dataset. It uses MongoDB for data storage and includes both API endpoints and web interface components.

## Development Workflow
You will do most of your work inside of git worktrees. This system has a specialized command for setting up git worktrees based on issue numbers: `gh issue worktree develop -c [Issue Number]`, which creates a worktree for the appropriate development branch (as in `gh issue develop -c [Issue Number]`). 

You must be `cd`ed into the correct worktree for you to execute commands, edit files, and see changes without causing conflicts.

You can find important information about the current development status by running

Before making any changes, always:

1. Get Environment Context Information:
```bash
bash scripts/wtdev
```
2. Determine whether you are in a work tree. Remember to do all your work inside the tree, and to check whether you are in the worktree or inside of the main repository. Inside worktrees, you must start the development server with the correct port number. Each worktree has a different port number to ensure parallelism. To find the correct number, consult wsgi.py inside the current worktree. It should never be 5000: that is reserved for the main branch. Every worktree should be a number greater than 5000.
3. Don't be too anxious to restart the development server: it is running in debug mode and need only be refreshed for most changes.

## Key Concepts

### **Series**

A **Series** is structured data containing:
* `CountryCode`
* `Year`
* One or more codes identifying the data content (e.g., `ItemCode`, `DatasetCode`)
* Some numeric observation, e.g. (a `Value` and `Unit`, or a `Score`)

All **Datasets** and **Items** are types of Series.

### **Dataset**
* A **Series** that originates from a **single, unique data source**.
* Always linked to exactly **one** `RawDocumentSet`.
* **Role in dataflow:** Datasets are the direct inputs for Indicators.

### **Item**
* A **Series** whose elements are **Scores** instead of Values.
* Does **not** have a unique source.
* Exists in a hierarchy:
  1. **SSPI** = function(Pillar Scores)
  2. **Pillar** = function(Category Scores)
  3. **Category** = function(Indicator Scores)
  4. **Indicator** = function(Dataset Values)
     * Uses a `ScoreFunction` to transform Dataset Values into Scores.
* Items may depend on one or more Datasets.

### **RawDocumentSet**
* The direct result of an external API call.
* We do not model RawDocumentSets: they are emergent entities that result from calls to `sspi_raw_api_data` based on Source information. The standard source information we use is specified in the documentation.md for each dataset and is accessed via `sspi_metadata.get_source_info(dataset_code)`. You can view the information that draws on by inspecting the output of 
`sspi metadata dataset [DATASET_CODE]` and looking in the `Source` field of the resulting object. Typically, a Source field will specify the `OrganizationCode` and the `QueryCode` used to fetch the dataset, but more information may be specified to make more granular queries depending on the query structure.
* Source information is saved at collection time by the datasource (defined in the source-appropriate file in @sspi_flask_app/api/datasource ) utility called by `@dataset_collector` utility.
* Contains:
  * Source organization code
  * Collection timestamp
  * Collection username
* May yield one or more Datasets.

### **RawDocument**
* A single record inside a `RawDocumentSet`.

## Dataflow

The SSPI data processing pipeline operates in the following order:

```
RawDocumentSet → Dataset → Indicator → Category → Pillar → SSPI
```
* **Stage 0: Collect**
  * Collect RawDocumentSets from external sources
* **Stage 1: Clean**
  * Transform `RawDocumentSet` → `Dataset`
* **Stage 2: Compute**
  * Transform `Dataset` → `Indicator`
* **Stage 3: Impute**
  * Missing Data Imputed, ensuring that all Country-Year-Score pairs are filled for the 2000 - 2023 period across the SSPI67 countries.
* **Stage 4: Finalize**
  * Computes scores for other items (category, pillar, sspi) and prepares plotable datasets

This flow ensures:
* Every Indicator is based on at least one Dataset.
* Dependencies between Items and Datasets are explicit and inspectable.

## Testing
```bash
pytest                       # Run all tests
```
The @tests/ directory contains the information you may need.

## CLI
The project includes a comprehensive CLI tool accessible via the `sspi` command after installation.

### Main CLI Commands
```bash
sspi collect SERIES_CODE     # Collect raw data from source APIs
sspi clean SERIES_CODE       # Clean raw API data
sspi compute SERIES_CODE     # Compute indicator scores
sspi query DATABASE [CODES]  # Query SSPI databases  
sspi impute SERIES_CODE      # Impute missing data
sspi finalize SERIES_CODE    # Finalize processed data
```

### Data Management 
```bash
sspi metadata [SERIES]      # View/manage metadata
```

#### Metadata Subcommands
```bash
# Reload and synchronize metadata
sspi metadata reload         # Clear and reload all metadata from local JSON

# Query hierarchy metadata
sspi metadata pillar [CODE]  # Get pillar metadata
                            # No args: list all pillars
                            # 'CODES': list pillar codes only
                            # Specific code: get details for that pillar

sspi metadata category [CODE] # Get category metadata  
                              # No args: list all categories
                              # 'CODES': list category codes only
                              # Specific code: get details for that category

sspi metadata indicator [CODE] # Get indicator metadata
                               # No args: list all indicators
                               # 'CODES': list indicator codes only
                               # Specific code: get details for that indicator

# Query dataset and item metadata
sspi metadata dataset [CODE]   # Get dataset metadata
                               # No args: list all datasets
                               # 'CODES': list dataset codes only
                               # Specific code: get details for that dataset

sspi metadata item ITEM_CODE   # Get specific item metadata (requires item code)

# Country metadata
sspi metadata country group [CODE] # Get country group metadata
                                   # No args: list all groups
                                   # 'ALL'/'DUMP'/'TREE': show full tree structure
                                   # Specific code: get members of that group
                                   # --remote/-r: query remote server
```

### Database Shortcodes (for use with CLI only)
- `raw` → `sspi_raw_api_data`
- `clean` → `sspi_clean_api_data` 
- `meta` → `sspi_metadata`
- `imputed` → `sspi_imputed_data`

*N.B.* the CLI is mostly case-insensitive.

## Code Conventions

### File Structure
- `cli/` - Command-line interface components and commands
- `sspi_flask_app/` - Main Flask application
  - `api/` - API routes and data processing
  - `client/` - Frontend templates and static files  
  - `models/` - Database models and business logic
- `datasets/` - Dataset-specific documentation
- `methodology` - Item-specific documentation
- `documentation/` - Project documentation (stale, requires updates)
- `tests/` - Test files (unit and integration)

### Coding Standards
- Follow existing patterns in similar components
- Use MongoDB documents for data storage (JSON format)
- All indicators use 6-character alphanumeric codes
- Include proper error handling and logging
- Write tests for new functionality

### Key Concepts
- **Documents**: JSON-formatted data stored in MongoDB with flexible schema
- **Indicators**: 6-character coded metrics for specific policies
- **API Endpoints**: RESTful routes for data collection, processing, and querying
- **Series Codes**: Unique identifiers for data series/indicators

## Important Notes
- Always activate virtual environment before development
- Use existing database models and patterns
- Follow MongoDB document structure conventions
- Test both API endpoints and web interface components
- Use `sspi` CLI for data operations rather than direct API calls
- Check documentation/ folder for detailed technical specs

## Development Tips
- When making changes to any non-python files, you must run `touch wsgi.py` to get the development server to reload

## Finalize Process and Active Schema

### Role of finalize.py in Data Pipeline
The `finalize.py` module (`sspi_flask_app/api/core/finalize.py`) is the final stage in the SSPI data processing pipeline. Its key responsibilities:

1. **Score Generation**: Creates score documents for all items (SSPI, Pillars, Categories, Indicators) using the SSPI hierarchical scoring system
2. **Metadata Enrichment**: Adds metadata from `sspi_metadata` to each score document, including:
   - `Children` field: List of child ItemCodes from the hierarchy 
   - `ItemName` field: The most specific name available (Indicator > Category > Pillar > Name)
3. **Data Storage**: Inserts the finalized score documents into `sspi_item_data` collection

### Active Schema Method
The `active_schema` method in `SSPIItemData` (`sspi_flask_app/models/database/sspi_item_data.py`):

1. **Purpose**: Returns a hierarchical tree structure showing only items with actual score data
2. **Filtering Logic**:
   - Queries only documents with non-null `Score` values
   - Builds tree bottom-up from indicators with scores
   - Excludes empty branches (pillars/categories with no child indicators having data)
   - Uses `ItemName` from documents, falling back to `name_map` parameter if needed
3. **Result**: A pruned tree containing only the active data structure

### Data Coverage and Empty Items
- Items may exist in metadata but lack actual score data
- The schema endpoint (`/api/v1/utilities/coverage/schema`) shows only the active data structure
- Empty pillars and categories (those without any child indicators with data) are automatically excluded
- This ensures charts and visualizations only show meaningful data, not empty metadata structures
- For example, if a pillar has three categories but only one has indicators with data, only that category will appear in the active schema

## Memories

### CLI and API Interactions
- When querying the SSPI, use the CLI. In particular use the `sspi url [stub]` endpoint, defined in @cli/commands/url.py
- Use jq to parse json on the command line
- The correct command to create worktrees by issue number is `gh issue worktree develop -c 653`. This is a custom alias I have to the script @/home/tjmisko/Tools/gh_issue_worktree_develop

### Development Environment
- Be sure to always check your working directory before acting: you may be in git worktree or on the main branch. To tell the difference, you can check whether .git is a file or a directory.
- Always run the setup script inside the worktree, never in the main repository. You're setting up the worktree to work correctly by doing so. 
- You must always check your pwd before running commands when you are working with worktrees. You should always assume that worktrees may be involved
- Never instantiate one worktree inside another. Before instantiating, always check that you are in the main repository.
- Don't guess at metadata like seriescodes, itemcodes, or indicator codes. Look them up using `sspi metadata item` or `sspi metadata dataset`. See their implementation and subcommands at @cli/commands/metadata.py
- You must always kill only the server running on the current port for the worktree. Other servers are running in parallel.
- You don't need to restart the flask server every time. Just touch wsgi.py. Only for major changes or module/import time changes do you need to restart

- You must use the sspi cli to access any `@login_protected` routes. Just sending curl requests to the URLs will fail because token based authentication is required. The sspi cli should always be used in such instances