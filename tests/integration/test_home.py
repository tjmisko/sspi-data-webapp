import pytest
from flask import url_for

def test_home_load(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer">' in response.data
    response = client.get(url_for('home'))
    assert response.status_code == 200
    assert b'home.html' in response.data