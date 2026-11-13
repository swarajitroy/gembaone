# Task 4 Handoff: Checklist Instances and Location

## Implemented Endpoints

### POST /api/v1/checklists
Create a new checklist instance from an active template version.

**Request:**
```json
{
  "template_version_id": 1,
  "title": "My Checklist Instance"
}
```

**Response:** ChecklistInstanceResponse
```json
{
  "id": 1,
  "template_version_id": 1,
  "title": "My Checklist Instance",
  "status": "draft",
  "created_by_user_id": 1,
  "created_at_utc": "2026-11-12T10:00:00Z",
  "submitted_by_user_id": null,
  "submitted_at_utc": null
}
```

**Behavior:**
- Creates instance only from published template versions (FR-003)
- Captures snapshot of template structure in `template_snapshot_json`
- Creates instance items from template items
- Snapshots conditional visibility rules in each item's `condition_snapshot_json`
- Initializes `visibility_trace_json` as null (evaluated later during answer capture)
- Instance starts in `draft` status
- Logs `checklist_instance_created` audit event

---

### GET /api/v1/checklists/{id}
Retrieve full checklist instance detail with items, locations, and template metadata.

**Response:** ChecklistDetailResponse
```json
{
  "instance": {
    "id": 1,
    "template_version_id": 1,
    "title": "SYN-CL-0042",
    "status": "draft",
    "created_by_user_id": 2,
    "created_at_utc": "2026-11-12T10:00:00Z",
    "submitted_by_user_id": null,
    "submitted_at_utc": null
  },
  "items": [
    {
      "id": 1,
      "checklist_instance_id": 1,
      "template_item_id": 1,
      "item_key": "equipment_type",
      "label": "Equipment Type",
      "item_type": "select",
      "display_order": 1,
      "is_required": true,
      "evidence_required": false,
      "location_mode": "none",
      "condition_snapshot_json": null
    }
  ],
  "locations": [
    {
      "id": 1,
      "checklist_instance_id": 1,
      "checklist_instance_item_id": null,
      "latitude": 59.3293,
      "longitude": 18.0686,
      "accuracy_meters": 10.0,
      "captured_by_user_id": 2,
      "captured_at_utc": "2026-11-12T10:05:00Z"
    }
  ],
  "template_version": {
    "id": 1,
    "template_id": 1,
    "version_number": 1,
    "version_label": "v1.0",
    "status": "published"
  }
}
```

**Behavior:**
- Returns full instance context for review
- Includes all instance items (preserving template structure snapshot)
- Includes all captured locations (instance-level and item-level)
- Includes template version metadata for traceability

---

### PUT /api/v1/checklists/{id}/location
Capture instance-level geo-location.

**Request:**
```json
{
  "latitude": 59.3293,
  "longitude": 18.0686,
  "accuracy_meters": 10.0
}
```

**Response:** LocationResponse
```json
{
  "id": 1,
  "checklist_instance_id": 1,
  "checklist_instance_item_id": null,
  "latitude": 59.3293,
  "longitude": 18.0686,
  "accuracy_meters": 10.0,
  "captured_by_user_id": 2,
  "captured_at_utc": "2026-11-12T10:05:00Z"
}
```

**Behavior:**
- Records location for entire checklist instance
- `checklist_instance_item_id` is null for instance-level locations
- Latitude validated: -90 to 90
- Longitude validated: -180 to 180
- Logs `checklist_location_captured` audit event with scope "instance"

---

### PUT /api/v1/checklists/{id}/items/{itemId}/location
Capture item-level geo-location for a specific checklist item.

**Request:**
```json
{
  "latitude": 59.3320,
  "longitude": 18.0700,
  "accuracy_meters": 5.0
}
```

**Response:** LocationResponse
```json
{
  "id": 2,
  "checklist_instance_id": 1,
  "checklist_instance_item_id": 3,
  "latitude": 59.3320,
  "longitude": 18.0700,
  "accuracy_meters": 5.0,
  "captured_by_user_id": 2,
  "captured_at_utc": "2026-11-12T10:10:00Z"
}
```

**Behavior:**
- Records location for specific item within checklist instance
- `checklist_instance_item_id` references the instance item
- Validates that item belongs to specified instance
- Latitude validated: -90 to 90
- Longitude validated: -180 to 180
- Logs `checklist_location_captured` audit event with scope "item"

---

## Seed Data

### Sample Checklist Instance: SYN-CL-0042
- Template: TPL-SYN-001 (SITE_SURVEY_V1) v1.0
- Status: `draft`
- Creator: syn.engineer (engineer@example.com / engineer123)
- Instance-level location captured: (59.3293, 18.0686) Stockholm coordinates
- Contains 2 instance items:
  - equipment_type (select field)
  - radio_frequency (number field with conditional visibility)

---

## Backend Flow

### Instance Creation Flow
1. Verify template version exists and is published (FR-003)
2. Retrieve template metadata and items
3. Build template snapshot JSON with structure
4. Create `checklist_instances` record in `draft` status
5. For each template item:
   - Create `checklist_instance_items` record
   - Snapshot item definition
   - Snapshot conditional visibility rule if exists
6. Initialize `visibility_trace_json` as null (evaluated during answer capture)
7. Log audit event
8. Return instance ID

### Location Capture Flow (Instance-Level)
1. Verify instance exists
2. Validate latitude (-90 to 90) and longitude (-180 to 180)
3. Create `checklist_locations` record with `checklist_instance_item_id` = null
4. Record captured_by_user_id and captured_at_utc timestamp
5. Log audit event
6. Return location ID

### Location Capture Flow (Item-Level)
1. Verify instance exists
2. Verify item exists and belongs to instance
3. Validate latitude and longitude
4. Create `checklist_locations` record with `checklist_instance_item_id` set
5. Record captured_by_user_id and captured_at_utc timestamp
6. Log audit event
7. Return location ID

---

## Services

### ChecklistExecutionService
- `create_instance()` - Create instance from published template version, snapshot structure
- `capture_instance_location()` - Capture instance-level location
- `capture_item_location()` - Capture item-level location

### ChecklistReviewService
- `get_checklist_detail()` - Retrieve instance with items, locations, and template metadata

---

## Acceptance Criteria Coverage

### FR-003: Create checklist instances from approved templates
- ✅ Instance can be created only from published template version
- ✅ Created instance records template version, creator, creation time
- ✅ Instance preserves snapshot of template structure
- ✅ Instance creation visible in audit history

### FR-006: Capture geo-location
- ✅ Template configuration marks items as location-aware (via `location_mode` field)
- ✅ Location data can be stored with checklist (instance-level and item-level)
- ✅ Location capture is optional or required per template rules
- ✅ Location data included in retrieval views

---

## Notes for Frontend Task

- Instance creation requires `template_version_id` - use published versions only
- Location capture validates coordinates server-side (Pydantic Field validators)
- `ChecklistDetailResponse` provides complete context for rendering checklist review UI
- Instance starts in `draft` status - submission flow implemented in later task
- Conditional item visibility evaluation happens during answer capture (not yet implemented)
- `visibility_trace_json` initialized null, will track conditional visibility decisions later
