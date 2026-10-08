# CRKL Backend

The backend is a FastAPI service that provides the CRKL REST API. It runs on
`http://127.0.0.1:8000` by default, with API routes under `/api/v1`.

## Setup

From the repository root, install the backend dependencies:

```bash
python3 -m pip install -r backend/installation.txt
```

Create the local database configuration:

```bash
cp backend/conf/local.example.yaml backend/conf/local.yaml
```

Set the MySQL password through the environment. The environment variable takes
precedence over the password in `local.yaml`:

```bash
export CRKL_DB_USER_PASSWORD='your_mysql_password'
```

If using `direnv`, put that export in a repository `.envrc` file and run
`direnv allow`.

## Run the API

Start MySQL, then run the API from the repository root:

```bash
cd backend/code
python3 main.py
```

When using the repository `.envrc`, start the backend through direnv so
`CRKL_DB_USER_PASSWORD` is available:

```bash
cd backend/code
direnv exec ../.. python3 main.py
```

The frontend's Next.js BFF connects to this private API server. Do not expose
port `8000` publicly when the frontend is deployed as the public entrypoint.

The default configuration file is `backend/conf/local.yaml`. To use another
configuration such as `backend/conf/foobar.yaml`, set `CRKL_CONFIG_PATH`
before starting the API:

```bash
export CRKL_CONFIG_PATH="$PWD/backend/conf/foobar.yaml"
cd backend/code
python3 main.py
```

Check that the service is running:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/v1/health
```

The health endpoint reports whether the API can connect to the configured
`crkl_db` MySQL database.

## Tests

Backend tests use mocked database calls, so they do not require MySQL or a
running API server.

Install the CI test dependencies and run the suite from the repository root:

```bash
python3 -m pip install -r backend/requirements-ci.txt
python3 -m pytest backend/tests
```

GitHub Actions runs this suite automatically for pushes and pull requests.
