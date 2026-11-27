# Purpose: endpoints.py contains the API endpoints for the backend, which are used by the frontend to access the database

import json
from typing import Any

import pymysql
from fastapi import APIRouter, Body, HTTPException, Query, Request

# importing our fetch commands from db_management.py, which will be used to query our database
from db_management import database_connection, fetch_all, fetch_one

# importing the Gmail-style search query parser
from search_query import And, Node, Not, Or, QueryError, Tag, Text, normalize_tag, parse_query

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

# defining how a tag:name term matches each resource
# tags belong to missions, so the other resources match through the mission junction tables
TAG_SEARCH = {
    "missions": """EXISTS (
            SELECT 1
            FROM mission_tags mt
            JOIN tags t ON t.tag_id = mt.tag_id
            WHERE mt.mission_id = missions.mission_id AND t.name = %s
        )""",
    "agencies": """EXISTS (
            SELECT 1
            FROM mission_agencies ma
            JOIN mission_tags mt ON mt.mission_id = ma.mission_id
            JOIN tags t ON t.tag_id = mt.tag_id
            WHERE ma.agency_id = agencies.agency_id AND t.name = %s
        )""",
    "spacecraft": """EXISTS (
            SELECT 1
            FROM mission_spacecraft ms
            JOIN mission_tags mt ON mt.mission_id = ms.mission_id
            JOIN tags t ON t.tag_id = mt.tag_id
            WHERE ms.spacecraft_id = spacecraft.spacecraft_id AND t.name = %s
        )""",
    "launches": """EXISTS (
            SELECT 1
            FROM mission_launches ml
            JOIN mission_tags mt ON mt.mission_id = ml.mission_id
            JOIN tags t ON t.tag_id = mt.tag_id
            WHERE ml.launch_id = launches.launch_id AND t.name = %s
        )""",
}

# the tags of each mission, returned as a JSON array alongside the mission's columns
MISSION_TAGS_COLUMN = """(
            SELECT JSON_ARRAYAGG(JSON_OBJECT('tag_id', t.tag_id, 'name', t.name))
            FROM mission_tags mt
            JOIN tags t ON t.tag_id = mt.tag_id
            WHERE mt.mission_id = missions.mission_id
        ) AS tags"""

# the name of each launch's launch service provider, returned alongside the launch's columns
LAUNCH_PROVIDER_COLUMN = """(
            SELECT a.name
            FROM agencies a
            WHERE a.agency_id = launches.launch_service_provider_id
        ) AS launch_service_provider"""

# the extra columns each resource returns alongside its own columns
EXTRA_COLUMNS = {
    "missions": MISSION_TAGS_COLUMN,
    "launches": LAUNCH_PROVIDER_COLUMN,
}

# the maximum number of tags a single mission can have
MAX_TAGS_PER_MISSION = 10

# the tags of one mission, sorted by name
MISSION_TAGS_QUERY = """SELECT t.tag_id, t.name
                   FROM tags t
                   JOIN mission_tags mt ON mt.tag_id = t.tag_id
                   WHERE mt.mission_id = %s
                   ORDER BY t.name"""

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

# function that will build the SQL condition for one plain search term (a word or a "quoted phrase")
def _text_condition(value: str, resource: str, related: bool) -> tuple[str, list[Any]]:
    # escape the LIKE wildcards so they are searched for literally
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    conditions = [f"{column} LIKE %s ESCAPE '\\\\'" for column in SEARCH_COLUMNS[resource]]
    parameters: list[Any] = [pattern for _ in SEARCH_COLUMNS[resource]]

    # "if related search is on, also match the term in linked records"
    if related:
        conditions.append(RELATED_SEARCH[resource][0])
        parameters.extend(pattern for _ in RELATED_SEARCH[resource][1])
    return "(" + " OR ".join(conditions) + ")", parameters


# function that will turn a parsed search query into a parameterized SQL condition
def _search_condition(node: Node, resource: str, related: bool) -> tuple[str, tuple[Any, ...]]:
    def build(current: Node) -> tuple[str, list[Any]]:
        if isinstance(current, Text):
            return _text_condition(current.value, resource, related)
        if isinstance(current, Tag):
            return TAG_SEARCH[resource], [current.name]
        if isinstance(current, Not):
            sql, parameters = build(current.child)
            return f"NOT {sql}", parameters
        joiner = " AND " if isinstance(current, And) else " OR "
        parts = [build(child) for child in current.children]
        return (
            "(" + joiner.join(sql for sql, _ in parts) + ")",
            [parameter for _, parameters in parts for parameter in parameters],
        )

    sql, parameters = build(node)
    return sql, tuple(parameters)


