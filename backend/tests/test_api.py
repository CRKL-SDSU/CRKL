import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "code"))

from main import app


client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "We are LIVE!"


def test_list_missions_defaults_to_related_search() -> None:
    with patch("endpoints.fetch_one", return_value={"count": 1}), patch(
        "endpoints.fetch_all", return_value=[{"mission_id": 1, "name": "Mars Mission"}]
    ) as fetch_all:
        response = client.get("/api/v1/missions?search=Mars")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    query, parameters = fetch_all.call_args.args
    assert "mission_launches" in query
    assert len(parameters) == 16


def test_list_missions_can_disable_related_search() -> None:
    with patch("endpoints.fetch_one", return_value={"count": 1}), patch(
        "endpoints.fetch_all", return_value=[{"mission_id": 1, "name": "Mars Mission"}]
    ) as fetch_all:
        response = client.get("/api/v1/missions?search=Mars&related=false")

    assert response.status_code == 200
    query, parameters = fetch_all.call_args.args
    assert "mission_launches" not in query
    assert len(parameters) == 8


def test_pagination_links_preserve_related_search_mode() -> None:
    with patch("endpoints.fetch_one", return_value={"count": 3}), patch(
        "endpoints.fetch_all", return_value=[]
    ):
        response = client.get(
            "/api/v1/launches?search=NASA&related=false&limit=2"
        )

    assert response.status_code == 200
    assert "related=false" in response.json()["next"]
