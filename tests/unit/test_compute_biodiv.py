from sspi_flask_app.api.source_utilities.sdg import flatten_nested_dictionary_biodiv, extract_sdg_pivot_data_to_nested_dictionary
from sspi_flask_app.api.sspi.compute import fetch_raw_data
import json
import math

def test_extract():
    test_data = fetch_raw_data("BIODIV")[0:2]
    nested_dict = extract_sdg_pivot_data_to_nested_dictionary(test_data)
    assert "AFG" in nested_dict.keys()
    assert "ALB" in nested_dict.keys()
    assert "ER_MRN_MPA" in nested_dict["AFG"][2010].keys()
    assert "N" in nested_dict["AFG"][2010].values()

def test_flatten():
    test_data = {"USA": {2018: {"a": 1, "b": 2, "c": 3}, 
                         2019: {"d": 4, "e": 5, "f": 6}},
                 "CHN": {2018: {"a": 1, "b": 2, "c": "N"},
                         2019: {"d": 3, "e": 4, "f": 5}},
                 "RUS": {2018: {},
                         2019: {"a": 1}}}
    final_data_list = flatten_nested_dictionary_biodiv(test_data)
    assert len(final_data_list) == 6
    assert final_data_list[0]["CountryCode"] == "USA"
    assert final_data_list[0]["RAW"] == 2
    assert final_data_list[2]["CountryCode"] == "CHN"
    assert math.isnan(final_data_list[2]["RAW"])
    assert final_data_list[4]["CountryCode"] == "RUS"
    assert final_data_list[4]["RAW"] == 0 
    assert final_data_list[5]["RAW"] == 1/3
                 
    