# function that will turn the JSON array of tags from MySQL into a sorted list
def _decode_tags(value: Any) -> list[dict[str, Any]]:
    if not value:
        return []
    tags = json.loads(value) if isinstance(value, (str, bytes)) else value
    return sorted(tags, key=lambda tag: tag["name"])


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

    # "try to parse the search query, and reject malformed queries with a 400 error"
    try:
        expression = parse_query(search)
    except QueryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    # "if given a search, build the WHERE clause from the parsed query"
    if expression is not None:
        condition, parameters = _search_condition(expression, resource, related)
        where = f" WHERE {condition}"

    # missions also return their tags, and launches their provider's name, so result cards can show them
    columns = f"*, {EXTRA_COLUMNS[resource]}" if resource in EXTRA_COLUMNS else "*"

    # "try to fetch the count of records and the actual records from this database and make an exception for any potential database errors"
    try:
        count_row = fetch_one(
            f"SELECT COUNT(*) AS count FROM {table}{where}", parameters
        )
        results = fetch_all(
            f"SELECT {columns} FROM {table}{where} ORDER BY {id_column} LIMIT %s OFFSET %s",
            parameters + (limit, offset),
        )
    except pymysql.MySQLError as error:
        raise _database_error(error) from error

    if resource == "missions":
        for record in results:
            record["tags"] = _decode_tags(record.get("tags"))

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
    table: str,
    id_column: str,
    record_id: int,
    relationship_queries: list[tuple[str, str]],
    columns: str = "*",
) -> dict[str, Any]:

    # "try to fetch a record from the database and make an exception for any potential database errors"
    try:
        record = fetch_one(
            f"SELECT {columns} FROM {table} WHERE {id_column} = %s", (record_id,)
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
            ("tags", MISSION_TAGS_QUERY),
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
        columns=f"*, {LAUNCH_PROVIDER_COLUMN}",
    )


# ===== TAG ENDPOINTS ===== #

# API endpoint for listing tags (used for suggestions while typing a tag)
@router.get("/tags", summary="List tags")
def list_tags(
    search: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    prefix = " ".join(search.split()).lower()
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    # "try to fetch the tags that start with the search text, most used first"
    try:
        results = fetch_all(
            """SELECT t.tag_id, t.name, COUNT(mt.mission_id) AS mission_count
               FROM tags t
               LEFT JOIN mission_tags mt ON mt.tag_id = t.tag_id
               WHERE t.name LIKE %s ESCAPE '\\\\'
               GROUP BY t.tag_id, t.name
               ORDER BY mission_count DESC, t.name
               LIMIT %s""",
            (f"{escaped}%", limit),
        )
    except pymysql.MySQLError as error:
        raise _database_error(error) from error
    return {"results": results}


# API endpoint for adding a tag to a mission; the tag is created if it doesn't exist yet
@router.post("/missions/{id}/tags", status_code=201, summary="Add a tag to a mission")
def add_mission_tag(id: int, name: str = Body(embed=True)) -> dict[str, Any]:
    # "try to normalize the tag name, and reject invalid names with a 400 error"
    try:
        tag_name = normalize_tag(name)
    except QueryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    # "try to add the tag in one transaction, and make an exception for any database errors"
    try:
        with database_connection() as connection:
            try:
                connection.begin()
                with connection.cursor() as cursor:
                    # lock the mission row so two requests can't both pass the tag limit check
                    cursor.execute(
                        "SELECT mission_id FROM missions WHERE mission_id = %s FOR UPDATE", (id,)
                    )
                    if cursor.fetchone() is None:
                        raise HTTPException(status_code=404, detail="Resource not found")

                    # count the mission's other tags, so re-adding a tag it already has never hits the limit
                    cursor.execute(
                        """SELECT COUNT(*) AS count
                           FROM mission_tags mt
                           JOIN tags t ON t.tag_id = mt.tag_id
                           WHERE mt.mission_id = %s AND t.name <> %s""",
                        (id, tag_name),
                    )
                    if cursor.fetchone()["count"] >= MAX_TAGS_PER_MISSION:
                        raise HTTPException(
                            status_code=409,
                            detail=f"A mission can have at most {MAX_TAGS_PER_MISSION} tags.",
                        )

                    # create the tag, or reuse the existing one with the same name
                    cursor.execute(
                        """INSERT INTO tags (name) VALUES (%s)
                           ON DUPLICATE KEY UPDATE tag_id = LAST_INSERT_ID(tag_id)""",
                        (tag_name,),
                    )
                    tag_id = cursor.lastrowid

                    # link it to the mission; adding a tag the mission already has is a no-op
                    cursor.execute(
                        "INSERT IGNORE INTO mission_tags (mission_id, tag_id) VALUES (%s, %s)",
                        (id, tag_id),
                    )
                    cursor.execute(MISSION_TAGS_QUERY, (id,))
                    tags = list(cursor.fetchall())
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    except pymysql.MySQLError as error:
        raise _database_error(error) from error
    return {"tags": tags}


# API endpoint for removing a tag from a mission; a tag no mission uses anymore is deleted
@router.delete("/missions/{id}/tags/{tag_id}", summary="Remove a tag from a mission")
def remove_mission_tag(id: int, tag_id: int) -> dict[str, Any]:
    # "try to remove the tag in one transaction, and make an exception for any database errors"
    try:
        with database_connection() as connection:
            try:
                connection.begin()
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM mission_tags WHERE mission_id = %s AND tag_id = %s",
                        (id, tag_id),
                    )
                    if cursor.rowcount == 0:
                        raise HTTPException(status_code=404, detail="Resource not found")

                    cursor.execute(
                        """DELETE FROM tags
                           WHERE tag_id = %s
                             AND NOT EXISTS (SELECT 1 FROM mission_tags WHERE tag_id = %s)""",
                        (tag_id, tag_id),
                    )
                    cursor.execute(MISSION_TAGS_QUERY, (id,))
                    tags = list(cursor.fetchall())
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    except pymysql.MySQLError as error:
        raise _database_error(error) from error
    return {"tags": tags}
