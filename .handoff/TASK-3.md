# TASK-3 Handoff: Backend Feature B1 - Template Management and Conditional Items

## Implemented Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/login
**Request:**
```json
{
  "email": "admin@example.com",
  "password": "admin123",
  "client_metadata": {  // optional
    "device": "web",
    "ip": "127.0.0.1"
  }
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "subject_id": "syn.admin",
    "display_name": "Admin User",
    "email": "admin@example.com",
    "role_codes": ["internal_admin"],
    "is_asp": false,
    "is_active": true,
    "created_at_utc": "2024-11-12T10:00:00Z",
    "updated_at_utc": "2024-11-12T10:00:00Z"
  }
}
```

**Rate Limiting:** 5 attempts per 60 seconds per email address. Returns 429 when exceeded.

**Audit Events:** Creates `login_success`, `login_failed`, or `login_rate_limited` audit log entries with correlation ID.

#### GET /api/v1/auth/me
**Headers:** `Authorization: Bearer {access_token}`

**Response:** Same `user` object as login response.

### Checklist Template Endpoints

#### POST /api/v1/checklist-templates
**Headers:** `Authorization: Bearer {access_token}` (requires `internal_admin` role)

**Request:**
```json
{
  "template_code": "TPL-SYN-002",
  "name": "Equipment Inspection",
  "description": "Standard equipment inspection checklist",
  "items": [
    {
      "item_key": "equipment_type",
      "label": "Equipment Type",
      "item_type": "single_select",
      "display_order": 1,
      "is_required": true,
      "evidence_required": false,
      "location_mode": "none",
      "options": {
        "choices": ["Radio Unit", "Base Station", "Antenna"]
      }
    },
    {
      "item_key": "radio_frequency",
      "label": "Radio Frequency (MHz)",
      "item_type": "number",
      "display_order": 2,
      "is_required": true,
      "evidence_required": false,
      "location_mode": "none",
      "condition": {
        "source_item_key": "equipment_type",
        "operator": "equals",
        "expected_value": "Radio Unit"
      }
    }
  ]
}
```

**Response:**
```json
{
  "id": 2,
  "template_code": "TPL-SYN-002",
  "name": "Equipment Inspection",
  "description": "Standard equipment inspection checklist",
  "current_version_id": 2,
  "status": "active",
  "created_by_user_id": 1,
  "created_at_utc": "2024-11-12T10:30:00Z",
  "updated_at_utc": "2024-11-12T10:30:00Z"
}
```

**Validation:**
- Template code must be unique
- Conditional items must reference source items that appear earlier in display order
- Returns 400 with readable error if validation fails

**Audit Events:** Creates `template_created` audit log entry with correlation ID.

