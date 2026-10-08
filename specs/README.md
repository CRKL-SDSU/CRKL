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

The app can be run in two ways:

- **Docker Compose** (`docker-compose.yml`), for deployment and demos: one
  command builds the images and starts MySQL, the private FastAPI backend,
  and the public Next.js frontend. Health checks start each service only
  after the one it depends on is ready. On first start, MySQL loads the
  schema, the sample data, and the least-privilege `crkl` user. Only the
  frontend port (3000) is published.
- **Local development** (`scripts/dev.sh`), without Docker: starts Homebrew
  MySQL if needed, the backend with auto-reload, and the Next.js dev server,
  and stops both servers on Ctrl+C.

Both serve the app on port 3000, so run one at a time.

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
    merge --> mode{How to run?}

    subgraph Docker["Deployment and demos: docker compose up --build"]
        direction TB
        d0["Create .env from .env.example<br/>CRKL_DB_ROOT_PASSWORD, CRKL_DB_USER_PASSWORD"] --> d1
        d1["Build backend and frontend images"] --> d2
        d2["Start mysql container<br/>first start: DDL.sql, dummy_data.sql, crkl user"] --> d3{mysql healthy?}
        d3 -- Yes --> d4["Start private backend container<br/>CRKL_CONFIG_PATH=conf/docker.yaml"]
        d4 --> d5{backend healthy?}
        d5 -- Yes --> d6["Start public frontend container<br/>CRKL_BACKEND_URL=http://backend:8000<br/>port 3000"]
    end

    subgraph Local["Local development: scripts/dev.sh"]
        direction TB
        l0["Load CRKL_DB_USER_PASSWORD<br/>environment or direnv .envrc"] --> l1
        l1["Check backend/conf/local.yaml,<br/>ports 3000 and 8000, dependencies"] --> l2
        l2["Start Homebrew mysql@8.0 if not running<br/>wait for 127.0.0.1:3306"] --> l3
        l3["Start backend: uvicorn --reload<br/>127.0.0.1:8000"] --> l4{backend connected<br/>to MySQL?}
        l4 -- Yes --> l5["Start Next.js dev server<br/>CRKL_BACKEND_URL from .env.local<br/>port 3000"]
        l5 --> l6{/explore ready?}
        l6 -- Yes --> l7["Run until Ctrl+C<br/>stops backend and frontend"]
    end

    mode -- "Deploy or demo" --> d0
    mode -- "Develop locally" --> l0
    d6 --> done((( Done )))
    l7 --> done
```

Mermaid has no native UML activity diagram, so this flowchart uses UML
activity notation: the empty circle marks the start, `fork`/`join` mark
parallel jobs, diamonds mark decisions, and the double circles mark end
states. The test jobs use mocked dependencies, so CI never connects to MySQL
or a running server.
