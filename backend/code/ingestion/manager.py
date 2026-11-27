# Purpose: manager.py is responsible for ensuring that the ETL pipeline process is executed in-order & without errors
# the steps should go as follows: extract --> transform --> load
# link to logger library: https://docs.python.org/3/library/logging.html
# link to a reference about watermarking & incremental pipelining: https://medium.com/@gankur277/incremental-data-load-strategies-deep-dive-36838e11845a

# importing the json library, as well as the pathlib
import json
from pathlib import Path

# importing a bunch of datetime libraries to help with watermarking 
from datetime import datetime, timedelta, timezone

# importing the logging library, which will help print ETL pipeline progress & potential errors
import logging

# ===== importing the ETL pipeline functions ===== #
# importing the components from the extractor library
from .extractor import fetch_agencies, fetch_spacecraft, fetch_launches

# importing the components from the transformer library
from .transformer import (
    transform_agency,
    transform_spacecraft,
    transform_launch,
    collect_unique_missions,
    transform_mission
)

# importing the components from the loader library
from .loader import (
    load_agencies,
    load_spacecraft,
    load_launches,
    load_missions,
    load_mission_agencies,
    load_mission_launches
)
# ================================================ #

# creating a logger for the ingestion manager
logger = logging.getLogger(__name__)

# defining the path for the launch watermark file (launches_watermark.json)
# NOTE: a potential improvement, though not currently necessary, is to apply this logic for the agencies & spacecraft!
cache_path = Path(__file__).resolve().parents[2] / "data" / "cache"
watermark_file = cache_path / "launches_watermark.json"


# function that will load the saved launch watermark
def load_launches_watermark() -> datetime:
    """
    Loads the most recently successful (processed) LL2 launch timestamp

    Returns:
        The saved timestamp as a datetime object
    """

    # "if the watermark file does NOT exist, raise a FileNotFoundError indicating that launch record extraction must be completed first"
    if not watermark_file.exists():
        raise FileNotFoundError("ERROR: Launch watermark not found. Please complete the initial extraction first!")


    # assumes the watermark_file exists, so with the file read the watermark
    with watermark_file.open("r", encoding = "utf-8") as file:
        watermark = json.load(file)

    # returning the saved timestamp as a datetime object
    return datetime.fromisoformat(watermark["last_updated"].replace("Z", "+00:00"))


# function that will save the updated launch watermark
def save_launches_watermark(last_updated: datetime, records_loaded: int) -> None:
    """
    Will save the most recently successful (processed) LL2 launch timestamp

    Args:
        last_updated: the newest LL2 last_updated timestamp
        records_loaded: the number of processed launch records
    """

     # ensuring that the timestamp is stored in UTC
    watermark = {
        "last_updated": last_updated.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "records_loaded": records_loaded
    }

    # creating the cache directory if it doesn't exist
    cache_path.mkdir(parents=True, exist_ok=True)

    # with the watermark_file (in "w"rite mode), dump the updated watermark into the file
    with watermark_file.open("w", encoding="utf-8") as file:
        json.dump(watermark, file, indent=4)


# function that will execute the ETL pipeline for agency records  
def run_agency_pipeline() -> int:
    """
    Runs the ETL pipeline for agency records

    Returns:
        The total number of processed agency records
    """
    # try to run the ETL pipeline for agency records, make an exception for logger errors
    try:
        # fetching & logging the raw agency records
        raw_agencies = fetch_agencies()
        logger.info("Extracted %s agency records", len(raw_agencies))

        # transforming the agency records
        transformed_agencies = [transform_agency(agency) for agency in raw_agencies]
        logger.info("Transformed %s agency records", len(transformed_agencies))

        # loading the transformed agency records
        loaded_agency_count = load_agencies(transformed_agencies)
        logger.info("Loaded %s agency records", loaded_agency_count)

        return loaded_agency_count

    # exception, in which case raise a logger error indicating the ETL pipeline failed for agencies
    except Exception:
        logger.exception("Agencies pipeline failed")
        raise


