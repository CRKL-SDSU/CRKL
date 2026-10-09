# Purpose: endpoints.py contains the API endpoints for the backend, which are used by the frontend to access the database

from typing import Any

import pymysql
from fastapi import APIRouter, HTTPException, Query, Request

# importing our fetch commands from db_management.py, which will be used to query our database
from db_management import fetch_all, fetch_one

# configuring our API router, which will be used to define the endpoints for our web server
router = APIRouter(prefix="/api/v1")

# defining the configuration for each resource, including the table name and primary key column"
RESOURCE_CONFIG = {
    "missions": ("missions", "mission_id"),
    "agencies": ("agencies", "agency_id"),
    "spacecraft": ("spacecraft", "spacecraft_id"),
    "launches": ("launches", "launch_id"),
}

# defining the columns to be searched for each resouce when a search query is provided
SEARCH_COLUMNS = {
    "missions": ("name", "description", "target_body", "status", "source_provider", "source_id"),
    "agencies": ("name", "abbrev", "country_code", "source_provider", "source_id"),
    "spacecraft": ("name", "spacecraft_type", "source_provider", "source_id"),
    "launches": ("name", "status", "source_provider", "source_id"),
}

# defining the related search queries for each resource, which will be used to search for related records in other tables
RELATED_SEARCH = {
    # writing a SQL query for each entity, which contains a subquery that checks for related records in other tables based on the search term
    "missions": (
        """EXISTS (
            SELECT 1
            FROM mission_agencies ma
            JOIN agencies a ON a.agency_id = ma.agency_id
            WHERE ma.mission_id = missions.mission_id
              AND (a.name LIKE %s ESCAPE '\\\\'
                   OR a.abbrev LIKE %s ESCAPE '\\\\'
                   OR a.country_code LIKE %s ESCAPE '\\\\')
        )
        OR EXISTS (
            SELECT 1
            FROM mission_spacecraft ms
            JOIN spacecraft s ON s.spacecraft_id = ms.spacecraft_id
            WHERE ms.mission_id = missions.mission_id
              AND (s.name LIKE %s ESCAPE '\\\\'
                   OR s.spacecraft_type LIKE %s ESCAPE '\\\\')
        )
        OR EXISTS (
            SELECT 1
            FROM mission_launches ml
            JOIN launches l ON l.launch_id = ml.launch_id
            WHERE ml.mission_id = missions.mission_id
              AND (l.name LIKE %s ESCAPE '\\\\'
                   OR l.status LIKE %s ESCAPE '\\\\'
                   OR l.source_id LIKE %s ESCAPE '\\\\')
        )""",
        ("a", "a", "a", "s", "s", "l", "l", "l"),
    ),
    "agencies": (
        """EXISTS (
            SELECT 1
            FROM mission_agencies ma
            JOIN missions m ON m.mission_id = ma.mission_id
            WHERE ma.agency_id = agencies.agency_id
              AND (m.name LIKE %s ESCAPE '\\\\'
                   OR m.description LIKE %s ESCAPE '\\\\'
                   OR m.target_body LIKE %s ESCAPE '\\\\'
                   OR m.status LIKE %s ESCAPE '\\\\')
        )""",
        ("m", "m", "m", "m"),
    ),
    "spacecraft": (
        """EXISTS (
            SELECT 1
            FROM mission_spacecraft ms
            JOIN missions m ON m.mission_id = ms.mission_id
            WHERE ms.spacecraft_id = spacecraft.spacecraft_id
              AND (m.name LIKE %s ESCAPE '\\\\'
                   OR m.description LIKE %s ESCAPE '\\\\'
                   OR m.target_body LIKE %s ESCAPE '\\\\'
                   OR m.status LIKE %s ESCAPE '\\\\')
        )""",
        ("m", "m", "m", "m"),
    ),
    "launches": (
        """EXISTS (
            SELECT 1
            FROM mission_launches ml
            JOIN missions m ON m.mission_id = ml.mission_id
            WHERE ml.launch_id = launches.launch_id
              AND (m.name LIKE %s ESCAPE '\\\\'
                   OR m.description LIKE %s ESCAPE '\\\\'
                   OR m.target_body LIKE %s ESCAPE '\\\\'
                   OR m.status LIKE %s ESCAPE '\\\\')
        )""",
        ("m", "m", "m", "m"),
    ),
}

# defining a database error handler that will be used to handle any databasee-releated errors that occur during API requests
def _database_error(error: pymysql.MySQLError) -> HTTPException:
    print(f"ERROR: Database query failed: {error}")
    return HTTPException(status_code=503, detail="Database unavailable")

