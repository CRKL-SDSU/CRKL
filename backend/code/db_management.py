import os
from contextlib import contextmanager
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

from config import CONFIG


@contextmanager
def database_connection() -> Iterator[pymysql.connections.Connection]:
    database = CONFIG["database"]
    connection = pymysql.connect(
        host=database["host"],
        user=database["user"],
        password=os.getenv("CRKL_MYSQL_PASSWORD", database["password"]),
        database=database["name"],
        port=int(database["port"]),
        cursorclass=DictCursor,
        connect_timeout=5,
    )
    try:
        yield connection
    finally:
        connection.close()


def fetch_all(query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            return list(cursor.fetchall())


def fetch_one(query: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone()


def database_connect() -> bool:
    try:
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
        return True

    except pymysql.MySQLError as error:
        print(f"ERROR: Failed to connect to crkl_db: {error}")
        return False
