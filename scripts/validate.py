import requests
import pandas
import json

base_url = 'http://localhost:5000'
home_dir = '/home/tjmisko/Projects/SSPI/sspi-data-webapp/'
sheet_data = pandas.read_csv(home_dir + './local/SSPIMainDataV3.csv',
                             skiprows=1)


def split_last(in_string: str):
    split_index = in_string.rindex("_")
    return in_string[0:split_index], in_string[split_index+1:]


def process_sheet_data(sheet_data):
    sheet_data = json.loads(str(sheet_data.to_json(orient='records')))
    sheet_data_long = []
    for cou_obs in sheet_data:
        output_dict = {}
        country = cou_obs["Country"]
        country_code = cou_obs["Country Code"]
        for key, value in cou_obs.items():
            if key in ["Country", "Country Code"]:
                continue
            obs_name, obs_type = split_last(key)
            if "_" in obs_name:
                obs_name = obs_name.split("_", 1)[1]
            if obs_name not in output_dict.keys():
                output_dict[obs_name] = []
            output_dict[obs_name].append({obs_type: value})
        for key, value in output_dict.items():
            new_long_obs = {
                "Country": country,
                "CountryCode": country_code,
                "ItemCode": key,
            }
            for obs in value:
                new_long_obs.update(obs)
            sheet_data_long.append(new_long_obs)
    return sheet_data_long


sheet_data_long = process_sheet_data(sheet_data)
database_data = requests.get(
    base_url + '/api/v1/query/sspi_static_rank_data').json()
# database_data_filtered = [
#     x for x in database_data if len(x['IName']) != 6]
# print(json.dumps(database_data))
# print(json.dumps(sheet_data_long))


def find_discrepancies(sheet_data_long, database_data, tol=0.01):
    def lookup_data(cou, icode, database_data):
        for data_row in database_data:
            print(data_row)
            if data_row["CCode"] == cou and data_row["ICode"] == icode:
                return data_row

    discrepancies = []
    for sheet_row in sheet_data_long:
        data_row = lookup_data(
            sheet_row["CountryCode"], sheet_row["ItemCode"], database_data)
        if not data_row:
            message = "Data not found in database for "
            raise Exception(message + f"{sheet_row['CountryCode']} {sheet_row['ItemCode']}")
        score_mismatch = abs(float(sheet_row["SCORE"]) - float(data_row["Score"])) > tol
        rank_mismatch = abs(int(sheet_row["RANK"]) - int(data_row["Rank"])) > tol
        if "YEAR" in sheet_row.keys():
            year_mismatch = abs(int(sheet_row["YEAR"]) - int(data_row["Year"])) > tol
        else:
            year_mismatch = False
        if any([score_mismatch, rank_mismatch, year_mismatch]):
            discrepancies.append(
                {"sheet": sheet_row, "database": data_row}
            )
    return discrepancies


discrepancies = find_discrepancies(sheet_data_long, database_data)
if discrepancies:
    print(json.dumps(discrepancies))
else:
    print("No discrepancies found")
