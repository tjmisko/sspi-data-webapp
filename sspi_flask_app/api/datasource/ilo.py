import requests
import json
from sspi_flask_app.models.database import sspi_raw_api_data


def collect_ilo_data(ilo_indicator_code, QueryParams="", URLParams=[], **kwargs):
    yield "Sending Data Request to ILO API\n"
    base_url = f"https://sdmx.ilo.org/rest/data/{ilo_indicator_code}"
    if QueryParams:
        api_url = base_url + f"/{QueryParams}?format=jsondata"
    else:
        api_url = base_url + "?format=jsondata"
    if URLParams:
        api_url += "&"
        api_url += "&".join(URLParams)
    yield "Requesting data from " + api_url
    response_obj = requests.get(api_url)
    org_series_code = f"Indicator={ilo_indicator_code};Parameters={QueryParams}"
    source_info = {
        "OrganizationName": "International Labor Organization",
        "OrganizationCode": "ILO",
        "OrganizationSeriesCode": ilo_indicator_code,
        "QueryCode": org_series_code,
        "BaseURL": base_url,
        "URL": api_url,
        "Format": "SDMX-JSON"
    }
    if response_obj.status_code != 200:
        err = f"(HTTP Error {response_obj.status_code})"
        yield f"\nFailed to fetch data from source {err}"
        yield f"Response: {response_obj.text[:500]}"
        return
    
    try:
        json_data = response_obj.json()
        json_string = json.dumps(json_data, indent=2)
        count = sspi_raw_api_data.raw_insert_one(json_string, source_info, **kwargs)
        yield f"\nInserted {count} observations into the database.\n"
        yield f"Collection complete for ILO {ilo_indicator_code}\n"
    except json.JSONDecodeError as e:
        yield f"\nFailed to parse JSON response: {str(e)}"
        yield f"Response content: {response_obj.text[:500]}"
        return


def collect_ilo_metadata(ilo_indicator_code, **kwargs):
    yield "Sending Metadata Request to ILO API\n"
    base_url = f"https://sdmx.ilo.org/rest/datastructure/ILO/{ilo_indicator_code}"
    api_url = base_url + "?format=jsondata"
    yield "Requesting metadata from " + api_url
    response_obj = requests.get(api_url)
    source_info = {
        "OrganizationName": "International Labor Organization",
        "OrganizationCode": "ILO",
        "OrganizationSeriesCode": ilo_indicator_code,
        "QueryCode": f"Metadata={ilo_indicator_code}",
        "BaseURL": base_url,
        "URL": api_url,
        "DataType": "Metadata",
        "Format": "SDMX-JSON"
    }
    if response_obj.status_code != 200:
        err = f"(HTTP Error {response_obj.status_code})"
        yield f"\nFailed to fetch metadata from source {err}"
        yield f"Response: {response_obj.text[:500]}"
        return
    
    try:
        json_data = response_obj.json()
        json_string = json.dumps(json_data, indent=2)
        count = sspi_raw_api_data.raw_insert_one(json_string, source_info, **kwargs)
        yield f"\nInserted metadata into the database.\n"
        yield f"Metadata collection complete for ILO {ilo_indicator_code}\n"
    except json.JSONDecodeError as e:
        yield f"\nFailed to parse JSON metadata response: {str(e)}"
        yield f"Response content: {response_obj.text[:500]}"
        return


