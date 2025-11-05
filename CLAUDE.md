# SSPI Data Webapp - Claude Instructions

## Project Overview
The SSPI Data Webapp is a Flask application for building and serving the Social Policy and Progress Index dataset. It uses MongoDB for data storage and includes both API endpoints and web interface components.

## Development Workflow

### Setup Commands
```bash
./scripts/setup              # Setup virtual environment and install dependencies
source env/bin/activate      # Activate virtual environment  
flask run --debug            # Start development server
```

### Testing
```bash
pytest                       # Run all tests
pytest tests/unit/           # Run unit tests only
pytest tests/integration/    # Run integration tests only
```

### Branch Management
```bash
gh issue develop -c [Issue Number]  # Create branch for issue
gh pr create -d -r tjmisko          # Create draft PR with reviewer
gh pr ready                         # Mark PR as ready for review
```

## SSPI CLI Usage

The project includes a comprehensive CLI tool accessible via `sspi` command after installation.

### Main CLI Commands
```bash
sspi collect SERIES_CODE     # Collect raw data from source APIs
sspi query DATABASE [CODES]  # Query SSPI databases  
sspi compute SERIES_CODE     # Compute indicator scores
sspi clean SERIES_CODE       # Clean raw API data
sspi impute SERIES_CODE      # Impute missing data
sspi interpolate SERIES_CODE # Interpolate data points
sspi extrapolate SERIES_CODE # Extrapolate data trends
sspi finalize SERIES_CODE    # Finalize processed data
sspi panel SERIES_CODE       # Generate panel data
```

### Data Management
```bash
sspi save DATABASE          # Save database content
sspi delete [options]       # Delete data (with confirmation)
sspi metadata [SERIES]      # View/manage metadata
sspi coverage [options]     # Check data coverage
sspi pull                    # Pull data from remote
sspi push                    # Push data to remote
```

### Viewing & Analysis
```bash
sspi view                    # Open main web interface
sspi view IDCODE            # View line chart for specific indicator
sspi view overview          # Open data overview
sspi view project           # Open GitHub project
sspi view repo              # Open GitHub repository
```

### Database Shortcuts
- `raw` → `sspi_raw_api_data`
- `clean` → `sspi_clean_api_data` 
- `meta` → `sspi_metadata`
- `imputed` → `sspi_imputed_data`

## Code Conventions

### File Structure
- `cli/` - Command-line interface components
- `sspi_flask_app/` - Main Flask application
  - `api/` - API routes and data processing
  - `client/` - Frontend templates and static files  
  - `models/` - Database models and business logic
- `datasets/` - Dataset-specific documentation
- `documentation/` - Project documentation
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

### Commit Messages
Use conventional commit format:
- `feat: Add new feature`
- `fix: Bug fix`
- `docs: Documentation update`
- `refactor: Code refactoring`

## Important Notes
- Always activate virtual environment before development
- Use existing database models and patterns
- Follow MongoDB document structure conventions
- Test both API endpoints and web interface components
- Use `sspi` CLI for data operations rather than direct API calls
- Check documentation/ folder for detailed technical specs

## Development Tips
- When making changes to any non-python files, you must run `touch wsgi.py` to get the development server to reload