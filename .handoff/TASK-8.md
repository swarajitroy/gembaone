# Task 8 Handoff: Mapping Management and Validation Structure

## Overview
This task implements the mapping management system that allows users to define, version, and manage source-to-target field mappings for Excel ingestion. Mappings validate workbook structure before data validation and ensure required target fields are mapped.

## Implemented Endpoints

### POST /api/v1/mappings
Create a new mapping definition with initial entries.

**Request:**
```json
{
  "mapping_code": "MAP-SYN-001",
  "source_entity": "Excel Site Inventory",
  "target_entity": "SYN Site Inventory",
  "entries": [
    {
      "source_column": "site_id",
      "target_field": "site_id",
      "target_type": "string",
      "is_required": true,
      "transform_expression": null
    },
    {
      "source_column": "site_name",
      "target_field": "site_name",
      "target_type": "string",
      "is_required": true
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "mapping_code": "MAP-SYN-001",
  "source_entity": "Excel Site Inventory",
  "target_entity": "SYN Site Inventory",
  "status": "active",
  "created_by_user_id": 1,
  "created_at_utc": "2024-01-15T10:30:00Z",
  "updated_at_utc": "2024-01-15T10:30:00Z",
  "current_version": {
    "id": 1,
    "mapping_definition_id": 1,
    "version_number": 1,
    "version_label": "v1.0",
    "status": "active",
    "published_at_utc": "2024-01-15T10:30:00Z",
    "published_by_user_id": 1,
    "created_at_utc": "2024-01-15T10:30:00Z",
    "entries": [
      {
        "id": 1,
        "mapping_version_id": 1,
        "source_column": "site_id",
        "target_field": "site_id",
        "target_type": "string",
        "is_required": true,
        "transform_expression": null,
        "created_at_utc": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

**Validation:**
- Mapping code must be unique (400 if duplicate)
- At least one entry required (400 if empty)
- No duplicate source columns (400 if duplicates)
- Valid target types: `string`, `number`, `date`, `boolean` (400 if invalid)

### GET /api/v1/mappings
List all mapping definitions with their active versions.

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "mapping_code": "MAP-SYN-001",
      "source_entity": "Excel Site Inventory",
      "target_entity": "SYN Site Inventory",
      "status": "active",
      "created_by_user_id": 1,
      "created_at_utc": "2024-01-15T10:30:00Z",
      "updated_at_utc": "2024-01-15T10:30:00Z",
      "current_version": {
        "id": 2,
        "mapping_definition_id": 1,
        "version_number": 2,
        "version_label": "v2.0",
        "status": "active",
        "published_at_utc": "2024-01-15T11:00:00Z",
        "published_by_user_id": 1,
        "created_at_utc": "2024-01-15T11:00:00Z",
        "entries": [...]
      }
    }
  ],
  "total": 1
}
```

### POST /api/v1/mappings/{id}/versions
Publish a new version of a mapping definition.

**Request:**
```json
{
  "version_label": "v2.0",
  "entries": [
    {
      "source_column": "site_id",
      "target_field": "site_id",
      "target_type": "string",
      "is_required": true
    },
    {
      "source_column": "site_name",
      "target_field": "site_name",
      "target_type": "string",
      "is_required": true
    },
    {
      "source_column": "latitude",
      "target_field": "latitude",
      "target_type": "number",
      "is_required": true
    },
    {
      "source_column": "longitude",
      "target_field": "longitude",
      "target_type": "number",
      "is_required": true
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "mapping_definition_id": 1,
  "version_number": 2,
  "version_label": "v2.0",
  "status": "active",
  "published_at_utc": "2024-01-15T11:00:00Z",
  "published_by_user_id": 1,
  "created_at_utc": "2024-01-15T11:00:00Z",
  "entries": [...]
}
```

**Behavior:**
- Creates new version with incremented version number
- Marks previous active version as "superseded"
- Only one version can have "active" status at a time
- Version history is preserved (superseded versions remain queryable)

## Seed Data

### Mapping: MAP-SYN-001 "SYN Site Inventory"
- **Status:** active
- **Active Version:** v2.0 (version_number: 2)
- **Previous Version:** v1.0 (version_number: 1, status: superseded)
- **Entries (v2.0 - 4 required fields):**
  1. `site_id` → `site_id` (string, required)
  2. `site_name` → `site_name` (string, required)
  3. `latitude` → `latitude` (number, required)
  4. `longitude` → `longitude` (number, required)

### Ingestion Record Using MAP-SYN-001
- **Record:** SYN-ING-0107 (completed, 1248 rows)
- **Uses:** MAP-SYN-001 v2.0 (active version)
- This ingestion record demonstrates the linkage between mapping versions and ingestion runs

## Backend Flows

### Create Mapping Flow
1. Validate mapping code uniqueness
2. Validate entries (no duplicates, valid types, at least one entry)
3. Create mapping definition with status "active"
4. Create initial version (v1.0) with status "active"
5. Create mapping entries for the version
6. Commit transaction
7. Return response with mapping definition and current version

### Publish Version Flow
1. Validate mapping definition exists (404 if not found)
2. Validate entries (same rules as create)
3. Get next version number (max + 1)
4. Find current active version
5. Mark current active version as "superseded"
6. Create new version with status "active"
7. Create mapping entries for new version
8. Commit transaction
9. Return new version response

