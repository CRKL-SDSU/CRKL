# Specifications

## Frontend request sequence

The browser communicates with the same-origin Next.js frontend. The Next.js
backend-for-frontend (BFF) forwards approved read-only API requests to the
private FastAPI backend. The backend queries MySQL and returns the response
through the same path.

```mermaid
sequenceDiagram
    participant Browser
    participant Next as Next.js frontend/BFF
    participant API as Private FastAPI backend
    participant DB as MySQL

    Browser->>Next: GET /api/v1/missions
    Next->>Next: Validate resource path
    Next->>API: GET /api/v1/missions
    API->>DB: Execute catalog query
    DB-->>API: Query results
    API-->>Next: JSON response
    Next-->>Browser: JSON response
```

The BFF entrypoint is `frontend/app/api/[...path]/route.ts`. Its private
backend address is configured with the server-only `CRKL_BACKEND_URL`
environment variable. The browser must not call the backend address directly.

## Deploy pipeline

GitHub Actions (`.github/workflows/tests.yml`) runs the backend and frontend
test jobs in parallel on every push and pull request. The workflow does not
build artifacts or deploy. Deployment is manual: the backend and frontend are
started by hand, and only the frontend is exposed publicly.

```mermaid
flowchart TD
    start(( )) --> trigger[Push or pull request]
    trigger --> fork{{fork}}

    subgraph CI["GitHub Actions: Tests workflow"]
        direction TB
        subgraph BE["Backend tests job"]
            be1[Checkout] --> be2[Set up Python 3.12 with pip cache]
            be2 --> be3[pip install -r requirements-ci.txt]
            be3 --> be4[pytest]
        end
        subgraph FE["Frontend tests job"]
            fe1[Checkout] --> fe2[Set up Node 20 with npm cache]
            fe2 --> fe3[npm ci]
            fe3 --> fe4[npm run typecheck]
            fe4 --> fe5[npm test]
        end
    end

    fork --> be1
    fork --> fe1
    be4 --> join{{join}}
    fe5 --> join
    join --> passed{All jobs passed?}
    passed -- No --> failed((( Fail )))
    passed -- Yes --> merge[Merge to main]

    subgraph Manual["Manual deployment"]
        direction TB
        m1[Start MySQL with crkl_db] --> m2["Start private FastAPI backend<br/>CRKL_CONFIG_PATH, CRKL_MYSQL_PASSWORD<br/>python3 main.py on port 8000"]
        m2 --> m3["Build frontend<br/>npm run build"]
        m3 --> m4["Start public Next.js server<br/>CRKL_BACKEND_URL=http://backend:8000<br/>npm run start"]
        m4 --> m5[Check /api/v1/health]
    end

    merge --> m1
    m5 --> done((( Done )))
```

Mermaid has no native UML activity diagram, so this flowchart uses UML
activity notation: the empty circle marks the start, `fork`/`join` mark
parallel jobs, and the double circles mark end states. The test jobs use
mocked dependencies, so CI never connects to MySQL or a running server.
