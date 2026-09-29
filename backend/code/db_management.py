# This file handles Python-to-database connections

import os
# imported library for connecting Python to MySQL database
import pymysql
# loading our database info from .env
from dotenv import load_dotenv

# loading the information from the .env file
load_dotenv()

def database_connect() -> bool:
    try:
        connection = pymysql.connect(
            host = os.getenv("db_host"),
            user = os.getenv("db_user"),
            password = os.getenv("db_password"),
            database = os.getenv("db_name"),
            port = int(os.getenv("db_port", 3306)),
            connect_timeout = 5
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")

        connection.close()
        return True

    except pymysql.MySQLError as e:
        print(f"ERROR: Failed to connect to space_exploration_db: {e}")
        return False