#### GET /api/v1/checklist-templates
**Headers:** `Authorization: Bearer {access_token}` (requires `internal_admin` role)

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 20)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "template_code": "SITE_SURVEY_V1",
      "name": "Site Survey Checklist",
      "description": "Standard site survey checklist for network deployment",
      "current_version_id": 1,
      "status": "active",
      "created_by_user_id": 1,
      "created_at_utc": "2024-11-12T09:00:00Z",
      "updated_at_utc": "2024-11-12T09:00:00Z"
    }
  ],
  "total": 1
}
```

#### POST /api/v1/checklist-templates/{id}/versions
**Headers:** `Authorization: Bearer {access_token}` (requires `internal_admin` role)

**Request:**
```json
{
  "version_label": "v2.0",
  "items": [
    // Same structure as create template items
  ]
}
```

**Response:**
```json
{
  "id": 3,
  "template_id": 1,
  "version_number": 2,
  "version_label": "v2.0",
  "status": "published",
  "published_at_utc": "2024-11-12T11:00:00Z",
  "published_by_user_id": 1,
  "items": [
    {
      "id": 5,
      "item_key": "equipment_type",
      "label": "Equipment Type",
      "item_type": "single_select",
      "display_order": 1,
      "is_required": true,
      "evidence_required": false,
      "location_mode": "none",
      "options": {
        "choices": ["Radio Unit", "Base Station", "Antenna"]
      },
      "condition": null
    }
  ],
  "created_at_utc": "2024-11-12T11:00:00Z"
}
```

**Behavior:**
- Creates new immutable version without overwriting historical versions
- Updates template's current_version_id to point to new version
- Validates conditional items same as create

**Audit Events:** Creates `template_version_published` audit log entry with correlation ID.

#### POST /api/v1/checklist-templates/{id}/retire
**Headers:** `Authorization: Bearer {access_token}` (requires `internal_admin` role)

**Response:** Same as template response with `status: "retired"`

**Behavior:**
- Marks template as unavailable for new checklist instances
- Historical checklist instances remain linked to their template version
- Template and all versions remain visible for history

**Audit Events:** Creates `template_retired` audit log entry with correlation ID.

## Seed Users and Credentials

Four users are created with roles:

1. **Admin User**
   - Email: `admin@example.com`
   - Password: `admin123` (or `$SEED_PASSWORD_ADMIN` env var)
   - Role: `internal_admin`
   - Subject ID: `syn.admin`

2. **Engineer User**
   - Email: `engineer@example.com`
   - Password: `engineer123` (or `$SEED_PASSWORD_ENGINEER` env var)
   - Role: `field_engineer`
   - Subject ID: `syn.engineer`

3. **Reviewer User**
   - Email: `reviewer@example.com`
   - Password: `reviewer123` (or `$SEED_PASSWORD_REVIEWER` env var)
   - Role: `reviewer`
   - Subject ID: `syn.reviewer`

4. **ASP User**
   - Email: `asp@example.com`
   - Password: `asp123` (or `$SEED_PASSWORD_ASP` env var)
   - Role: `asp_user`
   - Subject ID: `syn.asp`

## Seed Template

**Template Code:** `SITE_SURVEY_V1`  
**Name:** Site Survey Checklist  
**Description:** Standard site survey checklist for network deployment  
**Version:** v1.0 (published)

**Items:**
1. **equipment_type** (single_select, display_order: 1, required)
   - Choices: ["Radio Unit", "Base Station", "Antenna"]
   
2. **radio_frequency** (number, display_order: 2, required, conditional)
   - Condition: shown when equipment_type = "Radio Unit"
   - Operator: equals
   - Expected value: "Radio Unit"

## Backend Flow

1. **Template Creation:**
   - User with `internal_admin` role creates template with items
   - Service validates template_code uniqueness
   - Service validates conditional item ordering (source must precede dependent)
   - Creates template record with status "active"
   - Creates initial version v1.0 with status "published"
   - Creates items and conditions in database
   - Updates template.current_version_id
   - Records audit event with correlation ID

2. **Version Publishing:**
   - User with `internal_admin` role publishes new version
   - Service increments version_number
   - Creates new immutable version record
   - Creates new item and condition records linked to new version
   - Updates template.current_version_id
   - Historical versions remain unchanged
   - Records audit event with correlation ID

3. **Template Retirement:**
   - User with `internal_admin` role retires template
   - Updates template.status to "retired"
   - Template no longer available for new checklist instances
   - Historical instances remain linked to their template version
   - Template and versions remain visible for audit/history
   - Records audit event with correlation ID

## Middleware and Cross-Cutting Concerns

1. **Correlation ID Middleware:**
   - Generates `corr-<8-hex>` for each request
   - Adds to request.state.correlation_id
   - Adds X-Correlation-ID header to response
   - Propagated to audit logs and error responses

2. **Request Logging Middleware:**
   - Logs structured request start and completion
   - Includes correlation ID, method, path, status, duration

3. **Exception Handler Middleware:**
   - Catches unhandled exceptions
   - Returns standardized `{"detail": "...", "correlation_id": "..."}` error response
   - Logs exception with correlation ID

4. **Auth Context:**
   - Resolves current user from Bearer token via `get_current_user` dependency
   - Validates token signature and expiry
   - Returns User model
   - Returns 401 for invalid/expired tokens
   - Returns 403 for inactive users

5. **Permission Service:**
   - Enforces role-based permissions via `require_permission(user, permission_code)`
   - Permission codes: `template_management`, `checklist_creation`, `checklist_submission`, `checklist_review`, `ingestion_upload`, `ingestion_view`, `mapping_management`
   - Returns 403 for unauthorized access

6. **Audit Service:**
   - Records events via `record_event(event_type, actor, entity_ref, correlation_id, payload)`
   - Writes to audit_logs table
   - Event types: `login_success`, `login_failed`, `login_rate_limited`, `template_created`, `template_version_published`, `template_retired`

7. **Identity Provider Adapter:**
   - Demo mode: authenticates against seed users with bcrypt-hashed passwords
   - Implements `authenticate(username, password) -> IdentityClaims`
   - Implements `getUserProfile(subjectId) -> IdentityProfile`
   - Abstraction layer for future enterprise SSO integration

## Error Handling

All errors follow standardized format:
```json
{
  "detail": "Human-readable error message"
}
```

Common status codes:
- 400: Validation error (e.g., duplicate template_code, invalid conditional item order)
- 401: Authentication required or invalid token
- 403: Permission denied
- 404: Resource not found
- 429: Rate limit exceeded
- 500: Internal server error (includes correlation_id)
