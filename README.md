# CRKL
CS 514 Final Project

## Frontend API console

The `frontend/` directory contains a small Next.js app for testing the REST API
described in `specs/openapi/openapi.yaml`. It supports list and detail requests
for missions, agencies, spacecraft, and launches and displays JSON responses.

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` to the API server's `/api/v1`
base URL (for example, `http://localhost:8000/api/v1`). The frontend expects
the API to allow browser requests from the Next.js development origin.

The user-facing catalog is available at `http://localhost:3000/explore`. It
searches the selected resource collection returned by the API and displays
matching records as result cards. Select a result to open its detail overlay,
inspect related records, and navigate between related entities with the Back
and Forward controls. The API console remains available at `/`.

## Backend configuration

Backend database settings are loaded from `backend/conf/local.yaml`. Create it
from the example:

```bash
cp backend/conf/local.example.yaml backend/conf/local.yaml
```

The local file is ignored by Git. Set `CRKL_MYSQL_PASSWORD` to inject the MySQL
password at runtime; it takes precedence over the YAML value:

```bash
export CRKL_MYSQL_PASSWORD='your_mysql_password'
```

## Tests

The test suites do not require a running MySQL, backend, or frontend server.

Run the backend tests from the repository root:

```bash
python3 -m pip install -r backend/requirements-ci.txt
python3 -m pytest backend/tests
```

Run the frontend type check and tests:

```bash
cd frontend
npm install
npm run typecheck
npm test
```

Run both suites from the repository root:

```bash
python3 -m pytest backend/tests && \
  (cd frontend && npm run typecheck && npm test)
```

GitHub Actions runs both suites for pushes and pull requests.
