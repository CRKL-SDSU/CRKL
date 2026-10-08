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
jobs in parallel on every push and pull request. The frontend job also runs a
production build. The workflow does not publish artifacts or deploy.

Deployment uses Docker Compose (`docker-compose.yml`): one command builds the
images and starts MySQL, the private FastAPI backend, and the public Next.js
frontend. Health checks start each service only after the one it depends on
is ready. On first start, MySQL loads the schema, the sample data, and the
least-privilege `crkl` user. Only the frontend port (3000) is published.

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
            fe5 --> fe6[npm run build]
        end
    end

    fork --> be1
    fork --> fe1
    be4 --> join{{join}}
    fe6 --> join
    join --> passed{All jobs passed?}
    passed -- No --> failed((( Fail )))
    passed -- Yes --> merge[Merge to main]

    subgraph Deploy["Deployment: docker compose up --build"]
        direction TB
        d0["Create .env from .env.example<br/>MYSQL_ROOT_PASSWORD, CRKL_MYSQL_PASSWORD"] --> d1
        d1["Build backend and frontend images"] --> d2
        d2["Start mysql<br/>first start: DDL.sql, dummy_data.sql, crkl user"] --> d3{mysql healthy?}
        d3 -- Yes --> d4["Start private backend<br/>CRKL_CONFIG_PATH=conf/docker.yaml"]
        d4 --> d5{backend healthy?}
        d5 -- Yes --> d6["Start public frontend<br/>CRKL_BACKEND_URL=http://backend:8000<br/>port 3000"]
    end

    merge --> d0
    d6 --> done((( Done )))
```

Mermaid has no native UML activity diagram, so this flowchart uses UML
activity notation: the empty circle marks the start, `fork`/`join` mark
parallel jobs, diamonds mark decisions, and the double circles mark end
states. The test jobs use mocked dependencies, so CI never connects to MySQL
or a running server.

For local development without Docker, `scripts/dev.sh` starts Homebrew MySQL,
the backend with auto-reload, and the Next.js dev server.
