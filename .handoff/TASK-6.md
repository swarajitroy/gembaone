# TASK-6 Handoff: Checklist Submission and Review

## Overview
Implemented checklist submission and review functionality (FR-008, FR-009) with validation rules per LLD Section 11.3.

## Backend Endpoints Added

### POST /api/v1/checklists/{id}/submit
Submit a checklist instance for review.

**Request:**
- No request body
- Requires authentication

**Response (Success - 200):**
```json
{
  "status": "submitted",
  "submitted_by": 123,
  "submitted_at": "2026-11-12T10:30:00Z",
  "validation_issues": []
}
```

**Response (Validation Failed - 400):**
```json
{
  "detail": {
    "message": "Checklist validation failed. Please address the issues before submitting.",
    "validation_issues": [
      {
        "item_id": 456,
        "code": "required_answer_missing",
        "message": "Required item 'Site Access' must be answered before submission.",
        "severity": "error"
      },
      {
        "item_id": 789,
        "code": "required_evidence_missing",
        "message": "Item 'Site Photo' requires at least one attachment before submission.",
        "severity": "error"
      }
    ]
  }
}
```

**Response (Already Submitted - 409):**
```json
{
  "detail": "Cannot submit checklist in submitted status. Only draft checklists can be submitted."
}
```

### GET /api/v1/checklists/{id}
Retrieve checklist instance with full context (existing endpoint, supports review).

**Response:**
```json
{
  "instance": {
    "id": 1,
    "template_version_id": 1,
    "title": "SYN-CL-0041",
    "status": "submitted",
    "visibility_trace_json": "{...}",
    "created_by_user_id": 1,
    "created_at_utc": "2026-11-12T08:00:00Z",
    "submitted_by_user_id": 1,
    "submitted_at_utc": "2026-11-12T10:30:00Z"
  },
  "items": [...],
  "locations": [...],
  "template_version": {
    "id": 1,
    "template_id": 1,
    "version_number": 1,
    "version_label": "v1.0",
    "status": "published"
  }
}
```

### PUT /api/v1/checklists/{id}/answers
Updated to enforce read-only constraint after submission.

**Response (After Submission - 409):**
```json
{
  "detail": "Cannot modify answers for submitted checklist. Submitted instances are read-only."
}
```

## Submission Validation Rules (LLD Section 11.3)

The submission validation enforces:

1. **Required Visible Items:** All visible items marked as `is_required=true` must have answers
2. **Required Evidence:** All visible items marked as `evidence_required=true` must have at least one attachment
3. **Hidden Items Bypass:** Hidden items (based on conditional visibility) are excluded from validation - they are neither required to have answers nor required to have evidence
4. **Status Transition:** Only `draft` instances can be submitted; `submitted` instances cannot be re-submitted
5. **Read-Only After Submission:** Submitted instances cannot have answers modified (enforced with 409 status)

## Validation Issue Codes

- `required_answer_missing`: A visible required item has no answer
- `required_evidence_missing`: A visible item requiring evidence has no attachments

## Seed Data

### SYN-CL-0042 (Draft)
- Status: `draft`
- Answers: site_access="Obstructed", obstruction_details="Large tree blocking access"
- Attachments: 2 photos for site_photo item
- Location: Instance-level location captured
- Can be used to test submission flow

### SYN-CL-0041 (Submitted)
- Status: `submitted`
- Answers: site_access="Clear" (condition not triggered, obstruction_details hidden)
- Attachments: 2 photos for site_photo item
- Location: Instance-level location captured
- Submitted by: engineer user
- Submitted at: Seeded timestamp
- Can be used to test review flow and read-only enforcement

## Backend Flow Details

### Submission Flow
1. User POSTs to `/api/v1/checklists/{id}/submit`
2. Service validates instance is in `draft` status
3. Service loads all instance items and visibility trace
4. Service loads all answers and attachments
5. For each **visible** item:
   - If `is_required=true` and no answer exists → add validation issue
   - If `evidence_required=true` and no attachments exist → add validation issue
6. If validation issues exist → return 400 with issues list
7. If validation passes:
   - Update instance status to `submitted`
   - Record `submitted_by_user_id` and `submitted_at_utc`
   - Create audit event with correlation ID
   - Return 200 with submission confirmation

### Review Flow
1. Reviewer GETs `/api/v1/checklists/{id}`
2. Service retrieves instance, all items, all locations, and template version metadata
3. Response includes:
   - Instance with `status="submitted"`, submitter ID, and submission timestamp
   - All items (including hidden ones with condition snapshots)
   - All captured locations (instance-level and item-level)
   - Template version metadata (version number, label, status)
4. Frontend can display all answered items, conditional outcomes, attachments, and locations according to permission

### Read-Only Enforcement
1. User attempts PUT `/api/v1/checklists/{id}/answers` on submitted instance
2. Service checks instance status
3. If status is `submitted` → return 409 with readable error message
4. This prevents any answer modifications after submission

## Audit Trail

Every submission creates an audit event:
- Event type: `checklist_submitted`
- Actor: User ID of submitter
- Entity: `checklist_instance`, instance ID
- Correlation ID: Matches response header `X-Correlation-ID`
- Payload: `{"instance_id": 123, "submitted_at": "2026-11-12T10:30:00Z"}`

## Acceptance Criteria Coverage

### FR-008 Acceptance Criteria
✅ Submission validates required visible items and required evidence  
✅ Submitted instances become read-only except through authorized follow-up actions  
✅ Submission records submitter identity and timestamp  
✅ The system returns validation guidance when submission is blocked  

### FR-009 Acceptance Criteria
✅ Reviewers can open a submitted checklist and view all answered items  
✅ Conditional item outcomes are visible in context (via visibility_trace_json)  
✅ Linked attachments and locations are visible according to permission (returned in detail response)  
✅ Template version and submission metadata are displayed (included in template_version field)  

## Testing

All tests pass:
- Unit tests: `tests/test_submission_service.py` (6 tests)
- Integration tests: `tests/test_submission_integration.py` (3 tests)
- Acceptance tests: `tests/test_submission_acceptance.py` (4 tests)

Run with:
```bash
cd /repos/gembaone/backend
.venv/bin/python -m pytest tests/test_submission_service.py tests/test_submission_integration.py tests/test_submission_acceptance.py -v
```

## Next Steps for Frontend

1. **Submission UI:**
   - Add "Submit for Review" button on draft checklist execution screen
   - Before submitting, check all visible required items are answered
   - Show validation issues in modal/notification if submission fails
   - Show success message and redirect to read-only view on success

2. **Review UI:**
   - Display submitted checklist with read-only indicator
   - Show submission metadata: "Submitted by [User] on [Date]"
   - Display all answered items with their values
   - Show visibility trace context for conditional items (visible/hidden state)
   - Display attachments with download links
   - Display captured locations on map
   - Show template version information

3. **Read-Only Mode:**
   - Disable all input fields for submitted checklists
   - Hide "Save" and "Submit" buttons
   - Show "View Only" badge or similar indicator
   - Prevent attachment uploads and location captures

4. **Error Handling:**
   - Display validation issues from 400 response in user-friendly format
   - Show specific item labels in error messages
   - Provide guidance on how to fix each issue
   - Handle 409 conflict gracefully with clear messaging
