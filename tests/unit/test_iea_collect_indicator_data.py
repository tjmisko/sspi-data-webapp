from sspi_flask_app.api.source_utilities.iea import collect_IEA_indicator_data

def test_collect_indicator_data():
    lst = collect_IEA_indicator_data('TESbySource')
    print (lst)

    # check that the return type is correct
    assert type(lst[1]) == type("string")
    # check that the list is not empty
    assert len(lst) != 0
    # check that the list contains United States, which we know is in the dataset
    assert "840" in lst
    # check that the list contains Argentina, , which we know is in the dataset
    assert "032" in lst

def test_iea_endpoint(client):
    res = client.get("/collect/indicator=TESbyS")
    assert type(res) == type("")