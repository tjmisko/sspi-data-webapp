# Backend Documentation

## Writing a route for `collect.py`
1. Find and test the link for the source API.  You might be able to test the link from your browser, but if not, you can test it from the application.  If we already have another indicator from that source, look in the `datasource` folder to see if we've already written something that can accomplish this task.
2. The first step of any `collect_bp` route is to hit the source API with an HTTP `GET` request.  In python, this is accomplished via the `requests` module.
3. In order to process and store the request, we'll need to see its form to know what to do with it.  The best way to do this is to `return parse_json(response)` at the end of the route-in-progress, where `response` is whatever JSON response is handed back in `response = requests.get("https://api-link")`. With that return statement in place, the route-in-progress is now a valid route and can be run without getting a server error.  In your command line, `flask run` the application and navigate to the endpoint `/api/v1/collect/[your_indicator_code]`, which should now display the raw JSON returned by the source API.  
	* The reason we need to `return parse_json(response)` instead of `return response` is that the object `response` is a Python object, not a JSON object or dictionary.  The `parse_json` function is a simple wrapper that uses `json.dumps` and `json.loads` in order to return a valid object to Flask, can only accept strings and "serializable objects" like properly parsed JSON.
	* You may find that this does still return an `Internal Server Error`.  Oftentimes this has to do with JSON serialization.  Read the error messages in your terminal and follow your nose.
	* One thing we're looking for here is whether or not the source API is *paginated*.  If it is, then it will only return the first page of the data, and you will have to hit the API one time for each number of pages.  You can accomplish this with a simple `for` loop.  You'll know how many times to iterate based on the first response you received, which should tell you how many total pages there are.  Every time you loop, simply string add the appropriate URL argument (or however the source API implements this) for page numbers to the base URL slug and collect all of the responses.  You may find it easier to process and insert each page one at time, or to batch insert everything at the end.  Use your best judgement based on the response structure.  
