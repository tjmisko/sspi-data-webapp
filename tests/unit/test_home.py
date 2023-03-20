
def test_home_links(client):
    response = client.get("/")
    assert b'<h1 class="site-title"> Sustainable and Shared-Prosperity Index </h1>' in response.data