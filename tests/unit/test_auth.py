
def test_login(client):
    response = client.get("/login")
    assert response.status_code == 200
