-- =========================================================================
-- Space Exploration API Database Schema (DDL)
-- Target Engine: MySQL / MariaDB
-- =========================================================================

DROP DATABASE IF EXISTS space_exploration_db;
CREATE DATABASE space_exploration_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE space_exploration_db;

-- =========================================================================
-- 1. Master Data: Agencies Table
-- =========================================================================
CREATE TABLE agencies (
    agency_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    abbrev VARCHAR(50),
    country_code VARCHAR(10),
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================================
-- 2. Master Data: Launches Table
-- =========================================================================
CREATE TABLE launches (
    launch_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    net DATETIME NOT NULL,
    status VARCHAR(50) NOT NULL,
    image_url TEXT,
    window_start DATETIME,
    window_end DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================================
-- 3. Master Data: Spacecraft Table
-- =========================================================================
CREATE TABLE spacecraft (
    spacecraft_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    spacecraft_type VARCHAR(100),
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =========================================================================
-- 4. Core Data: Missions Table
-- =========================================================================
CREATE TABLE missions (
    mission_id INT AUTO_INCREMENT PRIMARY KEY,
    source_provider VARCHAR(50) NOT NULL,
    source_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_body VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
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
