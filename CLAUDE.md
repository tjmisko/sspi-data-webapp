# SSPI Data Webapp - Claude Instructions

## Project Overview
The SSPI Data Webapp is a Flask application for building and serving the
Sustainable and Shared-Prosperity Policy Index dataset and webpage. 

- Backend: MongoDB (via pymongo) for data storage and includes both 
API endpoints and web interface. (`./sspi_flask_app/api/`)
- Frontend: Raw Javascript, HTML (Jinja2
Templates), and CSS. (`./sspi_flask_app/client/`) 

## Development Workflow

### Setup Commands
```bash
flask run --debug            # Start development server
touch wsgi.py                # Refresh development server and rebuild script and style bundle
```

### Testing
```bash
pytest                       # Run all tests
```

## SSPI CLI Usage
The project includes a comprehensive CLI tool 
accessible via `sspi` command after installation.
You can use it with bash tool calls.

### Main CLI Commands
```bash
sspi collect SERIES_CODE     # Collect raw data from source APIs
sspi query DATABASE [CODES]  # Query SSPI databases  
sspi compute SERIES_CODE     # Compute indicator scores
sspi clean SERIES_CODE       # Clean raw API data
sspi impute SERIES_CODE      # Impute missing data
sspi finalize                # Generate finalized score and chart data
```

### Data Management
```bash
sspi delete [options]       # Delete data (with confirmation)
sspi coverage [options]     # Check data coverage

```

### Understanding Metadata Structures
Use the following commands to view the complete live 
metadata contained in the `sspi_metadata` database:

> Bash(sspi url:*)

> Bash(sspi metadata item:*)

> Bash(sspi metadata pillar:*)

> Bash(sspi metadata category:*)

> Bash(sspi metadata indicator:*)

> Bash(sspi metadata dataset:*)

### Database Shortcuts
- `raw` → `sspi_raw_api_data`
- `clean` → `sspi_clean_api_data` 
- `meta` → `sspi_metadata`
- `imputed` → `sspi_imputed_data`

## Code Conventions

### File Structure
- `cli/` - Command-line interface components (`sspi` for defined 
- `sspi_flask_app/` - Main Flask application
  - `api/` - API routes and data processing
  - `client/` - Frontend templates and static files  
  - `models/` - Database models
- `datasets/` - Dataset-specific documentation files
- `methodology/` - Item-specific documentation files
- `documentation/` - Project documentation
- `tests/` - Test files (unit and integration)

### Coding Standards
- Follow existing patterns in similar components
- Use MongoDB documents for data storage on backend (List and Dictionary JSON format)
- All indicators use 6-character alphanumeric codes
- Include proper error handling and logging
- Write tests for new functionality

### Key Concepts
- **Documents**: JSON-formatted data stored in MongoDB with flexible schema
- **Indicators**: 6-character coded metrics for specific policies
- **API Endpoints**: RESTful routes for data collection, processing, and querying
- **Series Codes**: Unique identifiers for data series/indicators

## Development Tips
- When making changes to any non-python files, you must run `touch wsgi.py` to get the development server to reload
- Use bash tool call to `sspi` and its subcommands for CLI for data operations rather than direct API calls.
- Never load the JavaScript in via script tags in the HTML unless explicitly told to. It is bundled by an asset bundler (in assets.py) system that minifies all of the js and puts iti nto sspi_flask_app/client/static/script.js. NEVER, EVER try to modify the script.js file directly!

