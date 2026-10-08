#!/bin/bash
# Create the least-privilege application user for the backend.
# The host is '%' because the backend connects from another container.
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<SQL
CREATE USER IF NOT EXISTS 'crkl'@'%' IDENTIFIED BY '${CRKL_MYSQL_PASSWORD}';
GRANT SELECT, INSERT, UPDATE, DELETE ON crkl_db.* TO 'crkl'@'%';
FLUSH PRIVILEGES;
SQL
