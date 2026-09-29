
# NOTE: A lot of the information regarding this web server, & what I used, can be found at: 
# https://fastapi.tiangolo.com/tutorial/first-steps/

# imported library for web framework
from fastapi import FastAPI
# connecting db_management.py to main
from db_management import *

# creating our server instance
app = FastAPI(title = "CRKL-Space", 
              description = "The official CRKL-Space web server.", 
              version = "1.0.0")

# getting the root endpoint path to our server
@app.get("/")
def root():
    return {"status:": "ONLINE", "message": "We are LIVE!"}

# health check-up on our web server
@app.get("/api/v1/health")
def health_check():
    server_is_connected = database_connect()

    return {
        "status": "healthy :)" if server_is_connected else "unhealthy :(",
        "database": "connected :)" if server_is_connected else "disconnected :("
    }


# note: this is also shown upon server startup
# Server is running on http://127.0.0.1:8000"
if __name__ == "__main__":
    import uvicorn

    # running our server on my main PC, using the network port (8000)
    # goal: make sure this can be ran for anyone at CRKL, & not just me at my house
    uvicorn.run(app, host = "127.0.0.1", port = 8000)