# function that will execute the ETL pipeline for spacecraft records
def run_spacecraft_pipeline() -> int:
    """
    Runs the ETL pipeline for spacecraft records

    Returns:
        The total number of processed spacecraft records
    """
    # try to run the ETL pipeline for spacecraft records, make an exception for logger errors
    try:
        # fetching & logging the raw spacecraft records
        raw_spacecraft = fetch_spacecraft()
        logger.info("Extracted %s spacecraft records", len(raw_spacecraft))

        # transforming the spacecraft records
        transformed_spacecraft = [transform_spacecraft(spacecraft) for spacecraft in raw_spacecraft]
        logger.info("Transformed %s spacecraft records", len(transformed_spacecraft))

        # loading the transformed spacecraft records
        loaded_spacecraft_count = load_spacecraft(transformed_spacecraft)
        logger.info("Loaded %s spacecraft records", loaded_spacecraft_count)

        return loaded_spacecraft_count

    # exception, in which case raise a logger error indicating the ETL pipeline failed for spacecraft
    except Exception:
        logger.exception("Spacecraft pipeline failed")
        raise


# function that will execute the ETL pipeline for launch records
# NOTE: because I've yet to properly handle LL2's rate limiting, upon function call you might create a checkpoint JSON file in backend/data/cache
# a temporary (& convenient) solution is to create checkpoints, allowing the pipeline to continue from any cutoff points
def run_launches_pipeline(raw_launches: list[dict] | None = None) -> int:
    """
    Runs the ETL pipeline for launch records

    Args:
        raw_launches: Optional list of raw LL2 launch records

    Returns:
        The total number of processed launch records
    """
    # try to execute the ETL pipeline for launches records, make an exception for logger errors
    try:
        # "if there are no raw launches initially, fetch them"
        if raw_launches is None:
            raw_launches = fetch_launches()

        logger.info("Extracted %s launch records", len(raw_launches))

        # transforming the launch records
        transformed_launches = [transform_launch(launch) for launch in raw_launches]
        logger.info("Transformed %s launch records", len(transformed_launches))

        # loading the transformed launch records
        loaded_launches_count = load_launches(transformed_launches)
        logger.info("Loaded %s launch records", loaded_launches_count)

        return loaded_launches_count

    # exception, in which case raise an error indicating the launches pipeline failed
    except Exception:
        logger.exception("Launches pipeline failed")
        raise


# function that will run an incremental pipeline
def run_incremental_launches_pipeline() -> dict:
    """
    Retrieves and loads launches that have been updated since the last successful pipeline run.
    It uses a one-hour overlap to avoid missing updates with matching timestamps, which should help combat against the LL2 API's rate limit.

    A (hopefully) supplemental link for incremental pipelining: https://medium.com/@gankur277/incremental-data-load-strategies-deep-dive-36838e11845a
    """

    # load the timestamp from the previous successful pipeline run
    watermark = load_launches_watermark()

    # subtract one hour to create an overlap for the incremental extraction
    cutoff = watermark - timedelta(hours=1)
    cutoff_string = cutoff.isoformat().replace("+00:00", "Z")

    # fetch launches updated since the calculated cutoff
    raw_launches = fetch_launches(
        extra_params={
            "last_updated__gte": cutoff_string,
            "ordering": "last_updated"
        },
        cache_name="launches_incremental.json",
        checkpoint_name="launches_incremental_checkpoint.json",
        use_cache=False
    )

    # "if no updated launches were found, leave the watermark unchanged"
    if not raw_launches:
        logger.info("No updated launches found.")

        return {
            "launches": 0,
            "missions": 0,
            "relationships": {
                "mission_agencies": 0,
                "mission_launches": 0
            }
        }

    # collect the last_updated timestamps from the retrieved launches
    timestamps = [
        datetime.fromisoformat(launch["last_updated"].replace("Z", "+00:00"))
        for launch in raw_launches
        if launch.get("last_updated")
    ]

    # ensure every retrieved launch has a last_updated timestamp
    if len(timestamps) != len(raw_launches):
        raise ValueError("ERROR: One or more launches are missing their last_updated timestamp!")

    # determine the newest timestamp without allowing the watermark to move backwards
    newest_timestamp = max(watermark, max(timestamps))

    # transform and load the retrieved launches into the database
    loaded_count = run_launches_pipeline(raw_launches=raw_launches)

    # load any missions and relationships associated with the updated launches
    mission_count = len(prepare_mission_records(raw_launches))
    relationship_counts = prepare_mission_relationships(raw_launches)

    # update the watermark only after the database load succeeds
    save_launches_watermark(newest_timestamp, loaded_count)

    logger.info("Incremental launch pipeline completed. Records processed: %s", loaded_count)

    return {
        "launches": loaded_count,
        "missions": mission_count,
        "relationships": relationship_counts
    }



