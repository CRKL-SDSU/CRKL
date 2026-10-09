# Purpose: main.py sets up both our backend web server & API endpoints for the frontend

# NOTE: A lot of the information regarding this web server & what I used can be found at: 
# https://fastapi.tiangolo.com/tutorial/first-steps/

# imported library for web framework
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db_management import database_connect
from endpoints import router as api_router

# creating our server instance
app = FastAPI(title = "CRKL-Space", 
              description = "The official CRKL-Space web server.", 
              version = "1.0.0")

# adding CORS (Cross-Origin Resource Sharing) middleware to our server, allowing requests from the localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# including the API router to our server (see endpoints.py for the endpoints)
app.include_router(api_router)

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