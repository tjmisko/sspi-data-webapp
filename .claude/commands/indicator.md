---
allowed-tools: Bash(sspi metadata:*), Bash(sspi compute:*), Bash(sspi query:*), Read, Write, Edit, MultiEdit, Glob, Grep
description: Create a new SSPI indicator by implementing methodology files, Python computation logic, and integration with the Flask application
---

You will be provided an **Indicator Code** (6-character alphanumeric) and related information to help you implement a new indicator in the SSPI system.

## SSPI Architecture Overview

The SSPI follows this hierarchy:
```
RawDocumentSet → Dataset → Indicator → Category → Pillar → SSPI
```

- **Dataset**: Raw data from a single source (e.g., `FPI_ECOFPT_PER_CAP`)
- **Indicator**: Scored metric derived from one or more datasets (your target)
- **Category**: Group of related indicators (e.g., `WST` - Waste)
- **Pillar**: Major domain (e.g., `SUS` - Sustainability)

## Implementation Process

### 1. Create Methodology File

**Location**: `methodology/{pillar}/{category}/{indicator}/methodology.md`

**Template**:
```yaml
---
ItemType: Indicator
ItemCode: YOUR_INDICATOR_CODE
DatasetCodes:
  - YOUR_DATASET_CODE
ItemName: Your Indicator Name
Description: >
    Detailed description of what this indicator measures.
Footnote: null
Indicator: Your Indicator Name
IndicatorCode: YOUR_INDICATOR_CODE
Inverted: false  # false = lower values are better, true = higher values are better
LowerGoalpost: 0.0  # Replace with calculated value
Policy: Related Policy Area
SourceOrganization: Data Source Organization
UpperGoalpost: 0.0  # Replace with calculated value
---
```

### 2. Update Category Metadata

**Location**: `methodology/{pillar}/{category}/methodology.md`

Add your indicator to the `IndicatorCodes` list:
```yaml
IndicatorCodes:
  - EXISTING_INDICATOR
  - YOUR_INDICATOR_CODE  # Add here
```

### 3. Analyze Dataset and Determine Goalposts

#### Get Dataset Information
```bash
sspi metadata dataset YOUR_DATASET_CODE
```

#### Analyze Distribution (use Python for statistical analysis)
```bash
sspi query clean YOUR_DATASET_CODE | python3 -c "
import json
import numpy as np
import sys

data = json.load(sys.stdin)
values = [float(record['Value']) for record in data]
values = np.array(values)

print(f'Total observations: {len(values)}')
print(f'Min: {np.min(values):.6f}')
print(f'Max: {np.max(values):.6f}')
print(f'Mean: {np.mean(values):.6f}')
print(f'Median: {np.median(values):.6f}')
print(f'Std Dev: {np.std(values):.6f}')
print()
print('=== Deciles ===')
for i in range(0, 101, 10):
    percentile_val = np.percentile(values, i)
    print(f'{i:3d}th percentile: {percentile_val:.6f}')
print()
print('=== Suggested Goalposts ===')
p10 = np.percentile(values, 10)
p90 = np.percentile(values, 90)
print(f'10th/90th percentiles (recommended):')
print(f'  Lower Goalpost: {p10:.6f}')
print(f'  Upper Goalpost: {p90:.6f}')
"
```

#### Goalpost Selection Guidelines
- **Recommended**: 10th/90th percentiles (excludes outliers)
- **Alternative**: 5th/95th percentiles (broader range)
- **Full range**: Min/Max (may include extreme outliers)

For sustainability indicators:
- **Lower Goalpost**: Good performance threshold (best 10%)
- **Upper Goalpost**: Poor performance threshold (worst 10%)

### 4. Create Implementation File

**Location**: `sspi_flask_app/api/core/sspi/{pillar}/{category}/{indicator}.py`

**Template**:
```python
import logging
from flask import Response, current_app as app
from flask_login import login_required, current_user
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata,
    sspi_indicator_data
)

log = logging.getLogger(__name__)

@compute_bp.route("/YOUR_INDICATOR_CODE", methods=['POST'])
@login_required
def compute_your_indicator():
    # Clear existing data
    sspi_indicator_data.delete_many({"IndicatorCode": "YOUR_INDICATOR_CODE"})
    
    # Fetch clean dataset(s)
    dataset_list = sspi_clean_api_data.find({"DatasetCode": "YOUR_DATASET_CODE"})
    
    # Get goalposts from metadata
    lg, ug = sspi_metadata.get_goalposts("YOUR_INDICATOR_CODE") 
    
    # Score the data
    scored_data, _ = score_indicator(
        dataset_list, "YOUR_INDICATOR_CODE",
        score_function=lambda YOUR_DATASET_CODE: goalpost(YOUR_DATASET_CODE, lg, ug),
        unit="Index"
    )
    
    # Insert scored data
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)
```

