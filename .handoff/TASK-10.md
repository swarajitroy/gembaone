# TASK-10 Handoff: Raw File Retention and Report Download

## Endpoints Added

### GET /api/v1/ingestions/{id}/raw-file

Returns signed download URL for the raw uploaded file.

**Response:**
```json
{
  "download_url": "string",
  "expires_at": "2026-11-12T10:15:30Z",
  "original_filename": "site_data_batch_0107.xlsx",
  "byte_size": 153600
}
```

**Permission:** ASP users can only download their own files.

**Audit:** Creates `raw_file_download` audit event with correlation ID.

---

### GET /api/v1/ingestions/{id}/report

Returns signed download URL for the result report.

**Response:**
```json
{
  "download_url": "string",
  "expires_at": "2026-11-12T10:15:30Z",
  "report_type": "csv",
  "generated_at": "2026-11-12T09:15:00Z"
}
```

**Permission:** ASP users can only download their own reports.

**Audit:** Creates `report_download` audit event with correlation ID.

---

## Seed Data

### Ingestion SYN-ING-0107

**Status:** completed  
**Uploaded by:** admin@example.com  
**Raw file:** `site_data_batch_0107.xlsx` (150KB)  
**Mapping:** MAP-SYN-001 v2.0  
**Validation:** SITE_DATA_RULES_V1  
**Results:** 1190 accepted, 36 accepted_with_warning, 22 rejected  

**Generated Report:**
- Type: CSV
- Generated at: 2026-11-12T09:15:00Z
- File size: 128KB
- Contains: Header row + data rows with columns (row_number, outcome, target_record_key, issues_summary, mapped_payload_excerpt)

**Sample row results:**
- Rows 1-10: accepted (no issues)
- Rows 11-16: accepted_with_warning (site name length warnings)
- Rows 17-22: rejected (latitude range errors)
- Rows 23-26: rejected (missing required field)

---

## Backend Flow

### Raw File Access

1. User requests GET `/api/v1/ingestions/{id}/raw-file`
2. Service checks ingestion exists and user has permission (ASP users: own files only)
3. Service retrieves `file_objects` record via `raw_file_object_id` FK
4. Object storage adapter generates signed URL with 1-hour expiry
5. Audit service records `raw_file_download` event with correlation ID
6. Response includes URL, expiry timestamp, filename, and byte size

### Report Download

1. User requests GET `/api/v1/ingestions/{id}/report`
2. Service checks ingestion exists and user has permission (ASP users: own reports only)
3. Service retrieves `generated_reports` record for ingestion
4. Service retrieves report `file_objects` record via `file_object_id` FK
5. Object storage adapter generates signed URL with 1-hour expiry
6. Audit service records `report_download` event with correlation ID
7. Response includes URL, expiry timestamp, report type, and generation timestamp

### Report Generation (Internal)

Report generation is triggered by `ReportService.generate_result_report()`:

1. Validates ingestion status is `completed`
2. Retrieves all row results with pagination (up to 10,000 rows)
3. For each row, retrieves validation issues
4. Generates CSV with columns: row_number, outcome, target_record_key, issues_summary, mapped_payload_excerpt
5. Stores CSV via object storage adapter (bucket: `ingestion-reports`)
6. Creates `file_objects` record with immutable flag
7. Creates `generated_reports` record linking ingestion and file object

---

## Database Schema

### generated_reports

- `id`: Primary key
- `ingestion_id`: FK to ingestion_records (indexed)
- `file_object_id`: FK to file_objects
- `report_type`: Type of report (e.g., 'csv')
- `generated_at_utc`: Generation timestamp
- `generated_by_user_id`: FK to users

**Relationships:**
- One report per ingestion (1:1)
- Report links to file_objects for report file storage

---

## Immutability

**Raw File Immutability:**
- Raw files stored via `file_objects` with `immutable_flag=True`
- Ingestion record stores stable `raw_file_object_id` FK
- Platform prevents silent replacement of raw file within same ingestion record (FK constraint ensures reference remains valid)

**Report Immutability:**
- Report files stored with `immutable_flag=True`
- Generated report record preserves `generated_at_utc` and `generated_by_user_id`
- Report content corresponds to ingestion row results at generation time

---

## Acceptance Criteria Coverage

### FR-019 (Raw File Retention)

✓ Uploaded file retained outside mutable business record fields (separate `file_objects` table with immutable flag)  
✓ Ingestion record stores stable reference (`raw_file_object_id` FK)  
✓ Platform prevents silent replacement (FK constraint + immutable flag)  
✓ Authorized users can retrieve raw file metadata (GET endpoint with permission check)

### FR-020 (Report Download)

✓ Completed ingestion exposes downloadable report (GET endpoint returns signed URL)  
✓ Report contains accepted/rejected outcomes and reasons (CSV with row outcomes + issues summary)  
✓ Report content corresponds to ingestion record viewed (report linked via `ingestion_id`)  
✓ Downloads are auditable (audit events created with correlation IDs)

---

## Frontend Implementation Guidance

### Raw File Download Button

Display download button on ingestion detail page when `status !== 'failed'`:

```typescript
const handleRawFileDownload = async (ingestionId: number) => {
  const response = await fetch(`/api/v1/ingestions/${ingestionId}/raw-file`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const data = await response.json();
  
  // Open signed URL in new tab or trigger download
  window.open(data.download_url, '_blank');
};
```

### Report Download Button

Display download button on ingestion detail page when `status === 'completed'` and report exists:

```typescript
const handleReportDownload = async (ingestionId: number) => {
  try {
    const response = await fetch(`/api/v1/ingestions/${ingestionId}/report`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (response.status === 404) {
      // Report not generated yet - show generate button instead
      return;
    }
    
    const data = await response.json();
    window.open(data.download_url, '_blank');
  } catch (error) {
    console.error('Report download failed:', error);
  }
};
```

### Error Handling

- 403: "Access denied to this file/report" → Show permission error
- 404 (raw-file): "Raw file not found" → Unusual, should not occur for valid ingestion
- 404 (report): "Report not found" → Show "Generate Report" button instead
- 400 (report generation): "Report can only be generated for completed ingestions" → Disable button for non-completed

---

## Security & Permission Model

**ASP User Restrictions:**
- ASP users can only download raw files and reports for ingestions they uploaded
- Internal admins can download any raw file or report
- Permission check enforced at service layer before generating download URL
- 403 returned if ASP user attempts to access another user's file/report

**Audit Trail:**
- Every raw file download creates audit event
- Every report download creates audit event
- Audit events include correlation ID for request tracing
- Actor user ID recorded for accountability