def parse_sdmx_json_to_tabular(json_data):
    """
    Parse SDMX-JSON format from ILO API into tabular data structure.
    
    Returns list of dictionaries with columns:
    - REF_AREA: Country code
    - TIME_PERIOD: Time period (year/month)
    - FREQ: Frequency
    - MEASURE: Measure code
    - SEX: Sex disaggregation
    - AGE: Age group (if present)
    - SOC: Social protection type (if present)
    - MIG: Migration status (if present)
    - OBS_VALUE: Observation value
    - UNIT_MEASURE: Unit of measurement
    """
    results = []
    
    # Navigate to data structure
    if 'data' not in json_data or 'dataSets' not in json_data['data']:
        return results
    
    data_sets = json_data['data']['dataSets']
    if not data_sets:
        return results
    
    # Get structure information
    structures = json_data['data']['structures']
    if not structures:
        return results
    
    structure = structures[0]
    
    # Extract dimension information
    series_dimensions = structure['dimensions']['series']
    observation_dimensions = structure['dimensions']['observation']
    
    # Create dimension mappings
    dim_mappings = {}
    for dim in series_dimensions:
        dim_mappings[dim['id']] = {
            'position': dim['keyPosition'], 
            'values': [v['id'] for v in dim['values']]
        }
    
    # Extract time dimension mapping
    time_mapping = {}
    for time_dim in observation_dimensions:
        if time_dim['id'] == 'TIME_PERIOD':
            time_mapping = {i: v['id'] for i, v in enumerate(time_dim['values'])}
            break
    
    # Process each dataset
    for dataset in data_sets:
        if 'series' not in dataset:
            continue
            
        series_data = dataset['series']
        
        # Process each series
        for series_key, series_value in series_data.items():
            # Decode series key (format: "0:1:2:3:4")
            key_parts = series_key.split(':')
            
            # Build dimension values
            row_base = {}
            
            # Map each dimension position to its value
            for dim_id, dim_info in dim_mappings.items():
                position = dim_info['position']
                if position < len(key_parts):
                    value_index = int(key_parts[position])
                    if value_index < len(dim_info['values']):
                        row_base[dim_id] = dim_info['values'][value_index]
            
            # Process observations for this series
            if 'observations' in series_value:
                for time_index, obs_array in series_value['observations'].items():
                    time_index = int(time_index)
                    
                    # Create row for this observation
                    row = row_base.copy()
                    
                    # Add time period
                    if time_index in time_mapping:
                        row['TIME_PERIOD'] = time_mapping[time_index]
                    
                    # Add observation value (first element in array)
                    if obs_array and len(obs_array) > 0 and obs_array[0] is not None:
                        row['OBS_VALUE'] = obs_array[0]
                        
                        # Set unit measure - default to "Rate" but can be overridden
                        row['UNIT_MEASURE'] = "Rate"
                        
                        results.append(row)
    
    return results


def extract_ilo(raw_ilo_data):
    """
    Takes in a list of raw ILO SDMX-JSON observations and returns a 
    list of flattened tabular data using the parse_sdmx_json_to_tabular function.
    """
    observations_list = []
    for document in raw_ilo_data:
        json_data = json.loads(document["Raw"])
        tabular_data = parse_sdmx_json_to_tabular(json_data)
        observations_list.extend(tabular_data)
    return observations_list


def filter_ilo(observations, dataset_code, unit_label="Rate", rename_map=None, drop_keys=None, **kwargs):
    """
    Filter and transform ILO observations similar to the UNSDG filter pattern.
    
    Args:
        observations: List of observations from extract_ilo
        dataset_code: The SSPI dataset code to assign
        unit_label: The unit label to assign (default: "Rate")
        rename_map: Dictionary for renaming fields
        drop_keys: List of fields to drop
        **kwargs: Filter criteria (e.g., SEX="SEX_T", SOC="SOC_CONTIG_UNE")
    
    Returns:
        List of cleaned observations ready for SSPI database insertion
    """
    if rename_map is None:
        rename_map = {
            "REF_AREA": "CountryCode",
            "TIME_PERIOD": "Year", 
            "OBS_VALUE": "Value",
            "UNIT_MEASURE": "Unit"
        }
    
    if drop_keys is None:
        drop_keys = ["FREQ", "MEASURE"]
    
    filtered_list = []
    for obs in observations:
        # Apply filtering based on kwargs
        drop_obs = False
        for k, v in kwargs.items():
            if k not in obs:
                continue
            list_test = isinstance(v, list) and obs[k] not in v
            value_test = not isinstance(v, list) and obs[k] != v
            if list_test or value_test:
                drop_obs = True
                break
        
        if drop_obs:
            continue
        
        # Create cleaned observation
        cleaned_obs = {}
        
        # Apply field renaming
        for k, v in rename_map.items():
            if k in obs:
                if v == "Year" and k in obs:
                    # Convert Year to integer
                    try:
                        cleaned_obs[v] = int(obs[k])
                    except (ValueError, TypeError):
                        continue  # Skip if year cannot be converted
                elif v == "Value" and k in obs:
                    # Ensure Value is numeric
                    try:
                        cleaned_obs[v] = float(obs[k])
                    except (ValueError, TypeError):
                        continue  # Skip if value cannot be converted
                else:
                    cleaned_obs[v] = obs[k]
        
        # Add dataset code and unit
        cleaned_obs["DatasetCode"] = dataset_code
        cleaned_obs["Unit"] = unit_label
        
        # Only include observations with valid core data
        country_code = cleaned_obs.get("CountryCode")
        # Skip region codes (contain numbers) and invalid country codes
        if country_code and not any(char.isdigit() for char in country_code):
            if (cleaned_obs.get("Year") and 
                cleaned_obs.get("Value") is not None):
                filtered_list.append(cleaned_obs)
    
    return filtered_list
