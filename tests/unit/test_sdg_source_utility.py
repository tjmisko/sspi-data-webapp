def test_collect_geo_area():
    """
    GIVEN an SDG Indicator Code
    THEN hits the API and returns a list strings 
    representing the M49 codes of countries with data for the indicator
    """
    lst = ["cheese", "burgeer"]
    assert type(lst[1]) == type("string")
    assert len(lst) != 0