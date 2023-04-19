
def test_download_params(client):
    response = client.get("/download")
    assert b'{"error": "No parameters provided"}' in response.data