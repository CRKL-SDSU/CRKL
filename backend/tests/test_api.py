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


def test_launch_detail_includes_related_missions() -> None:
    with patch(
        "endpoints.fetch_one",
        return_value={"launch_id": 7, "name": "Test Launch"},
    ), patch(
        "endpoints.fetch_all",
        return_value=[{"mission_id": 3, "name": "Test Mission"}],
    ) as fetch_all:
        response = client.get("/api/v1/launches/7")

    assert response.status_code == 200
    assert response.json()["missions"] == [
        {"mission_id": 3, "name": "Test Mission"}
    ]
    assert fetch_all.call_args.args[1] == (7,)


def test_launches_return_their_launch_service_provider_name() -> None:
    with patch("endpoints.fetch_one", return_value={"count": 1}), patch(
        "endpoints.fetch_all", return_value=[]
    ) as fetch_all:
        client.get("/api/v1/launches")
    assert "AS launch_service_provider" in fetch_all.call_args.args[0]

    with patch(
        "endpoints.fetch_one", return_value={"launch_id": 7, "launch_service_provider": "NASA"}
    ) as fetch_one, patch("endpoints.fetch_all", return_value=[]):
        response = client.get("/api/v1/launches/7")
    assert "AS launch_service_provider" in fetch_one.call_args.args[0]
    assert response.json()["launch_service_provider"] == "NASA"


def test_detail_returns_not_found_for_missing_record() -> None:
    with patch("endpoints.fetch_one", return_value=None):
        response = client.get("/api/v1/missions/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Resource not found"


def test_search_supports_tags_and_operators() -> None:
    with patch("endpoints.fetch_one", return_value={"count": 0}), patch(
        "endpoints.fetch_all", return_value=[]
    ) as fetch_all:
        response = client.get(
            "/api/v1/agencies", params={"search": "tag:Moon -NASA", "related": "false"}
        )

    assert response.status_code == 200
    query, parameters = fetch_all.call_args.args
    assert "mission_tags" in query
    assert " AND NOT " in query
    assert parameters[0] == "moon"
    assert parameters[1] == "%NASA%"


def test_excluded_words_keep_records_with_empty_columns() -> None:
    # real missions have no status (NULL); "-word" must not drop them
    with patch("endpoints.fetch_one", return_value={"count": 0}), patch(
        "endpoints.fetch_all", return_value=[]
    ) as fetch_all:
        client.get("/api/v1/missions", params={"search": "apollo -soyuz"})

    query = fetch_all.call_args.args[0]
    assert "NOT COALESCE((" in query
    assert query.count("NOT ") == 1


def test_malformed_search_returns_bad_request() -> None:
    response = client.get("/api/v1/missions", params={"search": "(mars"})

    assert response.status_code == 400
    assert "')'" in response.json()["detail"]


def test_mission_list_returns_sorted_tags() -> None:
    row = {
        "mission_id": 1,
        "name": "Lunar Scout",
        "tags": '[{"tag_id": 6, "name": "radar"}, {"tag_id": 1, "name": "moon"}]',
    }
    with patch("endpoints.fetch_one", return_value={"count": 1}), patch(
        "endpoints.fetch_all", return_value=[row]
    ):
        response = client.get("/api/v1/missions")

    assert response.status_code == 200
    assert [tag["name"] for tag in response.json()["results"][0]["tags"]] == ["moon", "radar"]


class FakeCursor:
    def __init__(self, results: list) -> None:
        self.results = results
        self.statements: list[tuple[str, tuple]] = []
        self.lastrowid = 4
        self.rowcount = 1

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def execute(self, query: str, parameters: tuple = ()) -> None:
        self.statements.append((query, parameters))

    def fetchone(self) -> object:
        return self.results.pop(0)

    def fetchall(self) -> object:
        return self.results.pop(0)


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False

    def begin(self) -> None:
        pass

    def cursor(self) -> FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def _fake_database(connection: FakeConnection):
    from contextlib import contextmanager

    @contextmanager
    def database_connection():
        yield connection

    return database_connection


def test_add_tag_normalizes_the_name() -> None:
    cursor = FakeCursor([{"mission_id": 1}, {"count": 0}, [{"tag_id": 4, "name": "deep space"}]])
    connection = FakeConnection(cursor)
    with patch("endpoints.database_connection", _fake_database(connection)):
        response = client.post("/api/v1/missions/1/tags", json={"name": "  Deep  SPACE "})

    assert response.status_code == 201
    assert response.json()["tags"] == [{"tag_id": 4, "name": "deep space"}]
    assert ("deep space",) in [parameters for _, parameters in cursor.statements]
    assert connection.committed


def test_add_tag_rejects_invalid_names() -> None:
    response = client.post("/api/v1/missions/1/tags", json={"name": "<b>"})

    assert response.status_code == 400


def test_add_tag_enforces_the_limit() -> None:
    cursor = FakeCursor([{"mission_id": 1}, {"count": 10}])
    connection = FakeConnection(cursor)
    with patch("endpoints.database_connection", _fake_database(connection)):
        response = client.post("/api/v1/missions/1/tags", json={"name": "moon"})

    assert response.status_code == 409
    assert connection.rolled_back


def test_remove_missing_tag_returns_not_found() -> None:
    cursor = FakeCursor([])
    cursor.rowcount = 0
    connection = FakeConnection(cursor)
    with patch("endpoints.database_connection", _fake_database(connection)):
        response = client.delete("/api/v1/missions/1/tags/99")

    assert response.status_code == 404
    assert connection.rolled_back
