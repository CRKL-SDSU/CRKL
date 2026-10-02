# Database setup

These scripts create the `crkl_db` database, load sample data, and create the
database user used by the backend.

## 1. Create the database and load sample data

From the repository root, run:

```bash
mysql -u root -p < specs/db/DDL.sql
mysql -u root -p crkl_db < specs/db/dummy_data.sql
```

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
export CRKL_MYSQL_PASSWORD='your_strong_password'
```

The local configuration file and password are not committed to Git.
