# CRKL
CS 514 Final Project

CRKL-Space is a searchable catalog of space missions, agencies, spacecraft,
and launches: a MySQL database, a FastAPI backend, and a Next.js frontend.
Project website: <https://crkl-sdsu.github.io/CRKL/>

## Start the servers

There are two ways to run CRKL-Space. Both serve the app at
<http://localhost:3000/explore>, so run one at a time.

| | [A. Docker](#a-docker) | [B. Local](#b-local-without-docker) |
| --- | --- | --- |
| Use it for | Trying the app, demos, grading | Day-to-day development |
| Start | `docker compose up --build` | `scripts/dev.sh` |
| Stop | `docker compose down` | Ctrl+C |
| You need | Docker Desktop only | Homebrew MySQL 8.0, Python 3.12, Node.js 20 |
| Database | `mysql-data` Docker volume, sample data loaded automatically | Your Homebrew MySQL `crkl_db` |
| Code changes | Rebuild: `docker compose up -d --build <service>` | Picked up on save (auto-reload) |

The two setups use separate databases: data changed in one does not appear in
the other.

### A. Docker

Docker Compose starts MySQL (with the sample data), the FastAPI backend, and
the Next.js frontend. You only need
[Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env      # then set both passwords in .env
docker compose up --build
```

Open <http://localhost:3000/explore>. Only port 3000 is published; the backend
and database are reachable only inside the Compose network.

On first start, MySQL runs `specs/db/DDL.sql`, `specs/db/dummy_data.sql`, and
`docker/mysql/03-app-user.sh`. The data is kept in the `mysql-data` volume
across restarts, and the passwords in `.env` are applied only on that first
start. To reset the database and reload the sample data:

```bash
docker compose down -v
docker compose up
```

### B. Local (without Docker)

`scripts/dev.sh` starts Homebrew MySQL if it is not running, the backend with
auto-reload, and the Next.js dev server, checks that each one is ready, and
prefixes their logs with `[backend]` and `[frontend]`.

**One-time setup**

1. Install and start MySQL 8.0, then create the database, sample data, and
   the `crkl` user as described in [`specs/db/README.md`](specs/db/README.md):

   ```bash
   brew install mysql@8.0
   brew services start mysql@8.0
   ```

2. Install the backend dependencies and create the backend config:

   ```bash
   python3 -m pip install -r backend/requirements.txt
   cp backend/conf/local.example.yaml backend/conf/local.yaml
   ```

3. Provide the `crkl` user's password. It overrides the value in
   `local.yaml`:

   ```bash
   export CRKL_DB_USER_PASSWORD='your_mysql_password'
   ```

   With [direnv](https://direnv.net/), put that line in an `.envrc` and run
   `direnv allow`; the script loads it automatically.

The script runs `npm install` and creates `frontend/.env.local` (with the
same setting as `frontend/.env.example`) if they are missing.

**Run**

```bash
scripts/dev.sh
```

Open <http://localhost:3000/explore>. Press **Ctrl+C** to stop the backend and
frontend. MySQL keeps running as a Homebrew service; stop it with
`brew services stop mysql@8.0`.

If the Docker frontend is running, the script stops with a message; free
port 3000 first with `docker compose stop frontend`.

**Without the script**, start the two servers in separate terminals:

```bash
# Backend: http://127.0.0.1:8000 (API under /api/v1)
cd backend/code && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Frontend: http://localhost:3000
cd frontend && npm install && npm run dev
```

Check the backend's database connection with
`curl http://127.0.0.1:8000/api/v1/health`.

## Frontend

The Next.js app in `frontend/` has two pages:

- `/explore`: the user-facing catalog. Search a resource collection, open a
  result's detail overlay, inspect related records, and move between them with
  the Back and Forward controls.
- `/`: an API console for list and detail requests against the REST API
  described in `specs/openapi/openapi.yaml`, showing the JSON responses.

The browser only calls same-origin `/api/v1` paths. The Next.js proxy in
`frontend/app/api/[...path]/route.ts` accepts the frontend's read-only
resource requests and forwards them server-side to `CRKL_BACKEND_URL`
(`http://127.0.0.1:8000` locally, `http://backend:8000` in Docker). The
backend URL is never exposed to client-side JavaScript, and the backend port
must not be published.

## Tests

The test suites do not require a running MySQL, backend, or frontend server.

Run the backend tests from the repository root:

```bash
python3 -m pip install -r backend/requirements-ci.txt
python3 -m pytest backend/tests
```

Run the frontend type check, tests, and production build:

```bash
cd frontend
npm install
npm run typecheck
npm test
npm run build
```

Run everything from the repository root:

```bash
python3 -m pytest backend/tests && \
  (cd frontend && npm run typecheck && npm test && npm run build)
```

GitHub Actions runs the same checks for pushes and pull requests.
