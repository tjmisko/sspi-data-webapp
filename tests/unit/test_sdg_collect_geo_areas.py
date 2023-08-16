# Use a python "relative import" to pull in the function you want to test
from sspi_flask_app.api.datasource.sdg import collectAvailableGeoAreas
# N.B. statement above uses . instead of / to capture the filepath
# It's saying "look in the sspi_flask_app folder, then in the  api folder, then 
# in the datasource folder, then in the SDG file"

def test_collect_geo_area():
    """
    GIVEN an SDG Indicator Code
    WHEN our SSPI collection api is called
    THEN hits the SDG API and returns a list of strings 
    representing the M49 codes of countries with data for the indicator
    """
    #lst = collectAvailableGeoAreas("15.1.2")
    print(lst)
    # check that the return type is correct
    assert type(lst[1]) == type("string")
    # check that the list is not empty
    assert len(lst) != 0
    # check that the list contains United States, which we know is in the dataset
    assert "840" in lst
    # check that the list contains Argentina, , which we know is in the dataset
    assert "032" in lst