# function that will generate pagination links for the API responses as a tuple, which is based on:
# the current request
# the limit, offset, and count parameters
# the search term
# related flags
def _pagination_links(
    request: Request,
    limit: int,
    offset: int,
    count: int,
    search: str,
    related: bool,
) -> tuple[str | None, str | None]:
    next_url = None
    previous_url = None
    # "if the sum of the offset and limit exceed our count, that means we've more records and should generate another page"
    if offset + limit < count:
        next_url = str(
            request.url.include_query_params(
                limit=limit, offset=offset + limit, search=search, related=str(related).lower()
            )
        )
    # "if the offset is greater than 0, that means we've previous records and should generate a previous page"
    if offset > 0:
        previous_url = str(
            request.url.include_query_params(
                limit=limit, offset=max(0, offset - limit), search=search, related=str(related).lower()
            )
        )
    return next_url, previous_url

# function that will list resources (missions, agencies, spacecraft, paunches) with pagination, search, and related filtering as a dictionary. This is based on:
# the resource type
# the request
# the limit, offset, and search parameters
# related flags
def _list_resource(
    resource: str,
    request: Request,
    limit: int,
    offset: int,
    search: str,
    related: bool,
) -> dict[str, Any]:
    table, id_column = RESOURCE_CONFIG[resource]
    search = search.strip()
    where = ""
    parameters: tuple[Any, ...] = ()

    # "if given a search, escape the search term to prevent SQL injection and construct the WHERE clause for the query"
    if search:
        escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions = [
            f"{column} LIKE %s ESCAPE '\\\\'" for column in SEARCH_COLUMNS[resource]
        ]
        parameters_list = [f"%{escaped_search}%" for _ in SEARCH_COLUMNS[resource]]

        # "if the search term is related, add the search conditions to the WHERE clause"
        if related:
            conditions.append(RELATED_SEARCH[resource][0])
            parameters_list.extend(
                f"%{escaped_search}%" for _ in RELATED_SEARCH[resource][1]
            )
        where = " WHERE (" + " OR ".join(conditions) + ")"
        parameters = tuple(parameters_list)

    # "try to fetch the count of records and the actual records from this database and make an exception for any potential database errors"
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

    # "if a count row was returned, set the count to the value of the count column, else set it to 0"
    count = int(count_row["count"]) if count_row else 0

    # generate our URLs (next and previous)
    next_url, previous_url = _pagination_links(
        request, limit, offset, count, search, related
    )
    return {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "results": results,
    }

# function that will get the details of a specific resource (missions, agencies, spacecraft, launches) as a dictionary. This is based on:
# the table name
# the primary key column name
# the record ID
# the relationship queries to fetch related records from other tables
def _get_detail(
    table: str, id_column: str, record_id: int, relationship_queries: list[tuple[str, str]]
) -> dict[str, Any]:

    # "try to fetch a record from the database and make an exception for any potential database errors"
    try:
        record = fetch_one(
            f"SELECT * FROM {table} WHERE {id_column} = %s", (record_id,)
        )

        # "if no record was found, raise an HTTPException"
        if record is None:
            raise HTTPException(status_code=404, detail="Resource not found")

        # "for each relationship query, fetch the related records and add them to the record dictionary"
        for field, query in relationship_queries:
            record[field] = fetch_all(query, (record_id,))
        return record
    except HTTPException:
        raise
    except pymysql.MySQLError as error:
        raise _database_error(error) from error


# ===== API ENDPOINTS ===== #

# API endpoint for displaying a list of missions
@router.get("/missions", summary="List missions")
def list_missions(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
    related: bool = Query(default=True),
) -> dict[str, Any]:
    return _list_resource("missions", request, limit, offset, search, related)

# API endpoint for specifying mission details, which can be customized to include related records from the other tables (agencies, spacecraft, launches)
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

# API endpoint for displaying a list of agencies
@router.get("/agencies", summary="List agencies")
def list_agencies(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
    related: bool = Query(default=True),
) -> dict[str, Any]:
    return _list_resource("agencies", request, limit, offset, search, related)

# API endpoint for specifying agency details, which can be customized to include related records from the missions table
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

# API endpoint for displaying a list of spacecraft
@router.get("/spacecraft", summary="List spacecraft")
def list_spacecraft(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
    related: bool = Query(default=True),
) -> dict[str, Any]:
    return _list_resource("spacecraft", request, limit, offset, search, related)

# API endpoint for specifying spacecraft details, which can be customized to include related records from the missions table
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

# API endpoint for displaying a list of launches
@router.get("/launches", summary="List launches")
def list_launches(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str = Query(default=""),
    related: bool = Query(default=True),
) -> dict[str, Any]:
    return _list_resource("launches", request, limit, offset, search, related)

# API endpoint for specifying launch details, which can be customized to include related records from the missions table
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
