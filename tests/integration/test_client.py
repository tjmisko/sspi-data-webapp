from flask import url_for

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer">' in response.data
    # response = client.get(url_for('client_bp.home'))
    # assert response.status_code == 200

def test_data_page(client):
    response = client.get("/data")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer">' in response.data

def test_methodology_page(client):
    response = client.get("/methodology")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer">' in response.data

def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer">' in response.data

def test_contact_page(client):
    response = client.get("/contact")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer">' in response.data
