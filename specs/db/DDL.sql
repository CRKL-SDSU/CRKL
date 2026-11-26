-- =========================================================================
-- Space Exploration API Database Schema (DDL)
-- Target Engine: MySQL / MariaDB
-- =========================================================================

DROP DATABASE IF EXISTS crkl_db;
CREATE DATABASE crkl_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE crkl_db;

-- =========================================================================
-- 1. Master Data: Agencies Table
-- =========================================================================
CREATE TABLE agencies (
    agency_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    abbrev VARCHAR(50),
    country_code VARCHAR(10),
    image_url TEXT,
    thumbnail_url TEXT, -- small square crop of a photo; not used for logos
    image_credit VARCHAR(255),
    image_license VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_source (source_provider, source_id)
) ENGINE=InnoDB;

-- =========================================================================
-- 2. Master Data: Launches Table
-- =========================================================================
CREATE TABLE launches (
    launch_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    net DATETIME NOT NULL,
    status VARCHAR(50) NOT NULL,
    image_url TEXT,
    thumbnail_url TEXT, -- small square crop of a photo; not used for logos
    image_credit VARCHAR(255),
    image_license VARCHAR(100),
    window_start DATETIME,
    window_end DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_source (source_provider, source_id)
) ENGINE=InnoDB;

-- =========================================================================
-- 3. Master Data: Spacecraft Table
-- =========================================================================
CREATE TABLE spacecraft (
    spacecraft_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    spacecraft_type VARCHAR(100),
    image_url TEXT,
    thumbnail_url TEXT, -- small square crop of a photo; not used for logos
    image_credit VARCHAR(255),
    image_license VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_source (source_provider, source_id)
) ENGINE=InnoDB;

-- =========================================================================
-- 4. Core Data: Missions Table
-- =========================================================================
CREATE TABLE missions (
    mission_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_body VARCHAR(100),
    status VARCHAR(50), -- NULL: LL2 missions have no status of their own
    image_url TEXT,
    thumbnail_url TEXT, -- small square crop of a photo; not used for logos
    image_credit VARCHAR(255),
    image_license VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_source (source_provider, source_id)
) ENGINE=InnoDB;

-- =========================================================================
-- 5. Junction Table: Mission Agencies
-- =========================================================================
CREATE TABLE mission_agencies (
    mission_id INT NOT NULL,
    agency_id INT NOT NULL,
    role VARCHAR(50) DEFAULT 'Primary',
    PRIMARY KEY (mission_id, agency_id),
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id) ON DELETE CASCADE,
    FOREIGN KEY (agency_id) REFERENCES agencies(agency_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================================
-- 6. Junction Table: Mission Spacecraft
-- =========================================================================
CREATE TABLE mission_spacecraft (
    mission_id INT NOT NULL,
    spacecraft_id INT NOT NULL,
    PRIMARY KEY (mission_id, spacecraft_id),
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id) ON DELETE CASCADE,
    FOREIGN KEY (spacecraft_id) REFERENCES spacecraft(spacecraft_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================================
-- 7. Junction Table: Mission Launches
-- =========================================================================
CREATE TABLE mission_launches (
    mission_id INT NOT NULL,
    launch_id INT NOT NULL,
    PRIMARY KEY (mission_id, launch_id),
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id) ON DELETE CASCADE,
    FOREIGN KEY (launch_id) REFERENCES launches(launch_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =========================================================================
-- 8. Users (reserved for authentication; tags are anonymous for now)
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
-- 9. Tags: user-defined labels, stored normalized (lowercase, single spaces)
-- =========================================================================
CREATE TABLE tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================================
-- 10. Junction Table: Mission Tags
-- =========================================================================
CREATE TABLE mission_tags (
    mission_id INT NOT NULL,
    tag_id INT NOT NULL,
    created_by INT NULL, -- NULL: added anonymously
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (mission_id, tag_id),
    FOREIGN KEY (mission_id) REFERENCES missions(mission_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;
