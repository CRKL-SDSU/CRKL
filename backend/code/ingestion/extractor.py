# Purpose: extractor.py is responsible for sending HTTP requests to the LL2 API, which retrieves the real data
# - in addition to sending HTTP requests, this file should also handle pagination, rate limiting, & error handling

# (unsure if you'll need ALL 3 of these, but here are supplementary links)
# link to the LL2 API setup tutorial: https://github.com/TheSpaceDevs/Tutorials/blob/main/tutorials/getting_started_LL2/README.md
# link to the LL2 API docs: https://ll.thespacedevs.com/docs/
# link to TheSpaceDevs' API page: https://thespacedevs.com/llapi

# importing the httpx library, a third-party library that allows us to send HTTP requests
import httpx