### Validation Rules
- **Duplicate Source Columns:** Rejected with 400 error
- **Invalid Target Types:** Must be one of: string, number, date, boolean
- **Empty Entries:** At least one entry required
- **Required Field Mapping:** During ingestion, all target fields marked as `is_required: true` must be mapped

### Version Status Transitions
- **active:** Currently used version for new ingestions
- **superseded:** Previous version replaced by newer active version
- Only one version per mapping definition can be "active" at a time

## Database Schema

### mapping_definitions
- `id` (PK, auto-increment)
- `mapping_code` (TEXT, unique, not null)
- `source_entity` (TEXT, not null)
- `target_entity` (TEXT, not null)
- `status` (TEXT, not null)
- `created_by_user_id` (FK to users)
- `created_at_utc`, `updated_at_utc`

### mapping_versions
- `id` (PK, auto-increment)
- `mapping_definition_id` (FK to mapping_definitions)
- `version_number` (INTEGER, not null)
- `version_label` (TEXT, not null)
- `status` (TEXT, not null) - "active" or "superseded"
- `published_at_utc` (nullable)
- `published_by_user_id` (FK to users, nullable)
- `created_at_utc`

### mapping_entries
- `id` (PK, auto-increment)
- `mapping_version_id` (FK to mapping_versions)
- `source_column` (TEXT, not null)
- `target_field` (TEXT, not null)
- `target_type` (TEXT, not null)
- `is_required` (BOOLEAN, not null)
- `transform_expression` (TEXT, nullable)
- `created_at_utc`

## FR-012 Acceptance Criteria Coverage

**FR-012: Validate workbook structure before mapping**

✅ **The system checks workbook readability and required sheet presence where configured.**
- Mapping definitions specify expected source columns
- Ingestion flow uses mapping to validate workbook structure before row-level validation

✅ **The system identifies missing headers or unsupported workbook conditions before row validation.**
- Mapping entries define source columns that must exist
- Structural validation (implemented in Task 7) checks against mapping configuration

✅ **Structural validation failures are recorded against the ingestion attempt.**
- Ingestion records link to mapping version used
- Status "failed" with failure_detail for structural issues

✅ **Users receive a readable failure message when structural validation blocks further processing.**
- 400 errors with descriptive detail messages
- Ingestion failure_detail field contains human-readable reasons

## FR-013 Acceptance Criteria Coverage

**FR-013: Configure source-to-target field mappings**

✅ **Authorized users can define mappings between source columns and target fields.**
- POST /api/v1/mappings creates new mapping definitions
- Authenticated users with proper roles can create mappings

✅ **Mappings are versioned or otherwise tracked over time.**
- mapping_versions table with version_number and version_label
- Version history preserved (superseded versions retained)

✅ **An ingestion run records which mapping definition was used.**
- ingestion_records.mapping_version_id links to specific version
- Seed data: SYN-ING-0107 uses MAP-SYN-001 v2.0

✅ **Unmapped required target fields are flagged before commit.**
- mapping_entries.is_required identifies required fields
- Validation can check all required target fields are present in entries
- Ingestion flow validates required fields mapped before processing rows

## Frontend Implementation Guidance

### Mapping List View
- Display all mappings from GET /api/v1/mappings
- Show mapping code, source/target entities, active version
- Table columns: Mapping Code, Source Entity, Target Entity, Active Version, Status

### Create Mapping Form
- Form fields: mapping_code, source_entity, target_entity
- Dynamic entry rows with: source_column, target_field, target_type (dropdown), is_required (checkbox), transform_expression (optional)
- Add/remove entry rows
- Validation: unique source columns, at least one entry
- POST to /api/v1/mappings

### Publish New Version
- Load existing mapping details
- Allow editing entries
- Show version history (v1.0 superseded, v2.0 active)
- POST to /api/v1/mappings/{id}/versions

### Ingestion Upload Integration
- Dropdown to select active mapping version
- Display mapping code and version label
- Pass mapping_version_id to ingestion upload endpoint

## Testing

### Unit Tests (11 tests)
- `test_mapping_service.py`: Service layer logic
  - Create mapping definition
  - Duplicate code rejection
  - Duplicate source columns rejection
  - Empty entries rejection
  - Invalid target type rejection
  - Publish version
  - Version supersede behavior
  - List mappings
  - Resolve active mapping

### Integration Tests (3 tests)
- `test_mapping_integration.py`: Database operations
  - Full CRUD workflow
  - Version supersede flow
  - Required field validation

### Acceptance Tests (9 tests)
- `test_mapping_acceptance.py`: API endpoints
  - POST /api/v1/mappings
  - GET /api/v1/mappings
  - POST /api/v1/mappings/{id}/versions
  - Version supersede verification
  - Validation scenarios
  - FR-012 and FR-013 acceptance criteria

## Authentication
All endpoints require authenticated user via `get_current_user` dependency.

## Error Responses
- **400 Bad Request:** Validation errors (duplicate code, invalid type, etc.)
- **404 Not Found:** Mapping definition not found when publishing version
- **401 Unauthorized:** Missing or invalid authentication token
