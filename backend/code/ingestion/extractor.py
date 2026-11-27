# Purpose: extractor.py is responsible for sending HTTP requests to the LL2 API, which retrieves the real data
# - in addition to sending HTTP requests, this file should also handle pagination, rate limiting, & error handling

# (unsure if ALL 3 of these are needed, but here are supplementary links to hopefully further understanding)
# link to the LL2 API setup tutorial: https://github.com/TheSpaceDevs/Tutorials/blob/main/tutorials/getting_started_LL2/README.md
# link to the LL2 API docs: https://ll.thespacedevs.com/docs/
# link to TheSpaceDevs' API page: https://thespacedevs.com/llapi

# importing the httpx library, a third-party library that allows us to send HTTP requests
import httpx

# importing the JSON library to create a local cache file
import json

# importing the pathlib to create the directory path for the local cache
from pathlib import Path

# the path for the cache directory
cache_path = Path(__file__).resolve().parents[2] / "data" / "cache"

# configuration for the LL2 API
base_url = "https://ll.thespacedevs.com/2.3.0"

# header for the user-agent
headers = {"User-Agent": "CRKL-Space/1.0 (https://crkl-sdsu.github.io/CRKL/)"}

# setting a page limit per API request
page_limit = 100

# the maximum time to wait for an API response
timeout = 60.0

