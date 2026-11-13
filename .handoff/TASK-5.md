# Task 5 Handoff: Backend Feature B3 - Structured Answers and Evidence Capture

## Implemented Endpoints

### PUT /api/v1/checklists/{id}/answers
Upsert answers for checklist instance and re-evaluate conditional visibility.

**Request:**
```json
{
  "answers": [
    {
      "item_id": 123,
      "value_type": "text",
      "value_text": "Obstructed",
      "value_number": null,
      "value_boolean": null,
      "value_date": null,
      "value_json": null
    }
  ]
}
```

**Response:** ChecklistInstanceResponse with updated visibility_trace_json
```json
{
  "id": 1,
  "template_version_id": 1,
  "title": "SYN-CL-0042",
  "status": "draft",
  "visibility_trace_json": "{\"site_access\": {\"visible\": true, \"required\": true, \"has_condition\": false}, \"obstruction_details\": {\"visible\": true, \"required\": true, \"has_condition\": true}, \"site_photo\": {\"visible\": true, \"required\": false, \"has_condition\": false}}",
  "created_by_user_id": 2,
  "created_at_utc": "2026-11-12T10:00:00Z",
  "submitted_by_user_id": null,
  "submitted_at_utc": null
}
```

**Value Types:** text, number, boolean, date, json

**Visibility Evaluation:**
- After each answer upsert, conditional visibility is re-evaluated per LLD Section 5.3
- Items with conditions check source answers
- Supported operators: equals, not_equals, contains, greater_than, less_than
- Hidden items are marked as not required
- visibility_trace_json contains current visibility state for all items

### POST /api/v1/checklists/{id}/attachments
Upload attachment (photo or file) for checklist item.

**Request:** Multipart form data
```
item_id: 456 (form field)
file: binary (file upload)
```

**Response:** AttachmentResponse
```json
{
  "id": 1,
  "file_object_id": 1,
  "original_filename": "site_photo_1.jpg",
  "content_type": "image/jpeg",
  "byte_size": 51200,
  "sha256_hex": "abc123...",
  "uploaded_by_user_id": 2,
  "uploaded_at_utc": "2026-11-12T10:05:00Z"
}
```

**Allowed Content Types:**
- image/jpeg
- image/png
- image/gif
- application/pdf

**Validation:**
- File type must be in allowed list (400 if not)
- File size must not exceed 25MB (400 if exceeded)
- SHA256 checksum computed and stored
- Files stored immutably in object storage

## Seed Data

### Checklist Instance SYN-CL-0042
- **Status:** draft
- **Template:** SITE_SURVEY_V1 v1.0
- **Created by:** engineer@example.com

### Items in SYN-CL-0042:
1. **site_access** (select): Site access condition
   - Choices: Clear, Obstructed, Locked
   - No condition
2. **obstruction_details** (text): Obstruction details
   - Conditional: visible only if site_access = "Obstructed"
3. **site_photo** (file): Site photo
   - Evidence required
   - No condition

### Answers in SYN-CL-0042:
1. site_access = "Obstructed" (triggers conditional visibility)
2. obstruction_details = "Large tree blocking access"

### Attachments in SYN-CL-0042:
2 sample file_objects linked to site_photo item:
- site_photo_1.jpg (50KB synthetic JPEG, sha256: synthetic_sha256_seed_001)
- site_photo_2.jpg (50KB synthetic JPEG, sha256: synthetic_sha256_seed_002)

Both uploaded by engineer@example.com

### Locations:
Instance-level location at Stockholm coordinates (59.3293, 18.0686), accuracy 10m

## Backend Flow

### Answer Upsert:
1. Validate item belongs to instance
2. Validate value matches type (text requires value_text, number requires value_number, etc.)
3. Upsert answer (update existing or create new)
4. Re-evaluate conditional visibility for all items
5. Update instance.visibility_trace_json with current state
6. Record audit event

### Visibility Evaluation (LLD Section 5.3):
1. Load all instance items in display order
2. Get all current answers
3. For each item:
   - Default: visible and required as configured
   - If has condition:
     - Find source item and its answer
     - Compare answer value to expected value using operator
     - If condition satisfied: visible=True, required as configured
     - If condition not satisfied: visible=False, required=False
4. Return visibility trace dict

### Attachment Upload:
1. Validate instance and item exist
2. Validate file type (must be in allowed list)
3. Validate file size (must be ≤ 25MB)
4. Compute SHA256 checksum
5. Generate unique storage key (UUID-based)
6. Store file via object storage adapter (local: backend/uploads/checklist-attachments/<key>)
7. Create file_objects metadata record (immutable_flag=True)
8. Create checklist_attachments linking file to instance and item
9. Record uploader and timestamp

### Object Storage:
- **Local mode:** Files stored in backend/uploads/<bucket>/<key>
- **Production mode:** Would use cloud storage (S3/Azure/GCS) - adapter pattern ready
- All files are immutable
- SHA256 checksums ensure integrity

## Acceptance Criteria Coverage

### FR-004 (Capture structured answers):
✓ Answers are stored per checklist item with defined data types
✓ The platform rejects malformed values that do not match the item type
✓ Submitted answers can be retrieved in a structured response format
✓ Structured responses are preserved independently of display formatting

### FR-005 (Attach photos and files):
✓ Users can upload a supported file type to an eligible checklist item
✓ The attachment is linked to the checklist instance and item
✓ The system records uploader and timestamp for each attachment
✓ Attachment access follows role permissions

## Test Coverage

### Unit Tests:
- test_answer_service.py: 5 tests for conditional visibility evaluation
  - No condition baseline
  - Satisfied equality condition
  - Unsatisfied equality condition
  - Numeric threshold (greater_than)
  - Hidden item bypass (non-required)
  
- test_evidence_service.py: 5 tests for attachment upload
  - Successful upload
  - Invalid file type rejection (400)
  - Size limit enforcement (400)
  - Item not found (404)
  - SHA256 checksum recording

### Integration Tests:
- test_answer_integration.py: 3 tests
  - Answer upsert with visibility re-evaluation
  - Answer type validation
  - Upsert updates existing (no duplicates)
  
- test_evidence_integration.py: 3 tests
  - Complete attachment upload flow
  - File type validation
  - File size validation

### Acceptance Tests:
- test_answer_acceptance.py: 4 tests for FR-004
- test_evidence_acceptance.py: 4 tests for FR-005

**Total:** 24 tests

## Notes for Frontend Implementation

1. **Answer submission:** Use PUT /api/v1/checklists/{id}/answers with array of answers
2. **Visibility handling:** After each answer update, check visibility_trace_json to show/hide conditional items
3. **File upload:** Use multipart/form-data with item_id as form field and file as binary
4. **Type validation:** Frontend should validate value types before submission
5. **Conditional logic:** Frontend should use visibility_trace to determine which items to display and which are required
6. **Hidden items:** Do not require answers for items marked as visible=False in visibility_trace
7. **Attachment limits:** Enforce 25MB size limit and allowed content types on frontend for better UX
