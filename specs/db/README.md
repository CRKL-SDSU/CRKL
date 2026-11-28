# Database setup

These scripts create the `crkl_db` database and the database user used by the
backend, for a local MySQL without Docker. With Docker, see
[Load data](../../README.md#load-data) in the main README instead.

## 1. Create the database

From the repository root, run:

```bash
mysql -u root -p < specs/db/DDL.sql
```

`DDL.sql` drops and recreates `crkl_db`, so rerunning it starts over with
empty tables.

## 2. Create the `crkl` database user

Open `specs/db/user.sql` and replace every
`REPLACE_WITH_A_STRONG_PASSWORD` value with the same strong password. Then
connect to MySQL as an administrator:

```bash
mysql -u root -p
```

Run the SQL statements from `specs/db/user.sql` in the MySQL prompt. The
statements create or update `crkl` for both `127.0.0.1` and `localhost`, and
grant it access to `crkl_db`.

Alternatively, after replacing the placeholder password, execute the SQL
statements without the first `mysql ...` line:

```bash
mysql -u root -p < specs/db/user.sql
```

## 3. Configure the backend

Create the local backend configuration:

```bash
cp backend/conf/local.example.yaml backend/conf/local.yaml
```

Set the user and database in `backend/conf/local.yaml`:

```yaml
database:
  user: crkl
  name: crkl_db
```

Inject the password when starting the backend:

```bash
export CRKL_DB_USER_PASSWORD='your_strong_password'
```

The local configuration file and password are not committed to Git.

## 4. Load data

Load the real data from the Launch Library 2 snapshot (after steps 2 and 3,
with `CRKL_DB_USER_PASSWORD` set). The ETL reads finished fetches from
`backend/data/cache/`, so copy the snapshot files there first; otherwise it
calls the API:

```bash
mkdir -p backend/data/cache
cp backend/data/snapshot/*.json backend/data/cache/
(cd backend/code && python3 -m ingestion.manager)
```

Or load the fictional sample data, which only loads into empty tables:

```bash
mysql -u root -p crkl_db < specs/db/dummy_data.sql
```

To replace one with the other, rerun `DDL.sql` first.
