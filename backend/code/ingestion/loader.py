# Purpose: loader.py will load each translated entry into its respective table
# - no need to create an entirely new database connection, as that logic exists in db_management.py
# - in addition to loading the data into the 4 super entity tables, this file should also handle loading data into the junction tables:
#   - mission_agencies
#   - mission_spacecraft
#   - mission_launches

# importing the db connection context manager, 
from db_management import database_connection


# function that will load transformed agency records into the agencies table
def load_agencies(agencies: list[dict]) -> int:
    """
    Loads transformed agency records into the agencies table

    Args:
        agencies: A list of the transformed agency dictionaries

    Returns:
        The number of processed agency records
    """

    # "if there are no agency records, terminate immediately"
    if not agencies: return 0

    # creating an SQL query to insert or update an agency record
    # NOTE: "%s" is a placeholder value for strings
    query = """
        INSERT INTO agencies (
            source_provider,
            source_id,
            name,
            abbrev,
            country_code,
            image_url
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            abbrev = VALUES(abbrev),
            country_code = VALUES(country_code),
            image_url = VALUES(image_url)
        """

    # using the logic from db_management.py to create a db connection
    # this will allow us to actually load the data into the database
    with database_connection() as connection:
        # "try to start a db transaction, make an exception for any necessary rollbacks"
        try:
            # begin the connection
            connection.begin()

            # with the connection cursor, prepare the agency data for insertion
            with connection.cursor() as cursor:
                values = [
                    (
                        agency["source_provider"],
                        agency["source_id"],
                        agency["name"],
                        agency["abbrev"],
                        agency["country_code"],
                        agency["image_url"]
                    )
                    for agency in agencies
                ]
                # inserting (or updating) all agencies records
                cursor.executemany(query, values)

            # commit to the transaction
            connection.commit()

        # exception, in which case rollback the transaction
        except Exception:
            connection.rollback()
            raise

    # returning the total # of loaded records in the agencies table
    return len(agencies)


# function that will load transformed spacecraft records into the spacecraft table
def load_spacecraft(spacecraft: list[dict]) -> int:
    """
    Loads transformed spacecraft records into the spacecraft table

    Args:
        agencies: A list of the transformed spacecraft dictionaries

    Returns:
        The number of processed spacecraft records
    """

    # "if there are no spacecraft records, immediately terminate"
    if not spacecraft: return 0

    # creating an SQL query to insert or update a spacecraft record
    query = """
        INSERT INTO spacecraft (
            source_provider,
            source_id,
            name,
            spacecraft_type,
            image_url
        )
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            spacecraft_type = VALUES(spacecraft_type),
            image_url = VALUES(image_url)
    """

    # using the logic from db_management.py to create a db connection
    with database_connection() as connection:
        # "try to start a db transaction, make an exception for any necessary rollbacks"
        try:
            # begin the connection
            connection.begin()

            # with the connection cursor, prepare the spacecraft data for insertion
            with connection.cursor() as cursor:
                values = [
                    (
                        item["source_provider"],
                        item["source_id"],
                        item["name"],
                        item["spacecraft_type"],
                        item["image_url"]
                    )
                    for item in spacecraft
                ]
                # inserting (or updating) all spacecraft records
                cursor.executemany(query, values)

            # commit to the transaction
            connection.commit()

        # exception, in which case rollback the transaction
        except Exception:
            connection.rollback()
            raise

    # returning the total # of loaded records in the spacecraft table
    return len(spacecraft)


# function that will load the transformed launches data into the launches table
def load_launches(launches: list[dict]) -> int:
    """
    Loads transformed launches records into the launches table

    Args:
        agencies: A list of the transformed launches dictionaries

    Returns:
        The number of processed launches records
    """
    # "if there are no launches, terminate immediately"
    if not launches: return 0

    # creating an SQL query to insert or update a launch record
    query = """
        INSERT INTO launches (
            source_provider,
            source_id,
            name,
            net,
            status,
            image_url,
            window_start,
            window_end
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            net = VALUES(net),
            status = VALUES(status),
            image_url = VALUES(image_url),
            window_start = VALUES(window_start),
            window_end = VALUES(window_end)
    """

    # using the logic from db_management.py to create a db connection
    with database_connection() as connection:
        # "try to start a db transaction, make an exception for any necessary rollbacks"
        try:
            # begin the connection
            connection.begin()

            # with the connection cursor, prepare the launch data for insertion
            with connection.cursor() as cursor:
                values = [
                    (
                        launch["source_provider"],
                        launch["source_id"],
                        launch["name"],
                        launch["net"],
                        launch["status"],
                        launch["image_url"],
                        launch["window_start"],
                        launch["window_end"]
                    )
                    for launch in launches
                ]

                # inserting (or updating) all launch records
                cursor.executemany(query, values)

            # commit to the transaction
            connection.commit()

        # exception, in which case rollback the transaction
        except Exception:
            connection.rollback()
            raise

    # returning the total # of processed launch records
    return len(launches)


# function that will load the transformed mission data into the missions table
def load_missions(missions: list[dict]) -> int:
    # "if there are no missions, terminate immediately"
    if not missions: return 0

    # NOTE: the check for mission_statuses is here because, currently, none of the missions have status labels
    # to be able to verify load_missions, you'll need to have some launches records already saved, either through a checkpoint file or the cache
    # while testing, I was able to create a checkpoint file containing ~1425 records as a reference for testing

    # check for missing required mission statuses before attempting db insertion
    missing_statuses = sum(not mission.get("status") for mission in missions)

    # "if there are missing statuses, raise a ValueError stating that a status is required"
    if missing_statuses:
        raise ValueError(
            f"Cannot load missions: {missing_statuses} records are missing a required status."
        )

    # creating an SQL query to insert or update a mission record
    query = """
        INSERT INTO missions (
            source_provider, source_id, name, description,
            target_body, status, image_url
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            description = VALUES(description),
            target_body = VALUES(target_body),
            status = VALUES(status),
            image_url = VALUES(image_url)
    """

    # using the logic from db_management.py to create a db connection
    with database_connection() as connection:
        # "try to start a db transaction, make an exception for any necessary rollbacks"
        try:
            # begin the connection
            connection.begin()

            # with the connection cursor, prepare the mission data for insertion
            with connection.cursor() as cursor:
                values = [
                    (
                        mission["source_provider"],
                        mission["source_id"],
                        mission["name"],
                        mission["description"],
                        mission["target_body"],
                        mission["status"],
                        mission["image_url"]
                    )
                    for mission in missions
                ]
                # inserting (or updating) all mission records
                cursor.executemany(query, values)
            
            # commit to the transaction
            connection.commit()

        # exception, in which case rollback the transaction
        except Exception:
            connection.rollback()
            raise

    # returning the total # of loaded records in the missions table
    return len(missions)