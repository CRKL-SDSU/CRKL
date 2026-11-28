#!/bin/sh
# Load the fictional sample data (specs/db/dummy_data.sql) for testing.
#
#   docker compose run --rm load-dummy-data             # into an empty database
#   docker compose run --rm load-dummy-data --replace   # delete all data first
#
# The sample data uses fixed IDs, so without --replace it can only go into an
# empty database. --replace deletes every mission, agency, spacecraft, launch,
# and tag (including tags added on the site) before loading.
set -eu

case "${1:-}" in
    "") REPLACE=0 ;;
    --replace) REPLACE=1 ;;
    *) echo "Usage: docker compose run --rm load-dummy-data [--replace]" >&2; exit 2 ;;
esac

export MYSQL_PWD="$CRKL_DB_USER_PASSWORD"
db() { mysql -h mysql -u crkl crkl_db "$@"; }

if [ "$REPLACE" -eq 1 ]; then
    echo "Deleting all existing data..."
    # deleting missions also deletes their junction rows and tags (ON DELETE CASCADE)
    db -e "START TRANSACTION;
           DELETE FROM missions; DELETE FROM launches; DELETE FROM spacecraft;
           DELETE FROM agencies; DELETE FROM tags;
           COMMIT;"
else
    records=$(db -N -e "SELECT (SELECT COUNT(*) FROM agencies) + (SELECT COUNT(*) FROM launches)
                             + (SELECT COUNT(*) FROM spacecraft) + (SELECT COUNT(*) FROM missions)")
    if [ "$records" -ne 0 ]; then
        echo "ERROR: The database already has $records records, and the sample data's fixed IDs" >&2
        echo "would collide with them. To replace all data with the sample data, run:" >&2
        echo "  docker compose run --rm load-dummy-data --replace" >&2
        exit 1
    fi
fi

db < /sample/dummy_data.sql
echo "Sample data loaded. Open http://localhost:3000/explore"