# function that will execute the ETL pipeline for missions records
def prepare_mission_records(launches: list[dict]) -> list[dict]:
    """
    Collects unique missions from launch records and transforms them.

    Args:
        launches: A list of raw LL2 launch records

    Returns:
        A list of transformed mission records
    """
    # try to run the ETL pipeline for mission records, make an exception for logger errors
    try:
        # fetching & logging the raw mission records
        raw_missions = collect_unique_missions(launches)
        logger.info("Collected %s unique mission records", len(raw_missions))

        # transforming the mission records
        transformed_missions = [transform_mission(mission) for mission in raw_missions]
        logger.info("Transformed %s mission records", len(transformed_missions))

        loaded_missions_count = load_missions(transformed_missions)
        logger.info("Loaded %s mission records", loaded_missions_count)

        return transformed_missions

    # exception, in which case raise an error indicating the missions pipeline failed
    except Exception:
        logger.exception("Mission preparation failed")
        raise


# function that will prepare and load mission relationship records
def prepare_mission_relationships(launches: list[dict]) -> dict:
    """
    Collects and loads mission-agency and mission-launch relationships

    Args:
        launches: A list of raw LL2 launch records

    Returns:
        A dictionary containing the number of loaded relationships
    """

    # collecting unique mission-agency relationships
    mission_agencies = {
        (str(mission["id"]), str(agency["id"]))
        for launch in launches
        if isinstance((mission := launch.get("mission")), dict)
        and mission.get("id") is not None
        for agency in (mission.get("agencies") or [])
        if isinstance(agency, dict) and agency.get("id") is not None
    }

    # collecting unique mission-launch relationships
    mission_launches = {
        (str(mission["id"]), str(launch["id"]))
        for launch in launches
        if isinstance((mission := launch.get("mission")), dict)
        and mission.get("id") is not None
        and launch.get("id") is not None
    }

    # loading the relationships into their respective junction tables
    agency_count = load_mission_agencies(list(mission_agencies))
    launch_count = load_mission_launches(list(mission_launches))

    logger.info("Loaded %s mission-agency relationships", agency_count)
    logger.info("Loaded %s mission-launch relationships", launch_count)

    return {
        "mission_agencies": agency_count,
        "mission_launches": launch_count
    }


# function that will run any available pipelines
# NOTE: supports both full & incremental launch loading
def run_available_pipelines(
    raw_launches: list[dict] | None = None,
    incremental: bool = False
) -> dict:
    """
    Runs all currently available, complete entity pipelines.

    Args:
        raw_launches: Optional list of raw LL2 launch records
        incremental: Whether to use incremental launch loading

    Returns:
        A dictionary containing the number of processed records for each completed pipeline
    """

    # "if the incremental flag is True and there are raw_launches, raise a ValueError indicating that raw launches can't be provided when incremental loading is active"
    if incremental and raw_launches is not None:
        raise ValueError("Cannot provide raw_launches when incremental loading is enabled.")

    logger.info("Starting available ETL pipelines...")

    # acquiring our pipeline results
    results = {
        "agencies": run_agency_pipeline(),
        "spacecraft": run_spacecraft_pipeline()
    }

    # if incremental loading is requested, run the incremental launch pipeline
    if incremental:
        results.update(run_incremental_launches_pipeline())

    # otherwise, run the full launch, mission, and relationship pipelines
    else:
        # "if there are no raw_launches, fetch them before running through the pipelines"
        if raw_launches is None:
            raw_launches = fetch_launches()

        results.update({
            "launches": run_launches_pipeline(raw_launches),
            "missions": len(prepare_mission_records(raw_launches)),
            "relationships": prepare_mission_relationships(raw_launches)
        })

    logger.info("Available ETL pipelines completed! :D")
    return results




# main, which will allow this module to be executed directly
if __name__ == "__main__":
    # configuring the logging output for a standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # running the available pipelines
    results = run_available_pipelines()
    logger.info("Pipeline results: %s", results)