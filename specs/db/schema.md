# Database Schema

## Overview

This database architecture is designed for a space exploration information portal, aligning with the Launch Library 2 (LL2) API standards and design-first specifications. It incorporates master data tables for agencies, launches, spacecraft, and missions, supported by Class Table Inheritance patterns for data sources, taxonomy tagging, and system synchronization logging.

## Entities Summary

- **sources**: Base table for all data sources containing shared network and status metadata (Class Table Inheritance base).
- **organizations** (or **agencies**): Sub-type table extending sources with organization-specific attributes (name, abbreviation, country code, image URL).
- **launches**: Master table tracking launch events, including launch windows, status, and net (No-Earlier-Than) times.
- **spacecraft**: Master table storing spacecraft variations, types, and technical specifications.
- **missions**: Core table tracking specific space missions, target bodies, statuses, and descriptive metadata.
- **mission_agencies**: Junction table connecting missions to agencies with assigned operational roles (e.g., Primary, Contributor).
- **mission_spacecraft**: Junction table linking missions to the spacecraft assets utilized during the operation.
- **mission_launches**: Junction table connecting missions to their respective launch events.
- **tags**: Taxonomy structure used for filtering and categorizing missions.
- **mission_tags**: Junction table connecting missions to tags.
- **sync_logs**: Execution logs for API crawlers to monitor system health, rate limits, and synchronization states.

## Relationships & Architecture

- **Missions & Master Data**: Missions maintain many-to-many relationships with agencies, spacecraft, and launches via dedicated junction tables (`mission_agencies`, `mission_spacecraft`, `mission_launches`), supporting rich nested JSON payload generation for frontend consumption.
- **Source Provider Tracking**: Master records incorporate source provider identifiers (`source_provider`, `source_id`) to ensure seamless upstream synchronization and data provenance tracking.

## Future Considerations: Handling Unbound Entities (Launch / Spacecraft)

In our Phase 1 design, we adopted a **Mission-Centric** model where `launches` and `spacecraft` are tightly coupled to `missions`. However, if the business requirements or data sources reveal independent entities that exist without a direct parent mission (e.g., test flights, orbital tests of raw boosters, or unassigned spacecraft reserves), the database architecture must be refactored with the following key steps:

### 1. Re-introducing `agency_id` to Child Tables
* **Action**: Restore the `agency_id` foreign key column to both `launches` and `spacecraft` tables.
* **Rationale**: Independent launches (like commercial rideshares or test flights) and standalone spacecraft are directly operated or owned by an agency (`agencies`), bypassing the `missions` entity.
