# TASK-9 Handoff: Backend Feature B7 - Layered Validation and Row Results

## Overview
Implemented complete layered validation engine with row-level results, validation issues, and deterministic outcome recording per LLD Section 5.5 and Section 13.1.

## Implemented Endpoints

### GET /api/v1/ingestions/{id}/results
Retrieve paginated row-level validation results with issues.

**Query Parameters:**
- `limit` (integer, default 50): Maximum rows to return
- `offset` (integer, default 0): Number of rows to skip

**Response:**
```json
{
  "items": [
    {
      "row_number": 1,
      "outcome": "accepted",
      "target_record_key": "SITE-0001",
      "issues": []
    },
    {
      "row_number": 2,
      "outcome": "accepted_with_warning",
      "target_record_key": "SITE-0002",
      "issues": [
        {
          "code": "SITE_NAME_LENGTH",
          "severity": "warning",
          "message": "Site name exceeds recommended length",
          "rule_code": "SITE_NAME_LENGTH"
        }
      ]
    },
    {
      "row_number": 3,
      "outcome": "rejected",
      "target_record_key": "SITE-0003",
      "issues": [
        {
          "code": "LATITUDE_RANGE",
          "severity": "error",
          "message": "Invalid latitude: out of range",
          "rule_code": "LATITUDE_RANGE"
        }
      ]
    }
  ],
  "total": 1248,
  "limit": 50,
  "offset": 0
}
```

**Valid Outcomes:**
- `accepted` - All validation checks passed, no warnings
- `accepted_with_warning` - All error-level checks passed, warnings present
- `rejected` - One or more error-level validation failures

**Issue Severities:**
- `error` - Causes row rejection
- `warning` - Flags concern but allows acceptance

## Seed Data

### Ingestion Record: SYN-ING-0107
- **Status:** completed
- **Total Rows:** 1248
- **Accepted:** 1190 rows (clean, no issues)
- **Accepted with Warning:** 36 rows (site_name exceeds recommended length)
- **Rejected:** 22 rows (various validation failures)

### Sample Row Results in Seed

**Accepted Rows (1-10):**
- Clean site data with valid coordinates
- Example: `SITE-0001` at Stockholm coordinates (59.3293, 18.0686)

**Accepted with Warning Rows (11-16):**
- Site names exceeding 50 characters
- Issue: "Site name exceeds recommended length" (warning severity)

**Rejected Rows - Invalid Latitude (17-22):**
- Latitude out of range (95.0 instead of -90 to 90)
- Issue: "Invalid latitude: out of range" (error severity)
- Rule: LATITUDE_RANGE

**Rejected Rows - Missing Required Field (23-26):**
- Missing required field: site_name
- Issue: "Missing required field: site_name" (error severity)
- No rule_code (mapping-level validation)

## Validation Algorithm (LLD Section 5.5)

### Layered Processing Order:
1. **Mapping Layer:** Apply mapping version to source row
   - Check required fields present
   - Issue code: `required_field_missing`

2. **Schema Layer:** Type validation per target_type
   - Validate string, number, date, boolean types
   - Issue codes: `invalid_type`, `SITE_ID_FORMAT`

3. **Business Layer:** Domain rules evaluation
   - Range checks (latitude: -90 to 90, longitude: -180 to 180)
   - Pattern validation
   - Issue codes: `LATITUDE_RANGE`, `LONGITUDE_RANGE`

4. **Warning Layer:** Non-blocking validations
   - Length warnings for site names >50 chars
   - Issue code: `SITE_NAME_LENGTH`

### Outcome Decision Model:
- **Any error-level issue → rejected**
- **Warnings only → accepted_with_warning**
- **No findings → accepted**

## Database Tables

### validation_rule_sets
- `rule_set_code`: Unique identifier (e.g., "SITE_DATA_RULES_V1")
- `version_number`: Rule set version
- `status`: active/superseded
- `checksum_sha256`: Immutable rule set hash

### validation_rules
- `rule_set_id`: FK to validation_rule_sets
- `rule_code`: Rule identifier (e.g., "LATITUDE_RANGE")
- `layer_code`: structural/schema/mapping/business
- `severity`: error/warning
- `expression_json`: Rule parameters (min, max, pattern, etc.)
- `human_message`: User-facing explanation
- `sort_order`: Execution order

### ingestion_row_results
- `ingestion_id`: FK to ingestion_records
- `row_number`: Source row number (1-based)
- `target_record_key`: Optional business key from mapped data
- `mapped_payload_json`: Mapped field values
- `outcome`: accepted/rejected/accepted_with_warning
- UNIQUE constraint on (ingestion_id, row_number) for idempotency

### validation_issues
- `ingestion_id`: FK to ingestion_records
- `ingestion_row_result_id`: FK to ingestion_row_results (nullable for ingestion-level issues)
- `issue_scope`: row/ingestion
- `issue_code`: Machine-readable code
- `severity`: error/warning
- `message`: Human-readable explanation
- `rule_code`: Optional link to validation_rules.rule_code

