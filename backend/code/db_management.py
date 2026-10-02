import os
from contextlib import contextmanager
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def database_connection() -> Iterator[pymysql.connections.Connection]:
    connection = pymysql.connect(
        host=os.getenv("db_host", "127.0.0.1"),
        user=os.getenv("db_user", "root"),
        password=os.getenv("db_password", ""),
        database=os.getenv("db_name", "space_exploration_db"),
        port=int(os.getenv("db_port", "3306")),
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

    except pymysql.MySQLError as e:
        print(f"ERROR: Failed to connect to space_exploration_db: {e}")
        return False