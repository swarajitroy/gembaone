# GembaONE Platform Developer Guide

This guide explains how to extend and maintain the GembaONE platform, covering common development tasks and extension points.

## Table of Contents

1. [Adding a New Mapping Version](#adding-a-new-mapping-version)
2. [Activating a Mapping](#activating-a-mapping)
3. [Adding a New Validation Rule Type](#adding-a-new-validation-rule-type)
4. [Regenerating Seed Data](#regenerating-seed-data)
5. [Architecture Overview](#architecture-overview)
6. [Testing Guidelines](#testing-guidelines)

## Adding a New Mapping Version

Mappings define how Excel columns map to target database fields. Mappings are versioned, and only one version is active at a time.

### Step 1: Understand the Current Mapping

Check the current active mapping in the database or seed data:

```bash
cd backend
source .venv/bin/activate
python -c "
from app.database import get_db
from app.repositories.mapping_repository import MappingRepository

db = next(get_db())
repo = MappingRepository(db)
mapping = repo.get_by_code('SITE_DATA_IMPORT_V1')
if mapping:
    active_version = repo.get_active_version(mapping.id)
    print(f'Current version: {active_version.version_label}')
    entries = repo.get_entries_for_version(active_version.id)
    for entry in entries:
        print(f'  {entry.source_column} -> {entry.target_field} ({entry.target_type})')
"
```

### Step 2: Create Mapping Entries

Create a list of mapping entries (source column → target field mappings):

```python
mapping_entries = [
    {
        "source_column": "Site ID",
        "target_field": "site_id",
        "target_type": "string",
        "is_required": True,
        "transform_expression": None
    },
    {
        "source_column": "Site Name",
        "target_field": "site_name",
        "target_type": "string",
        "is_required": True,
        "transform_expression": None
    },
    {
        "source_column": "Latitude",
        "target_field": "latitude",
        "target_type": "number",
        "is_required": True,
        "transform_expression": None
    },
    {
        "source_column": "Longitude",
        "target_field": "longitude",
        "target_type": "number",
        "is_required": True,
        "transform_expression": None
    }
]
```

### Step 3: Publish New Version via API

Use the API to publish a new version:

```bash
# Login as admin
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }' | jq -r '.access_token' > token.txt

# Publish new version
curl -X POST http://localhost:9000/api/v1/mappings/1/versions \
  -H "Authorization: Bearer $(cat token.txt)" \
  -H "Content-Type: application/json" \
  -d '{
    "version_label": "v3.0",
    "entries": [
      {
        "source_column": "Site ID",
        "target_field": "site_id",
        "target_type": "string",
        "is_required": true
      },
      {
        "source_column": "Site Name",
        "target_field": "site_name",
        "target_type": "string",
        "is_required": true
      },
      {
        "source_column": "Latitude",
        "target_field": "latitude",
        "target_type": "number",
        "is_required": true
      },
      {
        "source_column": "Longitude",
        "target_field": "longitude",
        "target_type": "number",
        "is_required": true
      },
      {
        "source_column": "Elevation",
        "target_field": "elevation",
        "target_type": "number",
        "is_required": false
      }
    ]
  }'
```

### Step 4: Verify Version Created

Check that the new version is active:

```bash
curl -X GET http://localhost:9000/api/v1/mappings \
  -H "Authorization: Bearer $(cat token.txt)" | jq '.items[0].active_version'
```

### Notes on Mapping Versions

- **Version Superseding**: When you publish a new version, the previous active version automatically becomes `superseded`
- **Version Labels**: Use semantic versioning (e.g., `v1.0`, `v2.0`, `v2.1`)
- **Version History**: All versions are preserved for audit trail
- **Ingestion Records**: Link to specific `mapping_version_id`, not the definition

## Activating a Mapping

Mappings are activated automatically when you publish their first version. To switch between versions of an existing mapping:

### Option 1: Publish New Version (Recommended)

Publishing a new version automatically makes it active:

```bash
# See "Adding a New Mapping Version" above
curl -X POST http://localhost:9000/api/v1/mappings/{mapping_id}/versions \
  -H "Authorization: Bearer $(cat token.txt)" \
  -H "Content-Type: application/json" \
  -d '{
    "version_label": "v3.0",
    "entries": [...]
  }'
```

### Option 2: Programmatic Activation (Advanced)

If you need to reactivate an older version or perform custom activation logic:

```python
from app.database import get_db
from app.repositories.mapping_repository import MappingRepository
from app.models.mapping import MappingVersion

db = next(get_db())
repo = MappingRepository(db)

# Get the mapping and target version
mapping_id = 1
target_version_number = 2  # The version you want to activate

# Mark current active version as superseded
current_active = repo.get_active_version(mapping_id)
if current_active:
    current_active.status = "superseded"

# Mark target version as active
target_version = db.query(MappingVersion).filter(
    MappingVersion.mapping_definition_id == mapping_id,
    MappingVersion.version_number == target_version_number
).first()
target_version.status = "active"

db.commit()
print(f"Activated version {target_version.version_label}")
```

### Important Notes

- Only ONE version per mapping can be `active` at a time
- Ingestion records reference specific `mapping_version_id`, so old ingestions still point to their original mapping version
- Mapping changes do NOT affect historical ingestion records (immutability principle)

## Adding a New Validation Rule Type

Validation rules are organized by layer (mapping, schema, business) and severity (error, warning).

### Step 1: Understand Validation Layers

The validation engine runs rules in this order:

1. **Mapping Layer**: Check required fields are mapped
2. **Schema Layer**: Validate data types and formats
3. **Business Layer**: Apply domain-specific rules
4. **Warning Layer**: Non-blocking validation checks

### Step 2: Define Rule Expression

Create a rule expression as JSON. The validation engine evaluates these expressions:

```python
# Example: Check if a field matches a pattern
{
    "field": "site_id",
    "operator": "regex",
    "pattern": "^SITE-[0-9]{4}$"
}

# Example: Check numeric range
{
    "field": "latitude",
    "operator": "range",
    "min": -90,
    "max": 90
}

# Example: Check required field presence
{
    "field": "site_name",
    "operator": "required"
}

# Example: Check value in allowed list
{
    "field": "status",
    "operator": "in",
    "values": ["active", "inactive", "pending"]
}
```

### Step 3: Add Rule to Validation Rule Set

#### Via Seed Data (`backend/app/seed.py`)

Add to the seed data:

```python
# In seed_data() function, after creating validation_rule_set:

rule_data = [
    {
        "rule_code": "ELEVATION_RANGE",
        "layer_code": "business",
        "severity": "warning",
        "expression_json": json.dumps({
            "field": "elevation",
            "operator": "range",
            "min": -500,
            "max": 9000
        }),
        "human_message": "Elevation should be between -500m and 9000m",
        "sort_order": 4
    }
]

for rule_info in rule_data:
    rule = db.query(ValidationRule).filter(
        ValidationRule.rule_set_id == validation_rule_set.id,
        ValidationRule.rule_code == rule_info["rule_code"]
    ).first()
    if not rule:
        rule = ValidationRule(
            rule_set_id=validation_rule_set.id,
            **rule_info
        )
        db.add(rule)
        print(f"    Created validation rule: {rule_info['rule_code']}")

db.commit()
```

#### Via Database Script

```python
from app.database import get_db
from app.repositories.validation_repository import ValidationRepository
from app.models.validation import ValidationRule

db = next(get_db())
repo = ValidationRepository(db)

# Get the rule set
rule_set = db.query(ValidationRuleSet).filter(
    ValidationRuleSet.rule_set_code == "SITE_DATA_RULES_V1"
).first()

# Add new rule
new_rule = ValidationRule(
    rule_set_id=rule_set.id,
    rule_code="ELEVATION_RANGE",
    layer_code="business",
    severity="warning",
    expression_json=json.dumps({
        "field": "elevation",
        "operator": "range",
        "min": -500,
        "max": 9000
    }),
    human_message="Elevation should be between -500m and 9000m",
    sort_order=4
)
db.add(new_rule)
db.commit()

print(f"Added rule: {new_rule.rule_code}")
```

### Step 4: Update Validation Engine (if needed)

If you're adding a NEW operator type, update the validation engine:

**File**: `backend/app/services/validation_engine_service.py`

```python
def _evaluate_rule(self, rule: ValidationRule, row_data: dict) -> bool:
    """Evaluate a validation rule against row data."""
    expression = json.loads(rule.expression_json)
    field = expression.get("field")
    operator = expression.get("operator")
    value = row_data.get(field)

    # Add your new operator here
    if operator == "range":
        min_val = expression.get("min")
        max_val = expression.get("max")
        if value is None:
            return False
        try:
            num_val = float(value)
            return min_val <= num_val <= max_val
        except (ValueError, TypeError):
            return False
    
    # ... existing operators ...
    
    return True
```

### Step 5: Test the New Rule

Write a test for the new validation rule:

```python
# backend/tests/test_validation_new_rule.py

def test_elevation_range_validation(db_session, admin_user):
    """Test elevation range validation rule."""
    # Create ingestion with out-of-range elevation
    ingestion = create_test_ingestion(db_session, admin_user)
    
    row_data = {
        "site_id": "SITE-0001",
        "site_name": "Test Site",
        "latitude": 59.3293,
        "longitude": 18.0686,
        "elevation": 10000  # Out of range
    }
    
    # Run validation
    validation_service = ValidationEngineService(db_session)
    result = validation_service.validate_row(ingestion.id, 1, row_data)
    
    # Should have warning (not error)
    assert result.outcome == "accepted_with_warning"
    issues = result.validation_issues
    warning_issues = [i for i in issues if i.severity == "warning"]
    assert len(warning_issues) == 1
    assert "elevation" in warning_issues[0].message.lower()
```

### Validation Rule Checklist

- [ ] Rule expression is valid JSON
- [ ] Layer code is one of: `mapping`, `schema`, `business`, `warning`
- [ ] Severity is one of: `error`, `warning`
- [ ] Rule code is unique within the rule set
- [ ] Human message is clear and actionable
- [ ] Sort order is sequential
- [ ] Rule is tested with passing and failing data

## Regenerating Seed Data

Seed data provides initial demo data for development and testing.

### Option 1: Re-run Seed Script (Idempotent)

The seed script is idempotent, so you can run it multiple times:

```bash
cd backend
source .venv/bin/activate
python app/seed.py
```

This will:
- Skip existing records (by checking unique constraints)
- Add new records if they don't exist
- Update references if needed

### Option 2: Reset Database and Re-seed

For a completely fresh database:

```bash
cd backend
source .venv/bin/activate

# Delete the database file
rm -f app.db

# Run migrations
alembic upgrade head

# Run seed data
python app/seed.py
```

### Option 3: Modify Seed Data

Edit `backend/app/seed.py` to change seed data:

**Example: Add a new user**

```python
# In seed_data() function, add to user_data list:
user_data = [
    # ... existing users ...
    {
        "subject_id": "syn.manager",
        "display_name": "Manager User",
        "email": "manager@example.com",
        "password": "manager123",
        "role_code": "internal_admin",
    },
]
```

**Example: Add a new checklist template**

```python
# In seed_data() function, after existing template creation:
template2 = db.query(ChecklistTemplate).filter(
    ChecklistTemplate.template_code == "EQUIPMENT_CHECKLIST_V1"
).first()
if not template2 and admin_user:
    template2 = ChecklistTemplate(
        template_code="EQUIPMENT_CHECKLIST_V1",
        name="Equipment Installation Checklist",
        description="Checklist for equipment installation verification",
        status="active",
        created_by_user_id=admin_user.id,
    )
    db.add(template2)
    db.flush()
    print("  Created template: EQUIPMENT_CHECKLIST_V1")
    
    # Add version and items...
```

### Seed Data Guidelines

- **Idempotency**: Always check if records exist before creating
- **Passwords**: Use `hash_password()` for all user passwords
- **Relationships**: Flush after creating parent records before adding children
- **Foreign Keys**: Always use `.id` references, never hardcoded IDs
- **Timestamps**: Use `datetime.now(timezone.utc)` for UTC timestamps
- **Status Values**: Use valid enum values (e.g., `active`, `published`, `completed`)

## Architecture Overview

### Backend Layered Architecture

The backend follows a strict layered architecture:

```
routers → services → repositories → models
```

**Dependency Rules**:
- Routers call services (no direct database access)
- Services call repositories (no direct ORM queries outside repositories)
- Repositories return ORM models
- Models have no business logic

### Key Design Patterns

1. **Repository Pattern**: All database access through repositories
2. **Service Layer**: Business logic and orchestration in services
3. **Adapter Pattern**: External systems (identity, storage) abstracted via adapters
4. **Middleware**: Cross-cutting concerns (auth, logging, correlation IDs)

### Immutability Principles

- **Template Versions**: Published versions cannot be modified
- **Mapping Versions**: Active versions cannot be modified
- **Raw Files**: Stored with `immutable_flag=True`
- **Audit Logs**: Append-only, never updated or deleted

### Conditional Visibility Algorithm

Checklist items can be conditionally visible based on other answers:

1. When answers are submitted, evaluate all conditions
2. For each item with conditions:
   - Check if source item value matches condition
   - Mark item as visible or hidden
3. Store visibility state in `visibility_trace_json`
4. Hidden items are NOT required for submission

**Implementation**: `backend/app/services/checklist_execution_service.py`

### Validation Pipeline

The validation engine runs in layers:

```
Mapping Layer    → Are required fields mapped?
    ↓
Schema Layer     → Are values the correct type?
    ↓
Business Layer   → Do values meet business rules?
    ↓
Warning Layer    → Are there non-blocking issues?
```

**Outcome Decision**:
- ANY error → `rejected`
- Warnings only → `accepted_with_warning`
- No issues → `accepted`

**Implementation**: `backend/app/services/validation_engine_service.py`

## Testing Guidelines

### Test Organization

- **Unit Tests**: Test individual services/repositories in isolation
- **Integration Tests**: Test workflows across multiple services
- **Acceptance Tests**: Test complete feature scenarios
- **E2E Tests**: Test user journeys through the UI (Playwright)

### Running Tests

```bash
# Backend unit tests
cd backend
.venv/bin/python -m pytest tests/test_*_service.py -v

# Backend integration tests
.venv/bin/python -m pytest tests/test_*_integration.py -v

# Backend acceptance tests
.venv/bin/python -m pytest tests/test_*_acceptance.py -v

# All backend tests
.venv/bin/python -m pytest tests/ -v

# Frontend unit tests
cd frontend
npm test

# Frontend E2E tests
npx playwright test
```

### Writing Good Tests

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Use Fixtures**: Leverage shared fixtures from `conftest.py`
3. **Test Behavior**: Test what the code does, not how it does it
4. **Meaningful Names**: Test names should describe the scenario
5. **Independent Tests**: Tests should not depend on each other

### Test Coverage Goals

- Services: >90% coverage
- Repositories: >80% coverage
- Routers: >80% coverage
- Overall: >85% coverage

### Example Test

```python
def test_publish_mapping_version_marks_previous_superseded(
    db_session, admin_user
):
    """Publishing a new version should mark the previous version as superseded."""
    # Arrange: Create mapping with v1.0
    mapping = create_test_mapping(db_session, admin_user)
    v1 = get_active_version(db_session, mapping.id)
    assert v1.status == "active"
    
    # Act: Publish v2.0
    service = MappingService(db_session)
    v2 = service.publishMappingVersion(
        mapping.id,
        PublishMappingVersionRequest(
            version_label="v2.0",
            entries=[...]
        ),
        admin_user.id
    )
    
    # Assert: v1 is superseded, v2 is active
    db_session.refresh(v1)
    assert v1.status == "superseded"
    assert v2.status == "active"
```

## Common Development Tasks

### Adding a New API Endpoint

1. Define request/response schemas in `app/schemas/`
2. Add repository method in `app/repositories/`
3. Add service method in `app/services/`
4. Add router endpoint in `app/routers/`
5. Wire up router in `app/main.py`
6. Write unit, integration, and acceptance tests
7. Update API documentation

### Adding a New Database Table

1. Create ORM model in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and edit migration in `alembic/versions/`
4. Run migration: `alembic upgrade head`
5. Add repository for the new model
6. Add seed data if needed
7. Write tests

### Adding a New Frontend Page

1. Create page component in `src/pages/`
2. Add route in `src/main.tsx`
3. Add navigation link in `src/components/layout/Sidebar.tsx`
4. Define TypeScript types in `src/types/`
5. Add API client methods in `src/lib/api-client.ts`
6. Write unit tests and E2E tests
7. Check Carbon Design System compliance

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org
- **React Docs**: https://react.dev
- **Carbon Design System**: https://carbondesignsystem.com
- **Playwright Docs**: https://playwright.dev

## Getting Help

For questions or issues:
1. Check this guide first
2. Review the API documentation at `/docs`
3. Check existing tests for examples
4. Contact the development team

## Appendix: Useful Scripts

### Check Database Schema

```bash
cd backend
source .venv/bin/activate
python -c "
from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
for table_name in inspector.get_table_names():
    print(f'\\nTable: {table_name}')
    for column in inspector.get_columns(table_name):
        print(f'  {column[\"name\"]}: {column[\"type\"]}')
"
```

### List All API Routes

```bash
cd backend
source .venv/bin/activate
python -c "
from app.main import app

for route in app.routes:
    if hasattr(route, 'methods'):
        print(f'{list(route.methods)[0]:6} {route.path}')
"
```

### Count Records in Database

```bash
cd backend
source .venv/bin/activate
python -c "
from app.database import get_db
from app.models.auth import User, Role
from app.models.checklist import ChecklistTemplate, ChecklistInstance
from app.models.mapping import MappingDefinition
from app.models.ingestion import IngestionRecord

db = next(get_db())
print(f'Users: {db.query(User).count()}')
print(f'Roles: {db.query(Role).count()}')
print(f'Templates: {db.query(ChecklistTemplate).count()}')
print(f'Instances: {db.query(ChecklistInstance).count()}')
print(f'Mappings: {db.query(MappingDefinition).count()}')
print(f'Ingestions: {db.query(IngestionRecord).count()}')
"
```
