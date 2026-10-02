from typing import Any

import pymysql
from fastapi import APIRouter, HTTPException, Query, Request

from db_management import fetch_all, fetch_one


router = APIRouter(prefix="/api/v1")

RESOURCE_CONFIG = {
    "missions": ("missions", "mission_id"),
    "agencies": ("agencies", "agency_id"),
    "spacecraft": ("spacecraft", "spacecraft_id"),
    "launches": ("launches", "launch_id"),
}
SEARCH_COLUMNS = {
    "missions": ("name", "description", "target_body", "status", "source_provider", "source_id"),
    "agencies": ("name", "abbrev", "country_code", "source_provider", "source_id"),
    "spacecraft": ("name", "spacecraft_type", "source_provider", "source_id"),
    "launches": ("name", "status", "source_provider", "source_id"),
}


def _database_error(error: pymysql.MySQLError) -> HTTPException:
    print(f"ERROR: Database query failed: {error}")
    return HTTPException(status_code=503, detail="Database unavailable")


def _pagination_links(
    request: Request, limit: int, offset: int, count: int, search: str
) -> tuple[str | None, str | None]:
    next_url = None
    previous_url = None
    if offset + limit < count:
        next_url = str(
            request.url.include_query_params(
                limit=limit, offset=offset + limit, search=search
            )
        )
    if offset > 0:
        previous_url = str(
            request.url.include_query_params(
                limit=limit, offset=max(0, offset - limit), search=search
            )
        )
    return next_url, previous_url


def _list_resource(
    resource: str, request: Request, limit: int, offset: int, search: str
) -> dict[str, Any]:
    table, id_column = RESOURCE_CONFIG[resource]
    search = search.strip()
    where = ""
    parameters: tuple[Any, ...] = ()
    if search:
        escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where = " WHERE " + " OR ".join(
            f"{column} LIKE %s ESCAPE '\\\\'" for column in SEARCH_COLUMNS[resource]
        )
        parameters = tuple(f"%{escaped_search}%" for _ in SEARCH_COLUMNS[resource])
    try:
        count_row = fetch_one(
            f"SELECT COUNT(*) AS count FROM {table}{where}", parameters
        )
        results = fetch_all(
            f"SELECT * FROM {table}{where} ORDER BY {id_column} LIMIT %s OFFSET %s",
            parameters + (limit, offset),
        )
    except pymysql.MySQLError as error:
        raise _database_error(error) from error

    count = int(count_row["count"]) if count_row else 0
    next_url, previous_url = _pagination_links(request, limit, offset, count, search)
    return {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "results": results,
    }


def _get_detail(
    table: str, id_column: str, record_id: int, relationship_queries: list[tuple[str, str]]
) -> dict[str, Any]:
    try:
        record = fetch_one(
            f"SELECT * FROM {table} WHERE {id_column} = %s", (record_id,)
        )
        if record is None:
            raise HTTPException(status_code=404, detail="Resource not found")
        for field, query in relationship_queries:
            record[field] = fetch_all(query, (record_id,))
        return record
    except HTTPException:
        raise
    except pymysql.MySQLError as error:
        raise _database_error(error) from error


@router.get("/missions", summary="List missions")
def list_missions(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
) -> dict[str, Any]:
    return _list_resource("missions", request, limit, offset, search)


@router.get("/missions/{id}", summary="Get mission details")
def get_mission(id: int) -> dict[str, Any]:
    return _get_detail(
        "missions",
        "mission_id",
        id,
        [
            (
                "agencies",
                """SELECT a.*, ma.role
                   FROM agencies a
                   JOIN mission_agencies ma ON ma.agency_id = a.agency_id
                   WHERE ma.mission_id = %s
                   ORDER BY a.agency_id""",
            ),
            (
                "spacecraft",
                """SELECT s.*
                   FROM spacecraft s
                   JOIN mission_spacecraft ms ON ms.spacecraft_id = s.spacecraft_id
                   WHERE ms.mission_id = %s
                   ORDER BY s.spacecraft_id""",
            ),
            (
                "launches",
                """SELECT l.*
                   FROM launches l
                   JOIN mission_launches ml ON ml.launch_id = l.launch_id
                   WHERE ml.mission_id = %s
                   ORDER BY l.launch_id""",
            ),
        ],
    )


@router.get("/agencies", summary="List agencies")
def list_agencies(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
) -> dict[str, Any]:
    return _list_resource("agencies", request, limit, offset, search)


@router.get("/agencies/{id}", summary="Get agency details")
def get_agency(id: int) -> dict[str, Any]:
    return _get_detail(
        "agencies",
        "agency_id",
        id,
        [
            (
                "missions",
                """SELECT m.*, ma.role
                   FROM missions m
                   JOIN mission_agencies ma ON ma.mission_id = m.mission_id
                   WHERE ma.agency_id = %s
                   ORDER BY m.mission_id""",
            )
        ],
    )


@router.get("/spacecraft", summary="List spacecraft")
def list_spacecraft(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
) -> dict[str, Any]:
    return _list_resource("spacecraft", request, limit, offset, search)


@router.get("/spacecraft/{id}", summary="Get spacecraft details")
def get_spacecraft(id: int) -> dict[str, Any]:
    return _get_detail(
        "spacecraft",
        "spacecraft_id",
        id,
        [
            (
                "missions",
                """SELECT m.*
                   FROM missions m
                   JOIN mission_spacecraft ms ON ms.mission_id = m.mission_id
                   WHERE ms.spacecraft_id = %s
                   ORDER BY m.mission_id""",
            )
        ],
    )


@router.get("/launches", summary="List launches")
def list_launches(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
) -> dict[str, Any]:
    return _list_resource("launches", request, limit, offset, search)


@router.get("/launches/{id}", summary="Get launch details")
def get_launch(id: int) -> dict[str, Any]:
    return _get_detail(
        "launches",
        "launch_id",
        id,
        [
            (
                "missions",
                """SELECT m.*
                   FROM missions m
                   JOIN mission_launches ml ON ml.mission_id = m.mission_id
                   WHERE ml.launch_id = %s
                   ORDER BY m.mission_id""",
            )
        ],
    )
