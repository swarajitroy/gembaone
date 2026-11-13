# TASK-7 Handoff: Backend Feature B5 - Ingestion Upload and Lifecycle

## Implemented Endpoints

### POST /api/v1/ingestions
Upload Excel file for ingestion.

**Request:** Multipart form data
- `file`: Binary .xlsx file
- `mapping_version_id`: Integer ID of mapping version to use

**Response:** IngestionResponse
```json
{
  "id": 1,
  "status": "submitted",
  "uploaded_by": 1,
  "uploaded_at": "2026-11-12T10:30:00Z",
  "source_filename": "site_data_batch_0107.xlsx",
  "raw_file_object_id": 1,
  "mapping_version_id": 1,
  "validation_rule_set_id": 1,
  "validation_started_at": null,
  "validation_completed_at": null,
  "accepted_count": 0,
  "rejected_count": 0,
  "warning_count": 0,
  "failure_detail": null
}
```

**Status codes:**
- 200: Upload successful
- 400: Invalid file type, size exceeded, or validation error
- 401: Not authenticated
- 403: Permission denied

**Validation rules:**
- Only `.xlsx` files accepted
- Maximum file size: 25MB
- File stored immutably in object storage
- Creates ingestion record with `status=submitted`
- Creates ingestion_event with correlation ID

---

### GET /api/v1/ingestions
List ingestions with ASP visibility scoping.

**Response:** IngestionListResponse with `{items, total}`
```json
{
  "items": [
    {
      "id": 1,
      "status": "completed",
      "uploaded_by": 1,
      "uploaded_at": "2026-11-12T10:30:00Z",
      "source_filename": "site_data_batch_0107.xlsx",
      "raw_file_object_id": 1,
      "mapping_version_id": 1,
      "validation_rule_set_id": 1,
      "validation_started_at": "2026-11-12T10:30:05Z",
      "validation_completed_at": "2026-11-12T10:30:15Z",
      "accepted_count": 1248,
      "rejected_count": 0,
      "warning_count": 0,
      "failure_detail": null
    }
  ],
  "total": 1
}
```

**Visibility scoping:**
- Internal admins: See all ingestions
- ASP users: See only their own ingestions

---

### GET /api/v1/ingestions/{id}
Retrieve ingestion detail with ASP visibility scoping.

**Response:** IngestionDetailResponse
```json
{
  "id": 2,
  "status": "failed",
  "source_filename": "site_data_batch_0105.xlsx",
  "mapping_version_id": 1,
  "validation_rule_set_id": 1,
  "raw_file_object_id": 2,
  "uploaded_by": 1,
  "uploaded_at": "2026-11-12T10:25:00Z",
  "validation_started_at": null,
  "validation_completed_at": null,
  "accepted_count": 0,
  "rejected_count": 0,
  "warning_count": 0,
  "failure_detail": "Required sheet 'Sites' not found"
}
```

**Status codes:**
- 200: Success
- 403: ASP user accessing another user's ingestion
- 404: Ingestion not found

---

## Seed Data

### Ingestion: SYN-ING-0107 (Completed)
- **Status:** `completed`
- **Source filename:** `site_data_batch_0107.xlsx`
- **Uploaded by:** admin@example.com
- **Raw file object ID:** Links to file_objects record with immutable_flag=True
- **Accepted count:** 1248 rows
- **Rejected count:** 0
- **Warning count:** 0
- **Failure detail:** null

### Ingestion: SYN-ING-0105 (Failed Structural Validation)
- **Status:** `failed`
- **Source filename:** `site_data_batch_0105.xlsx`
- **Uploaded by:** admin@example.com
- **Raw file object ID:** Links to file_objects record with immutable_flag=True
- **Failure detail:** "Required sheet 'Sites' not found"

---

## Backend Flow

### Upload Flow (Synchronous)
1. User uploads .xlsx file via POST /api/v1/ingestions
2. File type and size validation (400 if fails)
3. File stored immutably via object_storage adapter
4. file_objects metadata record created with `immutable_flag=True`
5. ingestion_records created with `status=submitted`
6. ingestion_events created with `event_type=ingestion_uploaded`, correlation ID
7. Response returned with ingestion ID and status

### Structural Validation Algorithm (LLD Section 5.4)
Implemented in `workbook_validation_service.py`:

1. **Resolve immutable raw workbook reference** - File stored in object storage
2. **Check workbook readable** - If no: record structural failure, mark `status=failed`, stop
3. **Verify xlsx content type and extension** - Validated in upload
4. **Check required sheets present** - If no: fail sheets with ingestion-level validation issue, stop
5. **Validate configured header set** - If headers not OK: fail headers with structural validation issues, stop
6. **Resolve active mapping version** - Already linked in ingestion record
7. **Transition ingestion to `status=validating`** - Pass structure, record validation_started_at_utc