# function that will fetch all pages for a given endpoint (applies to only agencies, launches, & spacecraft)
def fetch_all_pages(
        endpoint: str, 
        refresh: bool = False, 
        extra_params: dict | None = None, 
        cache_name: str | None = None, 
        checkpoint_name: str | None = None, 
        use_cache: bool = True
    ) -> list[dict]:
    """
    Retrieves all pages of data from the specified endpoint of the LL2 API

    Args:
        endpoint: the API endpoint (e.g., "/agencies/" or "/launches/")
        refresh: determines if extractor.py will gather fresh LL2 responses or use the local cache
        extra_params: optionally, include additional API filters
        cache_name: optionally, include a separate cache filename
        checkpoint_name: optionally, include a separate checkpoint filename
        use_cache: determines if an existing completed cache should be returned

    Returns:
        A list containing all the raw records returned by the LL2 API
    """

    # creating the path for the local cache 
    cache_file = cache_path / (cache_name or f"{endpoint.strip('/').replace('/', '_')}.json")

    # creating a temporary file to save pagination progress
    checkpoint_file = cache_path / (checkpoint_name or f"{endpoint.strip('/').replace('/', '_')}_checkpoint.json")

    # "if the cache director doesn't exist, create it via the path: backend/data/cache"
    cache_path.mkdir(parents = True, exist_ok = True)

    # "if a refresh is requested AND the checkpoint file exists, remove that checkpoint"
    if refresh and checkpoint_file.exists():
        checkpoint_file.unlink()

    # "if the checkpoint file exists, restore previous records & next-page URL & continue from that checkpoint..."
    if checkpoint_file.exists():
        # with the checkpoint file (in "r"ead mode), load its contents as a JSON file
        with checkpoint_file.open("r", encoding  = "utf-8") as file:
            checkpoint = json.load(file)

        # reacquiring record, next_url, & parameter information
        results = checkpoint["results"]
        url = checkpoint["next_url"]
        params = checkpoint["params"]

        # defining the requested parameters, optionally including any extra parameters if they exist
        requested_params = {"limit": page_limit, **(extra_params or {})}

        # "if the initial parameters exist in the checkpoint file, acquire them & check if they're the requested parameters"
        if "initial_params" in checkpoint:
            initial_params = checkpoint["initial_params"]

            # "if the initial parameters are NOT the requested parameters, raise a ValueError indicating that extraction can't continue..."
            if initial_params != requested_params:
                raise ValueError(
                    "ERROR: The existing checkpoint parameters do not match the requested parameters for extraction. "
                    "Resume with the original parameters or use refresh=True to restart."
                )

        # "... else if extra parameters were specificed, then raise another ValueError indicating that legacy / old checkpoint parameters can't be used..."
        elif extra_params:
            raise ValueError(
                "Legacy checkpoint cannot be used for incremental extraction. "
                "Use refresh=True to restart."
            )

        # "... else set the initial parameters to the requested parameters"
        else:
            initial_params = requested_params

        print(f"Resuming fetch from {len(results)} previously collected records")


    # "... else if the cache exists AND a refresh is NOT requested AND we want to use the cache, access & return the cache's contents..."
    elif cache_file.exists() and not refresh and use_cache:
        # with the file opened (in "r"ead mode), return its contents
        with cache_file.open("r", encoding = "utf-8") as file:
            return json.load(file)


    # "... else create record & pagination information"
    else:
        # the URL for the API request, obtained by concatenating the base URL and the endpoint
        url = f"{base_url}{endpoint}"
        
        # if specified, also include extra parameters
        initial_params = {"limit": page_limit, **(extra_params or {})}
        params = initial_params.copy()

        # will store all the records retrieved from the API
        results = []

    # creating a new httpx client & sending a GET request to the API endpoint
    with httpx.Client(timeout = timeout, headers = headers) as client:
        # while-loop that continues to send requests until there are no more pages of data to retrieve
        while url:
            # getting the API endpoint with the params
            response = client.get(url, params = params)

            # "if the LL2 API responds with a 429 error code (meaning that we've reached the rate limit), report the cooldown & stop execution"
            if response.status_code == 429:
                # get the retry response
                retry_after = response.headers.get("Retry-After")

                print("LL2 rate limit reached. Fetch progress has been saved.")

                # "if we got a retry response, display the timeout period until a fetch request can be made"
                if retry_after:
                    print(f"Retry-After: {retry_after}")

                # raising a HTTPStatusError indicating that we've reached the LL2 API's rate limit
                raise httpx.HTTPStatusError(
                    "LL2 rate limit reached; run the fetch function again later to resume.",
                    request=response.request,
                    response=response
                    
                )

            # status check for other unsuccessful responses
            response.raise_for_status()

            # storing the data as a JSON object
            data = response.json()

            # collecting the records from the current page
            results.extend(data["results"])

            # moving onto the next page
            url = data["next"]

            # since the params are already included in the next-page URL, no need to redefine params
            params = None

            # creating a checkpoint "object"
            checkpoint = {
                "results": results,
                "next_url": url,
                "params": params,
                "initial_params": initial_params
            }

            # with the checkpoint file (in "w"rite mode), dump the checkpoint info into it
            with checkpoint_file.open("w", encoding = "utf-8") as file:
                json.dump(checkpoint, file, indent = 4)


    # with the file opened (in "w"rite mode), save the fetched records as a JSON file in the cache directory
    with cache_file.open("w", encoding = "utf-8") as file:
        json.dump(results, file, indent = 4)

    # "if the checkpoint file exists, unlink (remove) it after completing a fetch request"
    if checkpoint_file.exists():
        checkpoint_file.unlink()

    return results


# ===== these functions will fetch their respective real data ===== #
# function that will fetch the agencies from the LL2 API
def fetch_agencies() -> list[dict]:
    """
    Retrieves all agencies records from the LL2 API
    """

    return fetch_all_pages("/agencies/")


# function that will fetch the spacecraft from the LL2 API
def fetch_spacecraft() -> list[dict]:
    """
    Retrieves all spacecraft records from the LL2 API
    """

    return fetch_all_pages("/spacecraft/")

# function that will fetch the launches records from the LL2 API
# NOTE: unlike the agencies & spacecraft, launches requires more work & retrieval because mission records rely on nested information within launch records
def fetch_launches(
        extra_params: dict | None = None,
        cache_name: str | None = None,
        checkpoint_name: str | None = None,
        use_cache: bool = True
) -> list[dict]:
    """
    Retrieves all launches records from the LL2 API

    Args:
        extra_params: optionally, include additional query parameters for better filtering results
        cache_name: optionally, include the relevant cache filename
        checkpoint_name: optionally, include the relevant checkpoint filename
        use_cache: determines whether to use an existing completed cache
    """

    return fetch_all_pages(
        "/launches/",
        extra_params = extra_params,
        cache_name = cache_name,
        checkpoint_name = checkpoint_name,
        use_cache = use_cache
    )