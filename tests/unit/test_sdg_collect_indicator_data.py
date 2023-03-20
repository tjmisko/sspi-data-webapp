from sspi_flask_app.api.source_utilities.sdg import collectSDGIndicatorData

def test_collect_indicator_data():
    """
    This set of tests is unfinished!
    
    GIVEN an SDG Indicator Code
    WHEN our SSPI collection api is called
    THEN hits the SDG API and returns all of the available data for our 
    """
    json_data = collectSDGIndicatorData("15.1.2")
    print(json_data)
    # check that the return type is a list
    assert type(json_data) == type([])
    # check that the return type of each element of the list is a dictionary
    assert type(json_data[0]) == type({})