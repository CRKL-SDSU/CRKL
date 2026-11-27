-- =========================================================================
-- CRKL-Space: Migration 001
-- Update existing database to match the current DDL schema.
--
-- IMPORTANT:
--   - Run against an existing crkl_db database only.
--   - Do NOT run DDL.sql or schema.sql beforehand.
--   - This is a one-time migration, not an initialization script.
--   - Back up the database before execution.
-- =========================================================================

USE crkl_db;

-- =========================================================================
-- 1. Agencies: image metadata and composite source index
-- =========================================================================

ALTER TABLE agencies
    ADD COLUMN thumbnail_url TEXT AFTER image_url,
    ADD COLUMN image_credit VARCHAR(255) AFTER thumbnail_url,
    ADD COLUMN image_license VARCHAR(100) AFTER image_credit,
    DROP INDEX source_id,
    ADD UNIQUE KEY uq_source (source_provider, source_id);

UPDATE agencies
SET source_provider = 'll2'
WHERE source_provider = 'launch_library_2';

-- =========================================================================
-- 2. Launches: image metadata and composite source index
-- =========================================================================

ALTER TABLE launches
    ADD COLUMN thumbnail_url TEXT AFTER image_url,
    ADD COLUMN image_credit VARCHAR(255) AFTER thumbnail_url,
    ADD COLUMN image_license VARCHAR(100) AFTER image_credit,
    DROP INDEX source_id,
    ADD UNIQUE KEY uq_source (source_provider, source_id);

UPDATE launches
SET source_provider = 'll2'
WHERE source_provider = 'launch_library_2';

-- =========================================================================
-- 3. Spacecraft: image metadata and composite source index
-- =========================================================================

ALTER TABLE spacecraft
    ADD COLUMN thumbnail_url TEXT AFTER image_url,
    ADD COLUMN image_credit VARCHAR(255) AFTER thumbnail_url,
    ADD COLUMN image_license VARCHAR(100) AFTER image_credit,
    DROP INDEX source_id,
    ADD UNIQUE KEY uq_source (source_provider, source_id);

UPDATE spacecraft
SET source_provider = 'll2'
WHERE source_provider = 'launch_library_2';

-- =========================================================================
-- 4. Missions: image metadata, nullable status, composite source index
-- =========================================================================

ALTER TABLE missions
    ADD COLUMN thumbnail_url TEXT AFTER image_url,
    ADD COLUMN image_credit VARCHAR(255) AFTER thumbnail_url,
    ADD COLUMN image_license VARCHAR(100) AFTER image_credit,
    MODIFY COLUMN status VARCHAR(50) NULL,
    DROP INDEX source_id,
    ADD UNIQUE KEY uq_source (source_provider, source_id);

UPDATE missions
SET source_provider = 'll2'
WHERE source_provider = 'launch_library_2';

-- =========================================================================
-- 5. Users: reserved for future authentication
-- =========================================================================

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    auth_provider VARCHAR(50) NOT NULL,
    auth_subject VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_auth (auth_provider, auth_subject)
) ENGINE=InnoDB;

-- =========================================================================
-- 6. Tags: user-defined labels
-- =========================================================================

CREATE TABLE tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================================
-- 7. Mission Tags: connects tags to missions
-- =========================================================================

CREATE TABLE mission_tags (
    mission_id INT NOT NULL,
    tag_id INT NOT NULL,
    created_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mission_id, tag_id),
    FOREIGN KEY (mission_id)
        REFERENCES missions(mission_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)
        REFERENCES tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by)
        REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- =========================================================================
-- Migration 001 complete
-- =========================================================================
