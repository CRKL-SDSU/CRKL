# Purpose: manager.py is responsible for ensuring that the ETL pipeline process is executed in-order & without errors
# the steps should go as follows: extract --> transform --> load
# link to logger library: https://docs.python.org/3/library/logging.html

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
from .loader import load_agencies, load_spacecraft, load_launches
# ================================================ #

# creating a logger for the ingestion manager
logger = logging.getLogger(__name__)

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


# function that will execute the ETL pipeline for missions records
# NOTE: this does NOT currently work as intended! I'm awaiting an official team response for handling mission status labels
# currently, I have a check that prevents missions WITHOUT statuses from being added, which means 0 missions will be added
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

        # === these lines are omitted because I'm waiting for the team's response on handeling mission status labels === #
        # loaded_missions_count = load_missions(transformed_missions)
        # logger.info("Loaded %s missions records", transformed_missions)

        # return loaded_missions_count

        return transformed_missions

    # exception, in which case raise an error indicating the missions pipeline failed
    except Exception:
        logger.exception("Mission preparation failed")
        raise


# function that will run any available pipelines
# NOTE: the argument is conditional (whether or not raw_launches is already defined) to factor two choices:
#   - send requests to LL2 API
#   - use existing raw launch records
def run_available_pipelines(raw_launches: list[dict] | None = None) -> dict:
    """
    Runs all currently available, complete entity pipelines

    Args:
        raw_launches: Optional list of raw LL2 launch records

    Returns:
        A dictionary containing the number of processed records for each completed pipeline
    """
    logger.info("Starting available ETL pipelines...")

    # acquiring our pipeline results
    results = {
        "agencies": run_agency_pipeline(),
        "spacecraft": run_spacecraft_pipeline(),
        "launches": run_launches_pipeline(raw_launches)

    }

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