**Key Patterns:**
- Route decorator: `@compute_bp.route("/INDICATOR_CODE", methods=['POST'])`
- Function name: `compute_{indicator_code_lower}()`
- Always clear existing data first
- Use `goalpost()` function for standard linear scoring
- Return `parse_json(scored_data)`

### 5. Register Import in Flask App

**Location**: `sspi_flask_app/__init__.py`

Add import line in the appropriate pillar/category section:
```python
import sspi_flask_app.api.core.sspi.{pillar}.{category}.{indicator}
```

Group imports by pillar/category for organization.

### 6. Load Metadata and Test

#### Reload Metadata
```bash
sspi metadata reload
```

This validates methodology files and loads metadata into the database.

#### Verify Metadata
```bash
sspi metadata indicator YOUR_INDICATOR_CODE
```

#### Test Implementation
```bash
# Restart Flask server to pick up new import
touch wsgi.py

# Compute indicator scores
sspi compute YOUR_INDICATOR_CODE
```

#### Verify Results
```bash
# Check sample scores
sspi query sspi_indicator_data YOUR_INDICATOR_CODE | jq '.[] | {CountryCode, Year, Score}' | head -5

# Check scoring distribution
sspi query sspi_indicator_data YOUR_INDICATOR_CODE | jq '.[] | .Score' | sort -n | uniq -c

# Verify extreme cases
sspi query sspi_indicator_data YOUR_INDICATOR_CODE | jq '.[] | select(.Score == 0 or .Score == 1)'
```

## File Structure Reference

```
methodology/
├── {pillar}/
│   ├── {category}/
│   │   ├── methodology.md           # Category file (update IndicatorCodes)
│   │   └── {indicator}/
│   │       └── methodology.md       # Indicator file (create new)

sspi_flask_app/
├── __init__.py                      # Add import here
└── api/
    └── core/
        └── sspi/
            └── {pillar}/
                └── {category}/
                    └── {indicator}.py    # Implementation file (create new)
```

## Common Issues and Solutions

### Metadata Validation Errors
**Error**: `CategoryFile {CATEGORY} specifies IndicatorCodes: {...} Methodology File Tree specifies Children: {...}`

**Solution**: Update the category methodology file to include your new indicator in `IndicatorCodes`.

### 404 Errors on Compute Endpoint
**Cause**: Flask import not registered

**Solution**: 
1. Add import to `sspi_flask_app/__init__.py`
2. Restart Flask server: `touch wsgi.py`

### Scoring Issues
**Problem**: Unexpected score values

**Debug checklist**:
1. Check goalpost values in methodology file
2. Verify `Inverted` setting (false = lower is better)
3. Examine dataset values: `sspi query clean DATASET_CODE`
4. Test goalpost function manually

## Testing Checklist

- [ ] Methodology file created with correct YAML structure
- [ ] Category file updated with new indicator in `IndicatorCodes`
- [ ] Goalposts determined via statistical analysis (not guessed)
- [ ] Implementation file created following naming patterns
- [ ] Import added to `sspi_flask_app/__init__.py`
- [ ] Metadata reloads without validation errors
- [ ] Indicator metadata queryable via CLI
- [ ] Compute endpoint responds (not 404)
- [ ] Scores generated for all available data
- [ ] Scoring logic produces expected results
- [ ] Countries at data extremes score appropriately (0 or 1)

## Key Commands

```bash
# Metadata operations
sspi metadata reload
sspi metadata indicator INDICATOR_CODE
sspi metadata dataset DATASET_CODE

# Data analysis and queries
sspi query clean DATASET_CODE
sspi query sspi_indicator_data INDICATOR_CODE

# Computation
sspi compute INDICATOR_CODE

# Server management
touch wsgi.py  # Restart Flask to pick up changes
```

## Critical Requirements

1. **Indicator codes**: Exactly 6 characters (alphanumeric)
2. **File naming**: Match indicator code (lowercase for Python files)
3. **Statistical rigor**: Always analyze data distribution for goalposts
4. **Pattern consistency**: Follow existing indicator implementations
5. **Testing**: Verify scoring logic and edge cases
6. **Documentation**: Update both methodology and category files

## Multiple Dataset Indicators

For indicators using multiple datasets, modify the score_function:

```python
# Example: combining datasets A and B
score_function=lambda DATASET_A, DATASET_B: goalpost(
    (DATASET_A + DATASET_B) / 2,  # Your calculation here
    lg, ug
)
```

The `score_indicator` utility automatically handles dataset matching and missing data.

---

This command provides complete guidance for SSPI indicator implementation based on the successful STCONS indicator development.