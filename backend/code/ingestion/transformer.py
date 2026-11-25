# Purpose: transformer.py is responsible for, well, transforming the data extracted from extractor.py
# - should contain functions that map the data to each super entity (i.e., agencies, spacecraft, launches, missions)
# - IMPORTANT: information about the missions might be (or are) nested within the LL2 LAUNCH responses, so that information needs to be handled a bit differently

# link to the datetime library: https://docs.python.org/3/library/datetime.html

# importing the datetime library & UTC timezone information
from datetime import datetime, timezone

# the source provider for the real data (from LL2 API)
source_provider = "launch_library_2"

# function that will transform an AGENCY record
def transform_agency(agency: dict) -> dict:
    """
    Fits a raw LL2 agency record into the CRKL database

    Args:
        agency: A raw agency dictionary returned by the API

    Returns:
        A dictionary containing the fields required by the agencies table
    """

    # get the alpha-2 code, if it exists
    countries = agency.get("country") or []
    if countries: country_code = countries[0].get("alpha_2_code")
    else: country_code = None

    # get the image & its URL, if it exists
    image = agency.get("image")
    if isinstance(image, dict): image_url = image.get("image_url")
    else: image_url = image

    # returning the agency record fitted to our database
    return {
        "source_provider": source_provider,
        "source_id": str(agency["id"]),
        "name": agency["name"],
        "abbrev": agency.get("abbrev"),
        "country_code": country_code,
        "image_url": image_url
        
    }


# function that will transform a SPACECRAFT record
def transform_spacecraft(spacecraft: dict) -> dict:
    """
    Fits a raw LL2 spacecraft record into the CRKL database

    Args:
        agency: A raw spacecraft dictionary returned by the API

    Returns:
        A dictionary containing the fields required by the spacecraft table
    """

    # get the spacecraft config & type, if it exists
    # NOTE: the spacecraft type is nested within the config
    spacecraft_config = spacecraft.get("spacecraft_config") or {}
    spacecraft_type = spacecraft_config.get("type") or {}
    type_name = spacecraft_type.get("name")

    # get the image & URL, if it exists
    image = spacecraft.get("image")
    if isinstance(image, dict): image_url = image.get("image_url")
    else: image_url = image

    # returning the spacecraft record fitted to our database
    return {
        "source_provider": source_provider,
        "source_id": str(spacecraft["id"]),
        "name": spacecraft["name"],
        "spacecraft_type": type_name,
        "image_url": image_url

    }


# function that will transform a LAUNCH record
def transform_launch(launch: dict) -> dict:
    """
    Fits a raw LL2 launch record into the CRKL database

    Args:
        launch: A raw launch dictionary returned by the API
    
    Returns:
        A dictionary containing the fields required by the launches table
    """
    # get the launch status, if it exists
    status = launch.get("status") or {}
    status_name = status.get("name")

    # get the image & its URL, if it exists
    image = launch.get("image") or {}
    image_url = image.get("image_url")

    # converting the LL2 timestamps into UTC datetime objects for MySQL
    net = datetime.fromisoformat(launch["net"].replace("Z", "+00:00"))
    net = net.astimezone(timezone.utc).replace(tzinfo=None)

    window_start = datetime.fromisoformat(launch["window_start"].replace("Z", "+00:00"))
    window_start = window_start.astimezone(timezone.utc).replace(tzinfo=None)

    window_end = datetime.fromisoformat(launch["window_end"].replace("Z", "+00:00"))
    window_end = window_end.astimezone(timezone.utc).replace(tzinfo=None)

    # returning the launch record fitted to our database
    return {
        "source_provider": source_provider,
        "source_id": str(launch["id"]),
        "name": launch["name"],
        "net": net,
        "status": status_name,
        "image_url": image_url,
        "window_start": window_start,
        "window_end": window_end

    }


# helper function that will acquire (not extract) strictly unique mission records from the API's launch responses
def collect_unique_missions(launches: list[dict]) -> list[dict]:
    """
    Collects unique mission records nested within LL2 launch records

    Args:
        launches: A list of raw LL2 launch records

    Returns:
        A list of unique raw mission records
    """
    # will store the unique missions
    unique_missions = {}

    # for-loop that iterates through our launches, gets the missions & checks if they're unique
    for launch in launches:
        mission = launch.get("mission")

        # "if the current mission is unique based on its ID, add it to the list of unique missions"
        if isinstance(mission, dict) and mission.get("id") is not None:
            unique_missions[str(mission["id"])] = mission

    return list(unique_missions.values())


# function that will transform a MISSION record
def transform_mission(mission: dict) -> dict:
    """
    Fits a raw LL2 mission record into the CRKL database

    Args:
            mission: A raw mission record nested within an LL2 launch response, returned by the API
    
    Returns:
            A dictionary containing the fields required by the missions table
    """
    # get the information on any relevant celestial bodies (i.e., planets, stars, asteroids), including its orbit, if it exists
    orbit = mission.get("orbit") or {}
    celestial_body = orbit.get("celestial_body") or {}

    # get the mission image & its url, if it exists
    image = mission.get("image")
    if isinstance(image, dict): image_url = image.get("image_url")
    else: image_url = image

    # returning the mission record fitted to our database
    return {
        "source_provider": source_provider,
        "source_id": str(mission["id"]),
        "name": mission["name"],
        "description": mission.get("description"),
        "target_body": celestial_body.get("name"),
        "status": mission.get("status"), # --> as of now, returns "None" because LL2 mission records lack this field
        "image_url": image_url

    }