from sspi_flask_app.api.api import format_m49_as_string

def test_m49_format():
    assert format_m49_as_string(5) == '005'
    assert format_m49_as_string(15) == '015'
    assert format_m49_as_string(150) == '150'