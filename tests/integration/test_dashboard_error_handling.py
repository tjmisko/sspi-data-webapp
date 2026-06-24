"""Regression tests for app-level error handling and dashboard 404 guards.

Covers issue #266 (content-negotiated error handlers) and issue #896
(dashboard endpoints used to raise 500s on unknown item/dataset codes because
``get_item_detail``/``get_dataset_detail`` return error/empty dicts that were
indexed directly).
"""


def test_panel_score_unknown_item_code_returns_json_404(client):
    """An unknown item code on /panel/score should 404 with JSON, not 500 (#896)."""
    response = client.get("/api/v1/panel/score/NOTACODE")
    assert response.status_code == 404
    assert response.is_json
    assert "error" in response.get_json()


def test_panel_dataset_unknown_code_returns_json_404(client):
    """An unknown dataset code on /panel/dataset should 404 with JSON, not 500 (#896)."""
    response = client.get("/api/v1/panel/dataset/NOTACODE")
    assert response.status_code == 404
    assert response.is_json
    assert "error" in response.get_json()


def test_unknown_api_route_returns_json_404(client):
    """Unknown routes under /api should be content-negotiated to JSON (#266)."""
    response = client.get("/api/v1/this/route/does/not/exist")
    assert response.status_code == 404
    assert response.is_json
    assert "error" in response.get_json()
