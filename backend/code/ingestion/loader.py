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
            image_url,
            thumbnail_url,
            image_credit,
            image_license
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            abbrev = VALUES(abbrev),
            country_code = VALUES(country_code),
            image_url = VALUES(image_url),
            thumbnail_url = VALUES(thumbnail_url),
            image_credit = VALUES(image_credit),
            image_license = VALUES(image_license)
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
                        agency["image_url"],
                        agency["thumbnail_url"],
                        agency["image_credit"],
                        agency["image_license"]
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
        spacecraft: A list of the transformed spacecraft dictionaries

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
            image_url,
            thumbnail_url,
            image_credit,
            image_license
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            spacecraft_type = VALUES(spacecraft_type),
            image_url = VALUES(image_url),
            thumbnail_url = VALUES(thumbnail_url),
            image_credit = VALUES(image_credit),
            image_license = VALUES(image_license)
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
                        item["image_url"],
                        item["thumbnail_url"],
                        item["image_credit"],
                        item["image_license"]
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
        launches: A list of the transformed launches dictionaries

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
            launch_service_provider_id,
            image_url,
            thumbnail_url,
            image_credit,
            image_license,
            window_start,
            window_end
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            net = VALUES(net),
            status = VALUES(status),
            launch_service_provider_id = VALUES(launch_service_provider_id),
            image_url = VALUES(image_url),
            thumbnail_url = VALUES(thumbnail_url),
            image_credit = VALUES(image_credit),
            image_license = VALUES(image_license),
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
                # map LL2 agency IDs to our agency_id, so each launch can point to its launch service provider
                # NOTE: a provider that isn't in the agencies table is stored as NULL
                cursor.execute("SELECT source_id, agency_id FROM agencies WHERE source_provider = 'll2'")
                agency_ids = {row["source_id"]: row["agency_id"] for row in cursor.fetchall()}

                values = [
                    (
                        launch["source_provider"],
                        launch["source_id"],
                        launch["name"],
                        launch["net"],
                        launch["status"],
                        agency_ids.get(launch["launch_service_provider_source_id"]),
                        launch["image_url"],
                        launch["thumbnail_url"],
                        launch["image_credit"],
                        launch["image_license"],
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

    # creating an SQL query to insert or update a mission record
    query = """
        INSERT INTO missions (
            source_provider, source_id, name, description,
            target_body, status, image_url, thumbnail_url,
            image_credit, image_license
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            description = VALUES(description),
            target_body = VALUES(target_body),
            status = VALUES(status),
            image_url = VALUES(image_url),
            thumbnail_url = VALUES(thumbnail_url),
            image_credit = VALUES(image_credit),
            image_license = VALUES(image_license)
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
                        mission["image_url"],
                        mission["thumbnail_url"],
                        mission["image_credit"],
                        mission["image_license"]
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


# === the following functions will fill in the junction tables === #
# (i.e., mission_agencies, mission_spacecraft, mission_launches)

# function that will load mission-agency relationships into that junction table
def load_mission_agencies(relationships: list[tuple[str, str]]) -> int:
    """
    Loads mission-agency relationships into the mission_agencies table

    Args:
        relationships: A list of (mission_source_id, agency_source_id) pairs

    Returns:
        The number of inserted or processed relationships
    """

    # "if there are no relationships, terminate immediately"
    if not relationships: return 0

    # query statement
    query = """
        INSERT IGNORE INTO mission_agencies (mission_id, agency_id)
        SELECT missions.mission_id, agencies.agency_id
        FROM missions
        JOIN agencies
            ON agencies.source_provider = 'll2'
            AND agencies.source_id = %s
        WHERE missions.source_provider = 'll2'
            AND missions.source_id = %s
    """

    # using the logic from db_management.py to createa  db connection
    with database_connection() as connection:
        # "try to start a db transaction, make an exception for any necessary rollbacks"
        try:
            # begin the connection
            connection.begin()

            # with the connection cursor, prepare the data for insertion
            with connection.cursor() as cursor:
                values = [(agency_id, mission_id) for mission_id, agency_id in relationships]
                cursor.executemany(query, values)

                loaded_count = cursor.rowcount

            connection.commit()

        # exception, at which initiate a rollback
        except Exception:
            connection.rollback()
            raise

    return loaded_count


# function that will load mission-launch relationships into that junction table
def load_mission_launches(relationships: list[tuple[str, str]]) -> int:
    """
    Loads mission-launch relationships into the mission_launches table

    Args:
        relationships: A list of (mission_source_id, launch_source_id) pairs

    Returns:
        The number of inserted or processed relationships
    """

    # "if there are no relationships, terminate immediately"
    if not relationships: return 0

    # query statement
    query = """
        INSERT IGNORE INTO mission_launches (mission_id, launch_id)
        SELECT missions.mission_id, launches.launch_id
        FROM missions
        JOIN launches
            ON launches.source_provider = 'll2'
            AND launches.source_id = %s
        WHERE missions.source_provider = 'll2'
            AND missions.source_id = %s
    """

    # using the logic from db_management.py to create a db connection
    with database_connection() as connection:
        # "try to start a db transaction, make an exception for any necessary rollbacks"
        try:
            # begin the connection
            connection.begin()

            # with the connection cursor, prepare the data for insertion
            with connection.cursor() as cursor:
                values = [
                    (launch_id, mission_id)
                    for mission_id, launch_id in relationships
                ]
                cursor.executemany(query, values)

                loaded_count = cursor.rowcount

            connection.commit()

        # exception, in which case rollback
        except Exception:
            connection.rollback()
            raise

    return loaded_count