### Lifecycle Events
Every status transition creates an ingestion_event with:
- `ingestion_id`: Link to ingestion record
- `event_type`: e.g., `ingestion_uploaded`, `validation_started`, `validation_failed`
- `from_status` and `to_status`: Status transition
- `event_message`: Human-readable message
- `event_at_utc`: Timestamp
- `actor_user_id`: User who triggered event (null for system)
- `correlation_id`: Request correlation ID for tracing

---

## Immutability and Security

### File Immutability
- All uploaded files stored with `immutable_flag=True` in file_objects
- Files cannot be silently replaced
- SHA256 checksums computed and stored for verification

### ASP Visibility Restrictions
- ASP users can only upload ingestions (ingestion_upload permission)
- ASP users can only list/view their own ingestions
- Internal admins can list/view all ingestions
- Enforced at service layer via permission_service

---

## Row Validation (Placeholder)
Row validation is implemented in the next task (TASK-8). Current implementation:
- Structural validation passes: transition to `status=validating`
- Actual row-by-row validation and result recording: future task
- Ingestion remains in `validating` status until row validation completes

---

## Frontend Implementation Guidance

### Upload Screen
- File input accepting only `.xlsx` files
- Mapping version selector (dropdown - mapping version ID must be provided, endpoint to list mapping versions will be implemented in future task)
- Upload button disabled until file selected and mapping chosen
- Progress indicator during upload
- Error handling for 400 (invalid file), 403 (permission), 500 (server error)
- Success redirect to ingestion detail page

### Ingestion List Screen
- Table showing: source_filename, status, uploaded_at, accepted_count, rejected_count, warning_count
- Status badge with colors: submitted (blue), validating (yellow), completed (green), failed (red)
- Filter by status
- Search by filename
- Sort by uploaded_at (default: newest first)
- Click row to navigate to detail page
- ASP users see only own records automatically

### Ingestion Detail Screen
- Header: source_filename, status badge, uploaded_at
- Metadata section: uploaded_by, mapping_version, validation_rule_set
- Counts section: accepted_count, rejected_count, warning_count (if status=completed)
- Failure detail section: failure_detail text (if status=failed)
- Timeline section: Show ingestion_events (future enhancement)
- Download raw file button: (download endpoint not yet implemented - future task)

---

## Testing Coverage

### Unit Tests (test_ingestion_service.py)
- ✓ Create ingestion success
- ✓ Invalid file extension rejected
- ✓ File too large rejected
- ✓ ASP visibility scoping in list
- ✓ ASP denied access to other user's ingestion

### Unit Tests (test_workbook_validation_service.py)
- ✓ Validation with ingestion not found
- ✓ Missing required sheet fails validation
- ✓ File not readable fails validation
- ✓ Validation creates ingestion events

### Integration Tests (test_ingestion_integration.py)
- ✓ Complete upload workflow
- ✓ Ingestion lifecycle transitions
- ✓ Events created with correlation ID

### Acceptance Tests (test_ingestion_acceptance.py)
- ✓ POST /api/v1/ingestions accepts .xlsx
- ✓ POST rejects non-.xlsx files
- ✓ POST rejects files >25MB
- ✓ GET /api/v1/ingestions enforces ASP visibility
- ✓ GET /api/v1/ingestions/{id} returns detail

---

## Acceptance Criteria Coverage

### FR-011: Upload Excel files for ingestion
- ✓ Upload flow accepts supported `.xlsx` files only
- ✓ Platform validates file presence, type, and maximum size before processing
- ✓ Each upload assigned unique ingestion record
- ✓ Unauthorized users cannot access upload action

### FR-018: Record ingestion status and lifecycle history
- ✓ Ingestion records include status values: submitted, validating, completed, failed
- ✓ Status changes are timestamped
- ✓ Users can retrieve current and prior ingestion statuses via events
- ✓ Status visibility follows role restrictions (ASP scoping)

---

## Dependencies and Integration Points

### Required by Frontend
- Mapping version ID must be provided during upload (mapping versions list endpoint not yet implemented - future task)
- Authentication and permission checks enforced via middleware
- Correlation ID from request headers for event tracking

### Integrates With
- object_storage adapter for file storage
- permission_service for ASP visibility enforcement
- audit logging via ingestion_events table
- mapping_versions for active mapping resolution
- validation_rule_sets for validation configuration

---

## Known Limitations and Next Steps

### Current Limitations
- Structural validation requires openpyxl library (added to dependencies)
- Row validation is placeholder only - implemented in next task
- No download endpoint for raw files yet
- No validation_issues detail view yet

### Next Task (TASK-8)
Will implement:
- Row-by-row validation per LLD Section 5.5
- ingestion_row_results table population
- validation_issues detail recording
- Transition to `status=completed` or remain `failed`
- Result retrieval endpoints
