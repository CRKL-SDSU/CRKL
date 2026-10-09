# Purpose: db_management.py manages the connection to our database

import os
from contextlib import contextmanager
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

# importing our configuration settings, or our "login info" (defined at the last line in config.py: CONFIG = load_config())
from config import CONFIG

# function that will connect to our database, using the CONFIG defined in config.py
@contextmanager
def database_connection() -> Iterator[pymysql.connections.Connection]:
    database = CONFIG["database"]
    connection = pymysql.connect(
        host=database["host"],
        user=database["user"],
        password=os.getenv("CRKL_DB_USER_PASSWORD", database["password"]),
        database=database["name"],
        port=int(database["port"]),
        cursorclass=DictCursor,
        connect_timeout=5,
    )
    # "try to yield the connection, and finally close the connection when done"
    try:
        yield connection
    finally:
        connection.close()

# function that will fetch all records from our database, given a query & parameters
def fetch_all(query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            return list(cursor.fetchall())

# function that will fetch only one record from our database, given a query & parameters
def fetch_one(query: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone()

# flag to check our database connection, which will be used in main.py
def database_connect() -> bool:
    # "try to verify the connection to our database and make an exception for any errors"
    try:
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
        return True

    except pymysql.MySQLError as error:
        print(f"ERROR: Failed to connect to crkl_db: {error}")
        return False
