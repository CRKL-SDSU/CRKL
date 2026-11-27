-- =========================================================================
-- CRKL-Space: Migration 002
-- Add each launch's launch service provider (the agency that carried out
-- the launch, as Launch Library 2 records it).
--
-- IMPORTANT:
--   - Run against an existing crkl_db database that already has migration 001.
--   - A new database created from DDL.sql already has this column.
--   - Rerun the ETL afterwards to fill the column for Launch Library 2 launches.
-- =========================================================================

USE crkl_db;

ALTER TABLE launches
    ADD COLUMN launch_service_provider_id INT AFTER status,
    ADD FOREIGN KEY (launch_service_provider_id) REFERENCES agencies(agency_id) ON DELETE SET NULL;