## Backend Flows

### Validation Pipeline Execution:
1. Ingestion status transitions: submitted → validating → completed
2. Resolve mapping version and validation rule set
3. For each row:
   - Apply mapping (extract and validate required fields)
   - Schema validation (type checks)
   - Business rules evaluation (deterministic rule expressions)
   - Warning checks (non-blocking validations)
   - Determine outcome based on issue severities
   - Create row result record
   - Create validation issue records for errors/warnings
4. Update ingestion summary counts (accepted_count, rejected_count, warning_count)
5. Mark ingestion completed with validation_completed_at_utc

### Background Processing Model (LLD Section 13.1):
- Validation runs asynchronously after structural validation passes
- Shares same backend boundary and relational store
- Idempotent row results with UNIQUE(ingestion_id, row_number)
- Deterministic rule evaluation for auditability

## Frontend Implementation Guidance

### Results List View:
- Display paginated row results from GET /api/v1/ingestions/{id}/results
- Show row_number, outcome, target_record_key
- Use Carbon DataTable with pagination controls
- Outcome badge colors:
  - Green: accepted
  - Yellow: accepted_with_warning
  - Red: rejected

### Issue Display:
- Expand rejected/warning rows to show issues list
- Display issue.message (human-readable)
- Group by severity (errors first, then warnings)
- Show rule_code when available for traceability

### Summary Statistics:
- Display accepted_count, rejected_count, warning_count from ingestion detail
- Show completion percentage: accepted / total
- Warning badge if warning_count > 0
- Error indicator if rejected_count > 0

### Pagination:
- Default: 50 rows per page
- Allow user to select page size (10, 50, 100)
- Show "Rows X-Y of Z" indicator
- Preserve filters/sort when changing pages

## Acceptance Criteria Coverage

### FR-015: Run layered validation before commit
✅ Validation includes structural, schema, business-rule, and mapping-level checks
✅ Each validation issue is associated with a row or ingestion-level context
✅ Validation outcomes distinguish accepted, rejected, and warning scenarios
✅ Commit logic respects the validation decision model

### FR-016: Produce row-level accepted and rejected results with reasons
✅ Each processed row has a recorded outcome
✅ Rejected rows include one or more human-readable reasons
✅ Accepted row counts and rejected row counts are summarized
✅ Result detail is retrievable after processing completes

## Testing

### Unit Tests (test_validation_engine_service.py):
- Validation pipeline success path
- Deterministic outcomes across runs
- Schema validation failure handling
- Business rule validation failure handling
- Warning-only outcome (accepted_with_warning)
- Clean accepted outcome (no findings)

### Integration Tests (test_validation_integration.py):
- Full validation workflow from ingestion to row results
- Validation idempotency on UNIQUE(ingestion_id, row_number)
- Summary counts match actual row result outcomes

### Acceptance Tests (test_validation_acceptance.py):
- FR-015: Layered validation checks coverage
- FR-016: Row-level results with reasons
- Results endpoint pagination (limit=10)

## Validation Rules in Seed

### SITE_DATA_RULES_V1 (Active Rule Set):
1. **SITE_ID_FORMAT** (schema, error)
   - Pattern: `^SITE-[0-9]{4}$`
   - Message: "Site ID must match format SITE-NNNN"

2. **LATITUDE_RANGE** (business, error)
   - Range: -90 to 90
   - Message: "Latitude must be between -90 and 90"

3. **LONGITUDE_RANGE** (business, error)
   - Range: -180 to 180
   - Message: "Longitude must be between -180 and 180"

4. **SITE_NAME_LENGTH** (implicit, warning)
   - Max: 50 characters
   - Message: "Site name exceeds recommended length"

## Next Steps for Frontend

1. **Results Table Component:**
   - Create `IngestionResultsTable.tsx` with Carbon DataTable
   - Implement row expansion for issue details
   - Add outcome badge component with color coding

2. **Results Page:**
   - Route: `/ingestions/:id/results`
   - Fetch results with pagination
   - Display summary statistics at top
   - Show paginated row results below

3. **Integration with Ingestion Detail:**
   - Add "View Results" button on ingestion detail page
   - Navigate to results page when status=completed
   - Show summary counts without navigation for other statuses

4. **Issue Details Modal (Optional):**
   - Show full mapped_payload_json for rejected rows
   - Display all validation issues with severity badges
   - Link to validation rule documentation if available

## Related Files
- `/repos/gembaone/backend/app/repositories/validation_repository.py`
- `/repos/gembaone/backend/app/services/validation_engine_service.py`
- `/repos/gembaone/backend/app/routers/ingestions.py`
- `/repos/gembaone/backend/app/schemas/ingestions.py`
- `/repos/gembaone/backend/app/seed.py` (updated with row results)
- `/repos/gembaone/backend/tests/test_validation_engine_service.py`
- `/repos/gembaone/backend/tests/test_validation_integration.py`
- `/repos/gembaone/backend/tests/test_validation_acceptance.py`
