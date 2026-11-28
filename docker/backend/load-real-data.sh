#!/bin/sh
# Load the real Launch Library 2 data from the snapshot files in
# backend/data/snapshot/ (mounted at /app/data/snapshot), without calling the API.
#
#   docker compose run --rm load-real-data             # add to the existing data
#   docker compose run --rm load-real-data --replace   # delete all data first
#
# Adding keeps any sample data; rerunning updates the real records instead of
# adding duplicates. --replace deletes every mission, agency, spacecraft,
# launch, and tag (including tags added on the site) before loading.
set -eu

SNAPSHOT=/app/data/snapshot
CACHE=/app/data/cache

case "${1:-}" in
    "") REPLACE=0 ;;
    --replace) REPLACE=1 ;;
    *) echo "Usage: docker compose run --rm load-real-data [--replace]" >&2; exit 2 ;;
esac

# the ETL calls the API for any file it can't find, so stop if one is missing
for name in agencies spacecraft launches; do
    if [ ! -f "$SNAPSHOT/$name.json" ]; then
        echo "ERROR: $SNAPSHOT/$name.json is missing; the snapshot is incomplete." >&2
        exit 1
    fi
done

cd /app/code

if [ "$REPLACE" -eq 1 ]; then
    echo "Deleting all existing data..."
    python - <<'PY'
from db_management import database_connection

# deleting missions also deletes their junction rows and tags (ON DELETE CASCADE)
with database_connection() as connection:
    try:
        connection.begin()
        with connection.cursor() as cursor:
            for table in ("missions", "launches", "spacecraft", "agencies", "tags"):
                cursor.execute(f"DELETE FROM {table}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
PY
fi

# the ETL reads finished fetches from its cache folder, so the snapshot files go there
mkdir -p "$CACHE"
cp "$SNAPSHOT/agencies.json" "$SNAPSHOT/spacecraft.json" "$SNAPSHOT/launches.json" "$CACHE/"

python -m ingestion.manager
echo "Real data loaded. Open http://localhost:3000/explore"