4. From here, we need to store our data in the `sspi_raw_api_data` database.  To accomplish this, we use the `PyMongo` API, documented [here](https://pymongo.readthedocs.io/en/stable/tutorial.html).  For a single observation `obs`, we can insert via `sspi_raw_api_data.insert_one(obs)`.  If you have a list of observations `obs_lst`, then you may use `sspi_raw_api_data.insert_many(obs_lst)` to insert all observations in `obs_lst`.  
6. Every observation in `sspi_raw_api_data` must contain metadata on the user running the route, the collection time, and the `IndicatorCode`, which is the standard six uppercase letter SSPI Indicator Code for which we are collecting data.  **If an observation does not have a `IndicatorCode` in the `collection-info` field, we won't be able to find it later for compute**.  Hence, a typical `obs` inserted into the database will look like the below.  Here, `r` corresponds to the JSON response we want to store.
```python
{"collection-info": 
	{"CollectedBy": current_user.username,            
	"IndicatorCode": IndicatorCode
	"CollectedAt": collection_time}, 
"observation": r}
```

## Writing a route for `compute.py`
1. First, we grab the data we stored in the `sspi_raw_api_data`.  We stored everything that goes into computing an indicator in `sspi_raw_api_data`, so now we can query `sspi_raw_api_data` using the PyMongo API (documentation [here](https://pymongo.readthedocs.io/en/stable/tutorial.html)).  We want to get all of the observations pertaining to a particular indicator from the database.  Recall that we denoted the indicator to which raw observations belong with the `IndicatorCode` field, which will be populated with the six uppercase letter SSPI Indicator Code string.  Hence, we call `sspi_raw_api_data.find(mongoQuery)`, where the variable `mongoQuery` specifies what data we want to find.  See the addendum below on queries for more information.  For now, you can use the utility function `fetch_raw_data`  below.
2. Next comes the processing phase, which will be different for every indicator you do.  The goal of the processing phase is operate on the raw data and turn it into cleaned data.  You'll have to be creative to get this done.  
	* For example, the BIODIV route requires a few steps, in which I harvest the data from the raw observations, group together observations for Marine, Terrestrial, and Freshwater at the country-year level, then I run an average that returns "NaN" if anything is missing, and finally I store everything in an output list.
		* That was the best way I thought of to do it for BIODIV; it may not be the best way to do it for you.
	* If you can only get a link for `.csv` data, you can absolutely use `pandas` or any other library to work with it.  
	* Likewise, certain operations like pivoting from wide to long formatting are best done through `pandas`.
	* Use M49 or ISO-3 country codes where possible to avoid issues with ambiguous country names.  I've loaded in an excellent library called `pycountry` which allows search by name, code lookup, fuzzy search, and transforming between code formats.  Documentation [here](https://pypi.org/project/pycountry/).  All of our internal methods will use the three capital letter ISO-3 country codes when querying `sspi_clean_api_data`, so be sure to store that information in the clean observations.
	* Keep track of "intermediates" as you go.  The idea is that, at the end of the computation, you should be able to replicate your results from just the intermediates you've kept around.  For example, the BIODIV compute route has three intermediates—the values for Marine, Freshwater, and Terrestrial.  If we ever needed to impute or check something, we could use the intermediates to do it.  Intermediates will be stored in the final observations as a nested dictionary.  See below for details, and refer to the BIODIV route as an example.
	* The `_id` field is added by MongoDB automatically.  You do not need to handle this yourself.
	* **I highly recommend incremental development here!  Use `print` statements and `parse_json` returns to your advantage.  Test as you go to make sure everything is working!**
3. The final step is to store the data in the `sspi_clean_api_data` database.  The format for clean API data is given below.  Again, we'll call the `insert_many` method to accomplish this.

## Using the SSPI API
* `/api/v1/query` runs the `query_full_database` function, which dumps back an unmodified JSON view of the entire database.  The default database is `sspi_main_data_v3`. You can use arguments after the URL to specify other databases, *e.g.*:
	* `/api/v1/query?database=sspi_raw_api_data` 
	* `/api/v1/query?database=sspi_clean_api_data`
* `/api/v1/query/indicator/<IndicatorCode>` runs the `query_indicator` function, which returns the contents of a database filtered by indicator code.  This will be one of the main ways of testing when developing your `collect` and `compute` routes.  As before, modify the default database with URL arguments.
* `/api/v1/download`: If for some reason you need to download the contents of a database, you can use this.  This is mainly intended for use later to link up to a download button on the data page.
* `/api/v1/api_coverage` is the route used to implement the internal tracker of how many routes have been completed.  All it's doing is checking whether there's a route registered with the appropriate name.
* `/api/v1/coverage` is a badly named route that right now is handling processing data and returning it for display on the Tabulator table on the website.  This route is still in developing and will be changing in name and content.  
* `/api/v1/delete` will direct you to a form that allows you to delete certain contents of a database.  This will when you need to wipe a database and start again, which will probably happen a number of times during the course of your development. 

## Querying Observations from MongoDB
* In MongoDB, we store "documents," which is terminology that might be confusing.  You can think of a MongoDB "document" as a Python dictionary or JSON object.   A MongoDB database, e.g. `sspi_raw_api_data`,  is a collection of documents that can be queried.
* Building queries in MongoDB is pretty natural.  Basically, we pass the `find` or `find_one` method a Python dictionary that tells it what the query parameters are.  
	* Passing the `find` method an empty dictionary `{}` will return everything in the database, since there are no query parameters to filter.  
	* To implement basic filtering, we can pass a dictionary like `{"color":"red"}`, which will return all of the documents which contain a color field with the value "red."  
	* A query like {"color": "red", "size": "small"} will get only documents with both "red" color and "small" size.  It's like an AND.  
	* For us, it will be important to do nested queries.  If we want to look further inside an observation, we can used the `.` syntax to check a subfield.  For example, `{"collection-info.IndicatorCode":"BIODIV"}` returns all documents which have a `collection-info` field which holds dictionary containing a `IndicatorCode` field holding a `"BIODIV"` value. 
	* There are a whole bunch of really powerful operators and ways of implementing complex queries in the [Mongo Documentation](https://pymongo.readthedocs.io/en/stable/tutorial.html).
* For fetching the raw data, I've written a quick utility function, which you're welcome to use to make things a little simpler to read.
```python
def fetch_raw_data(IndicatorCode):
	mongoQuery = {"collection-info.IndicatorCode": IndicatorCode}
	raw_data = parse_json(sspi_raw_api_data.find(mongoQuery))
	return raw_data
```
* *n.b.* When I refer to an "observation," each observation is a distinct MongoDB "document." There is some potential for confusion here. For example, a single raw data "observation"—one document in MongoDB—for the BIODIV indicator contains data for all of the years, since that's how the API returns the data.  In the example observation below, you can see how the "years" field has a string that can be parsed into JSON to get all of the data we need.  Below, we will refer to cleaned "observations" as documents in the `sspi_clean_api_data` database which contain information for one country, in one year, for one indicator.  Hopefully what I mean by "observation" will be clear from context, but mind the ambiguity in my usage.

## Example Raw Observation
This is what the first raw data document looks like for BIODIV, which contains the raw "observation." Notice that there are three top level fields: `_id`, `collection-info`, and `IndicatorCode`.  
```python
{"_id":{"$oid":"647a0c3524d162df31d2d48f"},
 "collection-info":
	 {"CollectedAt":{"$date":"2023-0602T11:35:13.966Z"},
	  "CollectedBy":"tjmisko",
	  "IndicatorCode":"BIODIV"},
 "observation":
	{"activity":null,"age":null,
	 "basePeriod":null,"cities":null,
	 "disability_status":null,"education_level":null,
	 "freq":null, "geoAreaCode":"4",
	 "geoAreaName":"Afghanistan","geoInfoUrl":null,
	 "goal":"14", "hazard_type":null,
	 "ihr_capacity":null,"indicator":"14.5.1",
	 "level_status":null,"location":null,"lowerBound":null,
	 "migratory_status":null,
	 "mode_of_transportation":null,
	 "name_of_international_agreement":null,
	 "name_of_international_institution":null,
	 "name_of_non_communicable_disease":null,
	 "policy_domains":null,"reporting_type":null,
	 "series":"ER_MRN_MPA","seriesCount":"6049",
	 "sex":null,"source":null
	 "target":"14.5","tariff_regime_status":null,
	"timeCoverage":null,"type_of_facilities":null,
	"type_of_mobile_technology":null,
	"type_of_occupation":null,"type_of_product":null,
	"type_of_skill":null,"type_of_speed":null,
	"units":"PERCENT","upperBound":null,
	"years":"[{\"year\":\"[1964]\",\"value\":\"\"},
	{\"year\":\"[1969]\",\"value\":\"\"},
	{\"year\":\"[1970]\",\"value\":\"\"},
	{\"year\":\"[1975]\",\"value\":\"\"},
	{\"year\":\"[1976]\",\"value\":\"\"},
	{\"year\":\"[1981]\",\"value\":\"\"},
	{\"year\":\"[1987]\",\"value\":\"\"},
	{\"year\":\"[1993]\",\"value\":\"\"},
	{\"year\":\"[1998]\",\"value\":\"\"},
	{\"year\":\"[1999]\",\"value\":\"\"},
	{\"year\":\"[2004]\",\"value\":\"N\",\"valueType\":\"String\",\"footnotes\":\"Non-relevant\",\"Nature\":\"C\",\"Source Type\":\"\",\"UnitMultiplier\":\"\",\"Unit\":\"PERCENT\",\"Management Level\":\"\",\"Observation Status\":\"A\",\"Geo Info Type\":\"\"},
	{\"year\":\"[2005]\",\"value\":\"N\",\"valueType\":\"String\",\"footnotes\":\"Non-relevant\",\"Nature\":\"C\",\"Source Type\":\"\",\"UnitMultiplier\":\"\",\"Unit\":\"PERCENT\",\"Management Level\":\"\",\"Observation Status\":\"A\",\"Geo Info Type\":\"\"},
	{\"year\":\"[2010]\",\"value\":\"N\",\"valueType\":\"String\",\"footnotes\":\"Non-relevant\",\"Nature\":\"C\",\"Source Type\":\"\",\"UnitMultiplier\":\"\",\"Unit\":\"PERCENT\",\"Management Level\":\"\",\"Observation Status\":\"A\",\"Geo Info Type\":\"\"},
	{\"year\":\"[2016]\",\"value\":\"N\",\"valueType\":\"String\",\"footnotes\":\"Non-relevant\",\"Nature\":\"C\",\"Source Type\":\"\",\"UnitMultiplier\":\"\",\"Unit\":\"PERCENT\",\"Management Level\":\"\",\"Observation Status\":\"A\",\"Geo Info Type\":\"\"}]"}}
```

## Example Clean Observation Format
The first few observations of `sspi_clean_api_data` are displayed below.   Putting all observations into this format is the goal of the compute routes.  
* Intermediates are not always required if the computation is very simple, i.e. if the `"RAW"` field is the only data that goes into the indicator.  If no intermediates are used, simply store an empty dictionary `{}` in that field. 
* Just to reiterate, the `_id` field is handled by MongoDB internally, and should not be touched or worried about by us.  

```python
[{"CountryCode":"AFG",
  "IndicatorCode":"BIODIV",
  "Intermediates":
	  {"ER_MRN_MPA":"N",
	   "ER_PTD_FRHWTR":"0",
	   "ER_PTD_TERR":"0"},   
  "RAW":"NaN",
  "YEAR":2004,
  "_id":{"$oid":"64b57d00d79438317daa3d8a"}},{"CountryCode":"AFG",
  "IndicatorCode":"BIODIV",
  "Intermediates":
	  {"ER_MRN_MPA":"N",
	   "ER_PTD_FRHWTR":"0",
	  "ER_PTD_TERR":"0"},
  "RAW":"NaN",
  "YEAR":2005,
  "_id":{"$oid":"64b57d00d79438317daa3d8b"}},{"CountryCode":"AFG",
  "IndicatorCode":"BIODIV",
  "Intermediates":
	{"ER_MRN_MPA":"N",
	 "ER_PTD_FRHWTR":"0",
	 "ER_PTD_TERR":"5.82179"},
 "RAW":"NaN",
 "YEAR":2010,
 "_id":{"$oid":"64b57d00d79438317daa3d8c"}},
 ...
]
```

## A note on style
Your functions should be *readable* and *concise*.  **Readability is absolutely more important than efficiency in this application**.  As such, it is really important that we avoid functions that are trying to do too much.   Below are two examples of an implementation , both of which solve the same task with almost exactly the same code.

### How not to do it
This block of code is unreadable and would take me an hour to parse through, even having written it myself.  This is prime example of complexity being the enemy.  Instead, we should practice *seperation of concerns*.

```python
def compute_biodiv():
	mongoQuery = {"collection-info.IndicatorCode": IndicatorCode}
    raw_data = parse_json(sspi_raw_api_data.find(mongoQuery))
	intermediate_obs_dict = {}
	for country in raw_data:
		geoAreaCode = format_m49_as_string(country["observation"]["geoAreaCode"])
		country_data = countries.get(numeric=geoAreaCode)
	if not country_data:
		continue
	series = country["observation"]["series"]
	annual_data_list = json.loads(country["observation"]["years"])
	COU = country_data.alpha_3
	if COU not in intermediate_obs_dict.keys():
		intermediate_obs_dict[COU] = {}
	for obs in annual_data_list:
		year = int(obs["year"][1:5])
		if obs["value"] == '':
			continue
		if year not in intermediate_obs_dict[COU].keys():
			intermediate_obs_dict[COU][year] = {}
		intermediate_obs_dict[COU][year][series] = obs["value"]
	final_data_list = []
	for cou in intermediate_obs_dict.keys():
		for year in intermediate_obs_dict[cou].keys():
			try:
				mean_across_series = sum([float(x) for x in intermediate_obs_dict[cou][year].values()])/3
			except ValueError:
				mean_across_series = "NaN"
			new_observation = {
				"CountryCode": cou,
				"IndicatorCode": "BIODIV",
				"YEAR": year,
				"RAW": mean_across_series,
				"Intermediates": intermediate_obs_dict[cou][year]
			}
			final_data_list.append(new_observation)
	return final_data_list
```

### How to do it
This is almost exactly the same code, but I've split the functionality up into smaller chunks wrapped in functions with descriptive names.  This offers a few benefits.  First of all, reading `compute_biodiv` becomes totally tractable.  And, if you find that something is wrong in `compute_biodiv`, you can easily figure out where it's going wrong by testing that each of these smaller component functions works correctly.  

```python
from sspi_flask_app.api.datasource.sdg import flatten_nested_dictionary_biodiv, extract_sdg_pivot_data_to_nested_dictionary

def compute_biodiv():
	if not raw_data_available("BIODIV"):
	        return "Data unavailable. Try running collect."
	    raw_data = fetch_raw_data("BIODIV")
	    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
	    # implement a computation function as an argument which can be adapted to different contexts
	    final_data_list = flatten_nested_dictionary_biodiv(intermediate_obs_dict)
	    # store the cleaned data in the database
	    sspi_clean_api_data.insert_many(final_data_list)
	    return f"Inserted {len(final_data_list)} observations into the database."

def raw_data_available(IndicatorCode):
    return bool(sspi_raw_api_data.find_one({"collection-info.IndicatorCode": IndicatorCode}))
```

Those smaller component functions are off to the side waiting in `datasource/sdg.py` and are also now much more readable because there's not too much going on in each of them.

```python
def extract_sdg_pivot_data_to_nested_dictionary(raw_sdg_pivot_data):
    intermediate_obs_dict = {}
    for country in raw_sdg_pivot_data:
        geoAreaCode = format_m49_as_string(country["observation"]["geoAreaCode"])
        country_data = countries.get(numeric=geoAreaCode)
        # make sure that the data corresponds to a valid country (gets rid of regional aggregates)
        if not country_data:
            continue
        series = country["observation"]["series"]
        annual_data_list = json.loads(country["observation"]["years"])
        COU = country_data.alpha_3
        # add the country to the dictionary if it's not there already
        if COU not in intermediate_obs_dict.keys():
            intermediate_obs_dict[COU] = {}
        # iterate through each of the annual observations and add the appropriate entry
        for obs in annual_data_list:
            year = int(obs["year"][1:5])
            if obs["value"] == '':
                continue
            if year not in intermediate_obs_dict[COU].keys():
                intermediate_obs_dict[COU][year] = {}
            intermediate_obs_dict[COU][year][series] = obs["value"]
    return intermediate_obs_dict
    
def flatten_nested_dictionary_biodiv(intermediate_obs_dict):
    final_data_list = []
    for cou in intermediate_obs_dict.keys():
        for year in intermediate_obs_dict[cou].keys():
            try:
                mean_across_series = sum([float(x) for x in intermediate_obs_dict[cou][year].values()])/3
            except ValueError:
                mean_across_series = "NaN"
            new_observation = {
                "CountryCode": cou,
                "IndicatorCode": "BIODIV",
                "YEAR": year,
                "RAW": mean_across_series,
                "Intermediates": intermediate_obs_dict[cou][year]
            }
            final_data_list.append(new_observation)
    return final_data_list
```
