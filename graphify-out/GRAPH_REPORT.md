# Graph Report - gembaone  (2026-11-12)

## Corpus Check
- 197 files · ~76,256 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 123 file(s) not represented in the graph (top: .csv 97, .scss 11, (none) 5)
- WARNING: 123 of 473 files seen (26%) have no supported extractor and are missing from this graph entirely. It may look complete while representing only part of the codebase.

## Summary
- 1948 nodes · 4407 edges · 124 communities (82 shown, 42 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 331 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a6f08332`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- GembaONE Platform Developer Guide
- backend
- test_pipeline_migration_parity.py
- package.json
- TASK-10 Handoff: Raw File Retention and Report Download
- IdentityProviderAdapter
- App.tsx
- backend
- gembaone-backend
- compilerOptions
- GembaONE Platform Frontend
- scripts
- index.ts
- ChecklistReviewService
- routers/checklist_templates.py
- AuthService
- Completed Items
- get_current_user
- HomePage.tsx
- io
- ChecklistTemplateService
- routers/ingestions.py
- react-router-dom
- test_cross_module_integration.py
- Task 8 Handoff: Mapping Management and Validation Structure
- test_template_acceptance.py
- TASK-7 Handoff: Backend Feature B5 - Ingestion Upload and Lifecycle
- seed_data
- correlation_id.py
- ChecklistExecutionService
- test_auth_acceptance.py
- TASK-6 Handoff: Checklist Submission and Review
- TASK-9 Handoff: Backend Feature B7 - Layered Validation and Row Results
- Task 5 Handoff: Backend Feature B3 - Structured Answers and Evidence Capture
- IngestionRepository
- ChecklistExecutionPage.tsx
- MappingVersion
- ChecklistTemplateRepository
- main.py
- Role
- Layout.tsx
- create_mapping
- Task 4 Handoff: Checklist Instances and Location
- MappingEditorPage.tsx
- TemplateBuilderPage.tsx
- MappingService
- .publish_mapping_version
- react-router-dom
- routers/mappings.py
- test_answer_acceptance.py
- MappingRepository
- ExceptionHandlerMiddleware
- test_mapping_acceptance.py
- datetime
- RequestLoggingMiddleware
- @playwright/test
- auth.ts
- config.py
- FastAPI
- devDependencies
- EvidenceRepository
- ChecklistReviewPage.tsx
- login
- eslint.config.js
- typing
- with
- MockUploadFile
- json
- ChecklistTemplate
- @vitejs/plugin-react
- evidence_service.py
- FileObject
- Ericsson GembaONE Platform
- @testing-library/jest-dom
- steps
- audit_test_62262a92.md
- deterministic_87930e49.md
- deterministic_ac2a3fab.md
- deterministic_f00721a7.md
- deterministic_test_10cd907c.md
- deterministic_test_42874c9d.md
- test_integration_2bcc32cd.md
- test_integration_88103f77.md
- test_integration_eea10b44.md
- test_sites_942f49d3.md
- test_sites_aabd09d5.md
- Adding a New Validation Rule Type
- jobs
- db_session
- steps
- .resolve_active_mapping
- Adding a New Mapping Version
- Architecture Overview
- Testing Guidelines
- start.sh
- Regenerating Seed Data
- lint-summary
- on
- Troubleshooting
- Quick Start
- Activating a Mapping
- Common Development Tasks
- Development
- Tech Stack
- Key Features
- checklist_template_service.py
- ValidationRepository
- stop.sh

## God Nodes (most connected - your core abstractions)
1. `User` - 102 edges
2. `FileObject` - 73 edges
3. `ChecklistTemplateVersion` - 69 edges
4. `IngestionRecord` - 62 edges
5. `ChecklistTemplate` - 58 edges
6. `MappingVersion` - 47 edges
7. `Role` - 45 edges
8. `UserRole` - 45 edges
9. `ChecklistExecutionService` - 44 edges
10. `MappingDefinition` - 42 edges

## Surprising Connections (you probably didn't know these)
- `Notes for Frontend Task` --references--> `ChecklistDetailResponse`  [INFERRED]
  .handoff/TASK-4.md → backend/app/schemas/checklists.py
- `Middleware and Cross-Cutting Concerns` --references--> `get_current_user()`  [INFERRED]
  .handoff/TASK-3.md → backend/app/middleware/auth_context.py
- `Authentication` --references--> `get_current_user()`  [INFERRED]
  .handoff/TASK-8.md → backend/app/middleware/auth_context.py
- `Seed Data Guidelines` --references--> `hash_password()`  [INFERRED]
  DEVELOPER_GUIDE.md → backend/app/seed.py
- `login()` --uses--> `PermissionService`  [INFERRED]
  backend/app/routers/auth.py → backend/app/services/permission_service.py

## Import Cycles
- None detected.

## Communities (124 total, 42 thin omitted)

### Community 0 - "GembaONE Platform Developer Guide"
Cohesion: 0.20
Nodes (8): Appendix: Useful Scripts, Check Database Schema, Count Records in Database, GembaONE Platform Developer Guide, Getting Help, List All API Routes, Resources, Table of Contents

### Community 1 - "backend"
Cohesion: 0.08
Nodes (27): PIP_TARGET, build, depends_on, environment, healthcheck, ports, x-preview-port, args (+19 more)

### Community 2 - "test_pipeline_migration_parity.py"
Cohesion: 0.09
Nodes (21): get_url(), run_migrations_offline(), run_migrations_online(), _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key() (+13 more)

### Community 3 - "package.json"
Cohesion: 0.12
Nodes (16): @carbon/styles@^1.72.0, autoprefixer@^10.4.20, postcss@^8.4.49, @testing-library/user-event@^14.6.10, typescript@~5.6.2, engines, node, name (+8 more)

### Community 4 - "TASK-10 Handoff: Raw File Retention and Report Download"
Cohesion: 0.09
Nodes (21): Acceptance Criteria Coverage, Backend Flow, Database Schema, Endpoints Added, Error Handling, FR-019 (Raw File Retention), FR-020 (Report Download), Frontend Implementation Guidance (+13 more)

### Community 5 - "IdentityProviderAdapter"
Cohesion: 0.14
Nodes (3): IdentityClaims, IdentityProfile, IdentityProviderAdapter

### Community 6 - "App.tsx"
Cohesion: 0.18
Nodes (13): App(), RequireAuth(), Layout(), ChecklistDetailPage(), ChecklistExecutionPage(), ChecklistListPage(), ChecklistReviewPage(), ChecklistsPage() (+5 more)

### Community 8 - "backend"
Cohesion: 0.09
Nodes (24): BACKEND_HOST, build, environment, healthcheck, ports, volumes, x-preview-port, args (+16 more)

### Community 11 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, forceConsistentCasingInFileNames, isolatedModules, jsx, lib, module, moduleDetection (+10 more)

### Community 12 - "GembaONE Platform Frontend"
Cohesion: 0.17
Nodes (11): Build, Design System, Development Setup, Environment Variables, GembaONE Platform Frontend, Linting and Type Checking, Prerequisites, Project Structure (+3 more)

### Community 13 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, type-check

### Community 14 - "index.ts"
Cohesion: 0.33
Nodes (5): ChecklistInstance, ChecklistTemplate, IngestionRecord, MappingDefinition, User

### Community 20 - "ChecklistReviewService"
Cohesion: 0.07
Nodes (23): capture_instance_location(), capture_item_location(), create_checklist(), get_checklist_detail(), submit_checklist(), upload_attachment(), upsert_answers(), AnswerRequest (+15 more)

### Community 21 - "routers/checklist_templates.py"
Cohesion: 0.09
Nodes (15): create_template(), list_templates(), publish_version(), retire_template(), ChecklistItemResponse, Config, CreateTemplateRequest, ItemConditionResponse (+7 more)

### Community 22 - "AuthService"
Cohesion: 0.06
Nodes (12): UserSession, AuthRepository, AuthService, test_create_access_token(), test_decode_invalid_token(), test_decode_token(), test_get_user_from_invalid_token(), test_get_user_from_token() (+4 more)

### Community 23 - "Completed Items"
Cohesion: 0.11
Nodes (17): 1. IngestionUploadPage (/ingestions/upload), 2. IngestionResultsPage (/ingestions/:id), 3. IngestionListPage (placeholder), 4. Carbon Design System Compliance, 5. Unit Tests, 6. E2E Tests, 7. Verification, Backend Contract Integration (+9 more)

### Community 24 - "get_current_user"
Cohesion: 0.12
Nodes (15): Authentication Endpoints, Backend Flow, Checklist Template Endpoints, Error Handling, GET /api/v1/auth/me, GET /api/v1/checklist-templates, Implemented Endpoints, Middleware and Cross-Cutting Concerns (+7 more)

### Community 25 - "HomePage.tsx"
Cohesion: 0.24
Nodes (11): @carbon/icons-react@^11.65.0, ChecklistsTable(), ChecklistsTableProps, IngestionsTable(), IngestionsTableProps, HomePage(), ChecklistInstance, ChecklistListItem (+3 more)

### Community 26 - "io"
Cohesion: 0.11
Nodes (11): EvidenceService, test_fr005_attachment_access_follows_permissions(), test_fr005_attachment_linked_to_instance_and_item(), test_fr005_upload_supported_file_type(), test_fr005_uploader_and_timestamp_recorded(), MockUploadFile, test_sha256_checksum_recorded(), test_upload_attachment_exceeds_size_limit() (+3 more)

### Community 27 - "ChecklistTemplateService"
Cohesion: 0.12
Nodes (13): ChecklistItemRequest, ItemConditionRequest, ChecklistTemplateService, test_create_template_duplicate_code(), test_create_template_success(), test_list_templates(), test_retire_template(), test_validate_conditional_items_success() (+5 more)

### Community 28 - "routers/ingestions.py"
Cohesion: 0.07
Nodes (17): get_ingestion(), get_ingestion_results(), get_raw_file_download(), get_report_download(), get_request(), list_ingestions(), upload_ingestion(), IngestionDetailResponse (+9 more)

### Community 29 - "react-router-dom"
Cohesion: 0.17
Nodes (11): IngestionDetail, IngestionResultsPage(), RowResult, mockChecklists, mockIngestions, mockUser, mockMappingResponse, mockTemplate (+3 more)

### Community 30 - "test_cross_module_integration.py"
Cohesion: 0.25
Nodes (3): test_audit_events_with_correlation_ids(), test_ingestion_full_workflow(), test_validation_outcomes_deterministic()

### Community 31 - "Task 8 Handoff: Mapping Management and Validation Structure"
Cohesion: 0.06
Nodes (31): Acceptance Tests (9 tests), Authentication, Backend Flows, Create Mapping Flow, Create Mapping Form, Database Schema, Error Responses, FR-012 Acceptance Criteria Coverage (+23 more)

### Community 32 - "test_template_acceptance.py"
Cohesion: 0.12
Nodes (7): test_create_template(), test_create_template_invalid_conditional_order(), test_create_template_with_conditional_items(), test_list_templates(), test_publish_version(), test_retire_template(), test_template_unauthenticated()

### Community 33 - "TASK-7 Handoff: Backend Feature B5 - Ingestion Upload and Lifecycle"
Cohesion: 0.06
Nodes (34): Acceptance Criteria Coverage, Acceptance Tests (test_ingestion_acceptance.py), ASP Visibility Restrictions, Backend Flow, Current Limitations, Dependencies and Integration Points, File Immutability, FR-011: Upload Excel files for ingestion (+26 more)

### Community 34 - "seed_data"
Cohesion: 0.18
Nodes (4): test_admin_user_creation(), test_database_connection(), test_health_check(), test_seed_data_idempotent()

### Community 36 - "ChecklistExecutionService"
Cohesion: 0.07
Nodes (13): ChecklistRepository, ChecklistExecutionService, test_capture_instance_location(), test_capture_item_location(), test_capture_location_invalid_instance(), test_create_instance_from_draft_version_fails(), test_create_instance_from_published_version(), test_create_instance_nonexistent_version_fails() (+5 more)

### Community 37 - "test_auth_acceptance.py"
Cohesion: 0.17
Nodes (5): test_get_me_authenticated(), test_get_me_unauthenticated(), test_login_invalid_credentials(), test_login_success(), test_login_unknown_user()

### Community 38 - "TASK-6 Handoff: Checklist Submission and Review"
Cohesion: 0.09
Nodes (21): Acceptance Criteria Coverage, Audit Trail, Backend Endpoints Added, Backend Flow Details, FR-008 Acceptance Criteria, FR-009 Acceptance Criteria, GET /api/v1/checklists/{id}, Next Steps for Frontend (+13 more)

### Community 39 - "TASK-9 Handoff: Backend Feature B7 - Layered Validation and Row Results"
Cohesion: 0.06
Nodes (34): Acceptance Criteria Coverage, Acceptance Tests (test_validation_acceptance.py):, Backend Flows, Background Processing Model (LLD Section 13.1):, Database Tables, FR-015: Run layered validation before commit, FR-016: Produce row-level accepted and rejected results with reasons, Frontend Implementation Guidance (+26 more)

### Community 40 - "Task 5 Handoff: Backend Feature B3 - Structured Answers and Evidence Capture"
Cohesion: 0.08
Nodes (23): Acceptance Criteria Coverage, Acceptance Tests:, Answer Upsert:, Answers in SYN-CL-0042:, Attachment Upload:, Attachments in SYN-CL-0042:, Backend Flow, Checklist Instance SYN-CL-0042 (+15 more)

### Community 41 - "IngestionRepository"
Cohesion: 0.06
Nodes (6): IngestionRepository, test_ingestion_events_with_correlation_id(), test_ingestion_lifecycle_transitions(), MockUploadFile, test_create_ingestion_file_too_large(), test_create_ingestion_invalid_extension()

### Community 43 - "ChecklistExecutionPage.tsx"
Cohesion: 0.10
Nodes (15): Answer, ChecklistForm(), ChecklistFormProps, ConditionalItemIndicator(), ConditionalItemIndicatorProps, Location, LocationDisplay(), LocationDisplayProps (+7 more)

### Community 44 - "MappingVersion"
Cohesion: 0.07
Nodes (28): MappingDefinition, MappingEntry, MappingVersion, ValidationRule, ValidationRuleSet, seed_data(), ValidationEngineService, WorkbookValidationService (+20 more)

### Community 46 - "main.py"
Cohesion: 0.20
Nodes (3): health_check(), lifespan(), root()

### Community 47 - "Role"
Cohesion: 0.06
Nodes (26): Role, User, UserRole, ReportRepository, hash_password(), RawFileService, admin_user(), auth_client() (+18 more)

### Community 48 - "Layout.tsx"
Cohesion: 0.17
Nodes (9): RequireAuthProps, Header(), LayoutProps, Sidebar(), LoginPage(), TemplateListPage(), mockLogin, mockNavigate (+1 more)

### Community 52 - "create_mapping"
Cohesion: 0.23
Nodes (3): create_mapping(), list_mappings(), publish_version()

### Community 53 - "Task 4 Handoff: Checklist Instances and Location"
Cohesion: 0.10
Nodes (19): Acceptance Criteria Coverage, Backend Flow, ChecklistExecutionService, ChecklistReviewService, FR-003: Create checklist instances from approved templates, FR-006: Capture geo-location, GET /api/v1/checklists/{id}, Implemented Endpoints (+11 more)

### Community 54 - "MappingEditorPage.tsx"
Cohesion: 0.15
Nodes (13): MappingDetailsForm(), MappingDetailsFormProps, MappingEntriesTable(), MappingEntriesTableProps, TARGET_TYPE_OPTIONS, MappingEditorPage(), renderWithRouter(), MappingDefinition (+5 more)

### Community 55 - "TemplateBuilderPage.tsx"
Cohesion: 0.18
Nodes (11): TemplateBuilderPage(), handlePublish(), loadTemplate(), validateItems(), CreateTemplateItemRequest, ItemCondition, PublishVersionRequest, Template (+3 more)

### Community 57 - "MappingService"
Cohesion: 0.19
Nodes (10): CreateMappingRequest, MappingEntryRequest, MappingService, test_create_mapping_definition_success(), test_create_mapping_duplicate_code_rejected(), test_create_mapping_duplicate_source_columns_rejected(), test_create_mapping_empty_entries_rejected(), test_create_mapping_invalid_target_type_rejected() (+2 more)

### Community 59 - ".publish_mapping_version"
Cohesion: 0.12
Nodes (3): PublishMappingVersionRequest, test_publish_mapping_version_marks_previous_superseded(), test_publish_mapping_version_success()

### Community 60 - "react-router-dom"
Cohesion: 0.15
Nodes (9): dependencies, @carbon/react@^1.72.0, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.1, IngestionUploadPage(), MappingVersion, react (+1 more)

### Community 62 - "routers/mappings.py"
Cohesion: 0.15
Nodes (7): MappingDefinitionResponse, Config, MappingEntryResponse, Config, MappingListResponse, MappingVersionResponse, Config

### Community 64 - "test_answer_acceptance.py"
Cohesion: 0.20
Nodes (4): test_fr004_answers_retrievable(), test_fr004_answers_stored_with_types(), test_fr004_malformed_values_rejected(), test_fr004_responses_preserved_independently()

### Community 67 - "test_mapping_acceptance.py"
Cohesion: 0.11
Nodes (8): test_create_mapping_endpoint(), test_fr_012_structural_validation(), test_fr_013_configure_mappings(), test_list_mappings_endpoint(), test_mapping_duplicate_source_columns_rejected(), test_mapping_publish_validation_missing_required_field_rejected(), test_publish_mapping_version_endpoint(), test_publish_version_marks_previous_superseded()

### Community 68 - "datetime"
Cohesion: 0.10
Nodes (7): Base, ChecklistItemCondition, GeneratedReport, IngestionEvent, docker-entrypoint.sh script, client(), _fresh_schema()

### Community 71 - "auth.ts"
Cohesion: 0.50
Nodes (3): LoginRequest, LoginResponse, User

### Community 74 - "FastAPI"
Cohesion: 0.14
Nodes (3): get_db(), get_correlation_id(), get_current_user()

### Community 75 - "devDependencies"
Cohesion: 0.12
Nodes (16): devDependencies, eslint@^9.17.0, jsdom@^25.0.1, @playwright/test@^1.49.1, sass-embedded@^1.108.2, tailwindcss@^3.4.17, @testing-library/react@^16.1.0, @types/react@^18.3.18 (+8 more)

### Community 77 - "ChecklistReviewPage.tsx"
Cohesion: 0.15
Nodes (10): Attachment, EvidenceGallery(), EvidenceGalleryProps, Answer, Attachment, ChecklistDetail, ChecklistInstance, ChecklistItem (+2 more)

### Community 78 - "login"
Cohesion: 0.10
Nodes (7): get_current_user_info(), login(), LoginRequest, LoginResponse, UserResponse, Config, ErrorDetail

### Community 79 - "eslint.config.js"
Cohesion: 0.18
Nodes (10): @eslint/js@^9.17.0, eslint-plugin-react-hooks@^5.1.0, eslint-plugin-react-refresh@^0.4.16, globals@^15.14.0, typescript-eslint@^8.18.2, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh (+2 more)

### Community 81 - "typing"
Cohesion: 0.29
Nodes (3): upgrade(), downgrade(), upgrade()

### Community 83 - "with"
Cohesion: 0.13
Nodes (15): with, cache, cache-dependency-path, cache-from, cache-to, context, file, flags (+7 more)

### Community 85 - "json"
Cohesion: 0.07
Nodes (15): ChecklistTemplateVersion, AnswerRepository, test_answer_upsert_updates_existing(), test_visibility_hidden_item_bypass(), test_visibility_no_condition(), test_visibility_numeric_threshold(), test_visibility_satisfied_equality(), test_visibility_unsatisfied_equality() (+7 more)

### Community 86 - "ChecklistTemplate"
Cohesion: 0.12
Nodes (18): ChecklistAnswer, ChecklistInstance, ChecklistInstanceItem, ChecklistLocation, ChecklistTemplate, ChecklistTemplateItem, test_get_checklist_detail(), test_fr008_submission_records_identity_and_timestamp() (+10 more)

### Community 87 - "@vitejs/plugin-react"
Cohesion: 0.33
Nodes (4): vite@^6.0.7, @vitejs/plugin-react@^4.3.4, vite, @vitejs/plugin-react

### Community 90 - "evidence_service.py"
Cohesion: 0.08
Nodes (4): DownloadLink, ObjectMetadata, ObjectRef, ObjectStorageAdapter

### Community 91 - "FileObject"
Cohesion: 0.09
Nodes (22): IngestionRecord, IngestionRowResult, ValidationIssue, FileObject, ReportService, test_fr019_authorized_metadata_access(), test_fr019_raw_file_immutable_linkage(), test_fr019_stable_reference() (+14 more)

### Community 92 - "Ericsson GembaONE Platform"
Cohesion: 0.14
Nodes (14): API Documentation, Backend Tests, Contributing, Deployment, Docker Production Build, Ericsson GembaONE Platform, Frontend Tests, License (+6 more)

### Community 99 - "steps"
Cohesion: 0.26
Nodes (12): name, runs-on, steps, steps, steps, docker, steps, if (+4 more)

### Community 111 - "Adding a New Validation Rule Type"
Cohesion: 0.22
Nodes (9): Adding a New Validation Rule Type, Step 1: Understand Validation Layers, Step 2: Define Rule Expression, Step 3: Add Rule to Validation Rule Set, Step 4: Update Validation Engine (if needed), Step 5: Test the New Rule, Validation Rule Checklist, Via Database Script (+1 more)

### Community 112 - "jobs"
Cohesion: 0.22
Nodes (8): name, runs-on, name, runs-on, jobs, e2e, frontend, name

### Community 114 - "steps"
Cohesion: 0.25
Nodes (8): name, runs-on, steps, DATABASE_URL, RATE_LIMIT_ENABLED, SECRET_KEY, backend, env

### Community 117 - "Adding a New Mapping Version"
Cohesion: 0.33
Nodes (6): Adding a New Mapping Version, Notes on Mapping Versions, Step 1: Understand the Current Mapping, Step 2: Create Mapping Entries, Step 3: Publish New Version via API, Step 4: Verify Version Created

### Community 118 - "Architecture Overview"
Cohesion: 0.33
Nodes (6): Architecture Overview, Backend Layered Architecture, Conditional Visibility Algorithm, Immutability Principles, Key Design Patterns, Validation Pipeline

### Community 119 - "Testing Guidelines"
Cohesion: 0.33
Nodes (6): Example Test, Running Tests, Test Coverage Goals, Test Organization, Testing Guidelines, Writing Good Tests

### Community 120 - "start.sh"
Cohesion: 0.53
Nodes (4): check_prerequisites(), find_available_port(), port_in_use(), start.sh script

### Community 121 - "Regenerating Seed Data"
Cohesion: 0.40
Nodes (5): Option 1: Re-run Seed Script (Idempotent), Option 2: Reset Database and Re-seed, Option 3: Modify Seed Data, Regenerating Seed Data, Seed Data Guidelines

### Community 122 - "lint-summary"
Cohesion: 0.40
Nodes (5): lint-summary, if, name, needs, runs-on

### Community 123 - "on"
Cohesion: 0.40
Nodes (5): on, pull_request, push, branches, branches

### Community 124 - "Troubleshooting"
Cohesion: 0.40
Nodes (5): Backend won't start, Docker build fails, Frontend won't start, Tests failing, Troubleshooting

### Community 125 - "Quick Start"
Cohesion: 0.40
Nodes (5): Docker Compose (PostgreSQL), Docker Compose (SQLite), Local Development (Recommended), Prerequisites, Quick Start

### Community 126 - "Activating a Mapping"
Cohesion: 0.50
Nodes (4): Activating a Mapping, Important Notes, Option 1: Publish New Version (Recommended), Option 2: Programmatic Activation (Advanced)

### Community 127 - "Common Development Tasks"
Cohesion: 0.50
Nodes (4): Adding a New API Endpoint, Adding a New Database Table, Adding a New Frontend Page, Common Development Tasks

### Community 128 - "Development"
Cohesion: 0.50
Nodes (4): Adding New Endpoints, Database Migrations, Development, Environment Variables

### Community 129 - "Tech Stack"
Cohesion: 0.50
Nodes (4): Backend, Frontend, Storage, Tech Stack

### Community 130 - "Key Features"
Cohesion: 0.50
Nodes (4): Checklist Management, Excel Ingestion, Key Features, Security & Compliance

### Community 132 - "checklist_template_service.py"
Cohesion: 0.15
Nodes (3): AuditLog, AuditRepository, AuditService

## Knowledge Gaps
- **1 isolated node(s):** `gembaone-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1021 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **42 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Role` to `seed_data`, `datetime`, `IdentityProviderAdapter`, `checklist_template_service.py`, `ChecklistExecutionService`, `IngestionRepository`, `FastAPI`, `FileObject`, `MappingVersion`, `ChecklistTemplateRepository`, `ChecklistReviewService`, `json`, `AuthService`, `ChecklistTemplate`, `MappingService`, `evidence_service.py`, `ChecklistTemplateService`, `routers/ingestions.py`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `User` (e.g. with `IdentityProviderAdapter` and `get_current_user()`) actually correct?**
  _`User` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `gembaone-backend` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `backend` be split into smaller, more focused modules?**
  _Cohesion score 0.082010582010582 - nodes in this community are weakly interconnected._
- **Why does `get_current_user()` connect `FastAPI` to `Role`, `ChecklistReviewService`, `AuthService`, `get_current_user`, `routers/ingestions.py`, `Task 8 Handoff: Mapping Management and Validation Structure`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ChecklistTemplateVersion` (e.g. with `ChecklistTemplateRepository` and `ChecklistTemplateService`) actually correct?**
  _`ChecklistTemplateVersion` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_pipeline_migration_parity.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08771929824561403 - nodes in this community are weakly interconnected._