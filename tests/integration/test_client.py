import pytest
from pathlib import Path

from flask import url_for

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer"' in response.data
    # response = client.get(url_for('client_bp.home'))
    # assert response.status_code == 200

def test_data_page(client):
    response = client.get("/data")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer"' in response.data

def test_methodology_page(client):
    response = client.get("/methodology")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer"' in response.data

def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer"' in response.data

def test_contact_page(client):
    response = client.get("/contact")
    assert response.status_code == 200
    assert b'<header class="site-header">' in response.data
    assert b'<body>' in response.data
    assert b'<footer class="site-footer"' in response.data

CLIENT_STATIC_DIR = Path(__file__).resolve().parents[2] / "sspi_flask_app" / "client" / "static"


def test_should_name_the_working_paper_once_when_rendering_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"from 2018 working paper" not in response.data
    assert b"IRLE Working Paper #101-25 (Brown and Misko 2025)" in response.data


def test_should_spell_policies_correctly_when_rendering_2018_home_page(client):
    response = client.get("/2018")
    assert response.status_code == 200
    assert b"polcies" not in response.data
    assert b"each\n                        of measures" not in response.data
    assert b"from 2018 working paper" not in response.data
    assert b"IRLE Working Paper #101-25 (Brown and Misko 2025)" in response.data


def test_should_not_use_the_old_index_name_when_scanning_client_sources():
    offending_files = [
        str(path.relative_to(CLIENT_STATIC_DIR))
        for path in CLIENT_STATIC_DIR.rglob("*.js")
        if path.name != "script.js"
        and "dist" not in path.parts
        and "Social Policy and Progress Index" in path.read_text(encoding="utf-8")
    ]
    assert offending_files == []


def test_should_return_404_when_country_code_is_unknown(client):
    response = client.get("/data/country/ZZZ")
    assert response.status_code == 404
    assert b"ZZZ" in response.data
    assert b"<h1>404</h1>" in response.data


def test_should_return_404_when_country_code_is_not_three_letters(client):
    response = client.get("/data/country/not-a-country")
    assert response.status_code == 404


def test_should_return_404_when_country_detail_has_no_metadata(client, monkeypatch):
    from sspi_flask_app.models.database import sspi_metadata
    monkeypatch.setattr(sspi_metadata, "get_country_detail", lambda code: {})
    response = client.get("/data/country/USA")
    assert response.status_code == 404


def test_should_render_country_page_when_country_code_is_known_in_any_case(client):
    from sspi_flask_app.models.database import sspi_metadata
    if not sspi_metadata.get_country_detail("USA"):
        pytest.skip("local metadata has no CountryDetail for USA")
    response = client.get("/data/country/usa")
    assert response.status_code == 200
