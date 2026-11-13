"""Seed data for development and demo."""
import json
from datetime import datetime, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.models.auth import Role, User, UserRole
from app.models.checklist import (
    ChecklistAnswer,
    ChecklistAttachment,
    ChecklistInstance,
    ChecklistInstanceItem,
    ChecklistItemCondition,
    ChecklistLocation,
    ChecklistTemplate,
    ChecklistTemplateItem,
    ChecklistTemplateVersion,
)
from app.models.mapping import MappingDefinition, MappingEntry, MappingVersion
from app.models.storage import FileObject
from app.models.validation import ValidationRule, ValidationRuleSet


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_data(db: Session) -> None:
    """Seed initial data idempotently."""
    print("Seeding data...")

    # Seed roles
    role_codes = ["internal_admin", "field_engineer", "reviewer", "asp_user"]
    role_display_names = ["Internal Administrator", "Field Engineer", "Reviewer", "ASP User"]

    roles = []
    for code, display in zip(role_codes, role_display_names):
        role = db.query(Role).filter(Role.role_code == code).first()
        if not role:
            role = Role(role_code=code, display_name=display)
            db.add(role)
            print(f"  Created role: {code}")
        roles.append(role)
    db.commit()

    # Seed users (one per role)
    user_data = [
        {
            "subject_id": "syn.admin",
            "display_name": "Admin User",
            "email": "admin@example.com",
            "password": "admin123",
            "role_code": "internal_admin",
        },
        {
            "subject_id": "syn.engineer",
            "display_name": "Engineer User",
            "email": "engineer@example.com",
            "password": "engineer123",
            "role_code": "field_engineer",
        },
        {
            "subject_id": "syn.reviewer",
            "display_name": "Reviewer User",
            "email": "reviewer@example.com",
            "password": "reviewer123",
            "role_code": "reviewer",
        },
        {
            "subject_id": "syn.asp",
            "display_name": "ASP User",
            "email": "asp@example.com",
            "password": "asp123",
            "role_code": "asp_user",
        },
    ]

    admin_user = None
    asp_user = None
    for user_info in user_data:
        user = db.query(User).filter(User.email == user_info["email"]).first()
        if not user:
            user = User(
                subject_id=user_info["subject_id"],
                display_name=user_info["display_name"],
                email=user_info["email"],
                hashed_password=hash_password(user_info["password"]),
                is_active=True,
            )
            db.add(user)
            db.flush()
            print(f"  Created user: {user_info['email']}")

            # Assign role
            role = db.query(Role).filter(Role.role_code == user_info["role_code"]).first()
            if role:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    assigned_by_user_id=user.id,  # Self-assigned for seed
                )
                db.add(user_role)
                print(f"    Assigned role: {user_info['role_code']}")

        # Set user references (whether created or already existing)
        if user_info["role_code"] == "internal_admin":
            admin_user = user
        elif user_info["role_code"] == "asp_user":
            asp_user = user

    db.commit()

    # Seed sample checklist template
    template = db.query(ChecklistTemplate).filter(ChecklistTemplate.template_code == "SITE_SURVEY_V1").first()
    if not template and admin_user:
        template = ChecklistTemplate(
            template_code="SITE_SURVEY_V1",
            name="Site Survey Checklist",
            description="Standard site survey checklist for network deployment",
            status="active",
            created_by_user_id=admin_user.id,
        )
        db.add(template)
        db.flush()
        print("  Created template: SITE_SURVEY_V1")

        # Create template version
        version = ChecklistTemplateVersion(
            template_id=template.id,
            version_number=1,
            version_label="v1.0",
            status="published",
            published_at_utc=datetime.now(timezone.utc),
            published_by_user_id=admin_user.id,
            schema_snapshot_json=json.dumps({"version": "1.0", "items": []}),
        )
        db.add(version)
        db.flush()
        print("  Created template version: v1.0")

        # Create three items with conditional logic
        item1 = ChecklistTemplateItem(
            template_version_id=version.id,
            item_key="site_access",
            label="Site access condition",
            item_type="select",
            display_order=1,
            is_required=True,
            evidence_required=False,
            location_mode="none",
            options_json=json.dumps({"choices": ["Clear", "Obstructed", "Locked"]}),
        )
        db.add(item1)
        db.flush()
        print("    Created item: site_access")

        item2 = ChecklistTemplateItem(
            template_version_id=version.id,
            item_key="obstruction_details",
            label="Obstruction details",
            item_type="text",
            display_order=2,
            is_required=True,
            evidence_required=False,
            location_mode="none",
        )
        db.add(item2)
        db.flush()
        print("    Created item: obstruction_details")

        # Create condition: show obstruction_details only if site_access = "Obstructed"
        condition = ChecklistItemCondition(
            template_item_id=item2.id,
            source_item_key="site_access",
            operator="equals",
            expected_value="Obstructed",
        )
        db.add(condition)
        print("    Created condition for obstruction_details")

        item3 = ChecklistTemplateItem(
            template_version_id=version.id,
            item_key="site_photo",
            label="Site photo",
            item_type="file",
            display_order=3,
            is_required=False,
            evidence_required=True,
            location_mode="none",
        )
        db.add(item3)
        db.flush()
        print("    Created item: site_photo")

        # Update template with current version
        template.current_version_id = version.id

    db.commit()

    # Seed sample mapping definition MAP-SYN-001 "SYN Site Inventory"
    mapping = (
        db.query(MappingDefinition).filter(MappingDefinition.mapping_code == "MAP-SYN-001").first()
    )
    if not mapping and admin_user:
        mapping = MappingDefinition(
            mapping_code="MAP-SYN-001",
            source_entity="Excel Site Inventory",
            target_entity="SYN Site Inventory",
            status="active",
            created_by_user_id=admin_user.id,
        )
        db.add(mapping)
        db.flush()
        print("  Created mapping: MAP-SYN-001")

        # Create mapping version v1 (superseded)
        mapping_version_v1 = MappingVersion(
            mapping_definition_id=mapping.id,
            version_number=1,
            version_label="v1.0",
            status="superseded",
            published_at_utc=datetime.now(timezone.utc),
            published_by_user_id=admin_user.id,
        )
        db.add(mapping_version_v1)
        db.flush()
        print("  Created mapping version: v1.0 (superseded)")

        # Create mapping version v2 (active)
        mapping_version = MappingVersion(
            mapping_definition_id=mapping.id,
            version_number=2,
            version_label="v2.0",
            status="active",
            published_at_utc=datetime.now(timezone.utc),
            published_by_user_id=admin_user.id,
        )
        db.add(mapping_version)
        db.flush()
        print("  Created mapping version: v2.0 (active)")

        # Create mapping entries for v2 (4 required entries)
        entries = [
            {
                "source_column": "site_id",
                "target_field": "site_id",
                "target_type": "string",
                "is_required": True,
            },
            {
                "source_column": "site_name",
                "target_field": "site_name",
                "target_type": "string",
                "is_required": True,
            },
            {
                "source_column": "latitude",
                "target_field": "latitude",
                "target_type": "number",
                "is_required": True,
            },
            {
                "source_column": "longitude",
                "target_field": "longitude",
                "target_type": "number",
                "is_required": True,
            },
        ]

        for entry_data in entries:
            entry = MappingEntry(
                mapping_version_id=mapping_version.id,
                source_column=entry_data["source_column"],
                target_field=entry_data["target_field"],
                target_type=entry_data["target_type"],
                is_required=entry_data["is_required"],
            )
            db.add(entry)
        print(f"    Created {len(entries)} mapping entries for v2.0")

    db.commit()

    # Seed validation rule set
    rule_set = (
        db.query(ValidationRuleSet).filter(ValidationRuleSet.rule_set_code == "SITE_DATA_RULES_V1").first()
    )
    if not rule_set and admin_user:
        rule_set = ValidationRuleSet(
            rule_set_code="SITE_DATA_RULES_V1",
            version_number=1,
            status="active",
            checksum_sha256="abc123def456",
            created_by_user_id=admin_user.id,
        )
        db.add(rule_set)
        db.flush()
        print("  Created validation rule set: SITE_DATA_RULES_V1")

        # Create validation rules
        rules = [
            {
                "rule_code": "SITE_ID_FORMAT",
                "layer_code": "schema",
                "severity": "error",
                "expression_json": json.dumps({"field": "site_id", "pattern": "^SITE-[0-9]{4}$"}),
                "human_message": "Site ID must match format SITE-NNNN",
                "sort_order": 1,
            },
            {
                "rule_code": "LATITUDE_RANGE",
                "layer_code": "business",
                "severity": "error",
                "expression_json": json.dumps({"field": "latitude", "min": -90, "max": 90}),
                "human_message": "Latitude must be between -90 and 90",
                "sort_order": 2,
            },
            {
                "rule_code": "LONGITUDE_RANGE",
                "layer_code": "business",
                "severity": "error",
                "expression_json": json.dumps({"field": "longitude", "min": -180, "max": 180}),
                "human_message": "Longitude must be between -180 and 180",
                "sort_order": 3,
            },
        ]

        for rule_data in rules:
            rule = ValidationRule(
                rule_set_id=rule_set.id,
                rule_code=rule_data["rule_code"],
                layer_code=rule_data["layer_code"],
                severity=rule_data["severity"],
                expression_json=rule_data["expression_json"],
                human_message=rule_data["human_message"],
                sort_order=rule_data["sort_order"],
            )
            db.add(rule)
        print(f"    Created {len(rules)} validation rules")

    db.commit()

    # Seed sample checklist instance with answers and attachments
    checklist_instance = db.query(ChecklistInstance).filter(ChecklistInstance.id == 1).first()
    if not checklist_instance and admin_user:
        # Find the published template version
        published_version = db.query(ChecklistTemplateVersion).filter(
            ChecklistTemplateVersion.status == "published"
        ).first()

        if published_version:
            # Create checklist instance SYN-CL-0042 (draft)
            template_snapshot = json.dumps({
                "template_code": "SITE_SURVEY_V1",
                "template_name": "Site Survey Checklist",
                "version_number": 1,
                "version_label": "v1.0",
                "items": []
            })

            # Reuse the same template snapshot for both instances
            template_snapshot_for_submitted = template_snapshot

            # Find engineer user
            engineer_user = db.query(User).filter(User.email == "engineer@example.com").first()
            creator_user = engineer_user if engineer_user else admin_user

            checklist_instance = ChecklistInstance(
                template_version_id=published_version.id,
                title="SYN-CL-0042",
                status="draft",
                template_snapshot_json=template_snapshot,
                visibility_trace_json=json.dumps({
                    "site_access": {"visible": True, "required": True, "has_condition": False},
                    "obstruction_details": {"visible": True, "required": True, "has_condition": True},
                    "site_photo": {"visible": True, "required": False, "has_condition": False},
                }),
                created_by_user_id=creator_user.id,
            )
            db.add(checklist_instance)
            db.flush()
            print("  Created checklist instance: SYN-CL-0042")

            # Create instance items from template
            template_items = db.query(ChecklistTemplateItem).filter(
                ChecklistTemplateItem.template_version_id == published_version.id
            ).order_by(ChecklistTemplateItem.display_order).all()

            instance_items = []
            for template_item in template_items:
                # Get condition if exists
                condition_result = db.query(ChecklistItemCondition).filter(
                    ChecklistItemCondition.template_item_id == template_item.id
                ).first()

                condition_snapshot = None
                if condition_result:
                    condition_snapshot = json.dumps({
                        "source_item_key": condition_result.source_item_key,
                        "operator": condition_result.operator,
                        "expected_value": condition_result.expected_value
                    })

                instance_item = ChecklistInstanceItem(
                    checklist_instance_id=checklist_instance.id,
                    template_item_id=template_item.id,
                    item_key=template_item.item_key,
                    label=template_item.label,
                    item_type=template_item.item_type,
                    display_order=template_item.display_order,
                    is_required=template_item.is_required,
                    evidence_required=template_item.evidence_required,
                    location_mode=template_item.location_mode,
                    condition_snapshot_json=condition_snapshot,
                )
                db.add(instance_item)
                instance_items.append(instance_item)

            db.flush()
            print("    Created checklist instance items")

            # Create answers
            # Answer 1: site_access = "Obstructed" (triggers conditional visibility)
            site_access_item = next((item for item in instance_items if item.item_key == "site_access"), None)
            if site_access_item:
                answer1 = ChecklistAnswer(
                    checklist_instance_item_id=site_access_item.id,
                    value_type="text",
                    value_text="Obstructed",
                    answered_by_user_id=creator_user.id,
                    answered_at_utc=datetime.now(timezone.utc),
                )
                db.add(answer1)
                print("    Created answer: site_access = Obstructed")

            # Answer 2: obstruction_details = "Large tree blocking access"
            obstruction_item = next((item for item in instance_items if item.item_key == "obstruction_details"), None)
            if obstruction_item:
                answer2 = ChecklistAnswer(
                    checklist_instance_item_id=obstruction_item.id,
                    value_type="text",
                    value_text="Large tree blocking access",
                    answered_by_user_id=creator_user.id,
                    answered_at_utc=datetime.now(timezone.utc),
                )
                db.add(answer2)
                print("    Created answer: obstruction_details")

            db.flush()

            # Create file objects and attachments for site_photo item
            site_photo_item = next((item for item in instance_items if item.item_key == "site_photo"), None)
            if site_photo_item:
                # Create 2 sample file objects
                for i in range(1, 3):
                    file_obj = FileObject(
                        storage_bucket="checklist-attachments",
                        storage_key=f"seed/photo_{i}.jpg",
                        original_filename=f"site_photo_{i}.jpg",
                        content_type="image/jpeg",
                        byte_size=1024 * 50,  # 50KB synthetic
                        sha256_hex=f"synthetic_sha256_seed_{i:03d}",
                        immutable_flag=True,
                        created_by_user_id=creator_user.id,
                    )
                    db.add(file_obj)
                    db.flush()

                    # Create attachment linking file to item
                    attachment = ChecklistAttachment(
                        checklist_instance_id=checklist_instance.id,
                        checklist_instance_item_id=site_photo_item.id,
                        file_object_id=file_obj.id,
                        uploaded_by_user_id=creator_user.id,
                        uploaded_at_utc=datetime.now(timezone.utc),
                    )
                    db.add(attachment)

                print("    Created 2 file objects and attachments for site_photo")

            # Create instance-level location
            location = ChecklistLocation(
                checklist_instance_id=checklist_instance.id,
                checklist_instance_item_id=None,  # Instance-level
                latitude=59.3293,  # Stockholm coordinates
                longitude=18.0686,
                accuracy_meters=10.0,
                captured_by_user_id=creator_user.id,
                captured_at_utc=datetime.now(timezone.utc),
            )
            db.add(location)
            print("    Created instance-level location")

            db.commit()

            # Create second checklist instance SYN-CL-0041 (submitted with all requirements met)
            checklist_instance_submitted = ChecklistInstance(
                template_version_id=published_version.id,
                title="SYN-CL-0041",
                status="submitted",
                template_snapshot_json=template_snapshot_for_submitted,
                visibility_trace_json=json.dumps({
                    "site_access": {"visible": True, "required": True, "has_condition": False},
                    "obstruction_details": {"visible": False, "required": False, "has_condition": True},
                    "site_photo": {"visible": True, "required": False, "has_condition": False},
                }),
                created_by_user_id=creator_user.id,
                submitted_by_user_id=creator_user.id,
                submitted_at_utc=datetime.now(timezone.utc),
            )
            db.add(checklist_instance_submitted)
            db.flush()
            print("  Created checklist instance: SYN-CL-0041 (submitted)")

            # Create instance items for submitted checklist
            submitted_instance_items = []
            for template_item in template_items:
                # Get condition if exists
                condition_result = db.query(ChecklistItemCondition).filter(
                    ChecklistItemCondition.template_item_id == template_item.id
                ).first()

                condition_snapshot = None
                if condition_result:
                    condition_snapshot = json.dumps({
                        "source_item_key": condition_result.source_item_key,
                        "operator": condition_result.operator,
                        "expected_value": condition_result.expected_value
                    })

                submitted_instance_item = ChecklistInstanceItem(
                    checklist_instance_id=checklist_instance_submitted.id,
                    template_item_id=template_item.id,
                    item_key=template_item.item_key,
                    label=template_item.label,
                    item_type=template_item.item_type,
                    display_order=template_item.display_order,
                    is_required=template_item.is_required,
                    evidence_required=template_item.evidence_required,
                    location_mode=template_item.location_mode,
                    condition_snapshot_json=condition_snapshot,
                )
                db.add(submitted_instance_item)
                submitted_instance_items.append(submitted_instance_item)

            db.flush()
            print("    Created checklist instance items for submitted checklist")

            # Add answers for submitted checklist
            # Answer 1: site_access = "Clear" (condition not triggered, obstruction_details hidden)
            submitted_site_access_item = next((item for item in submitted_instance_items if item.item_key == "site_access"), None)
            if submitted_site_access_item:
                submitted_answer1 = ChecklistAnswer(
                    checklist_instance_item_id=submitted_site_access_item.id,
                    value_type="text",
                    value_text="Clear",
                    answered_by_user_id=creator_user.id,
                    answered_at_utc=datetime.now(timezone.utc),
                )
                db.add(submitted_answer1)
                print("    Created answer: site_access = Clear (submitted checklist)")

            db.flush()

            # Add attachments for submitted checklist (site_photo has evidence_required but is not required)
            submitted_site_photo_item = next((item for item in submitted_instance_items if item.item_key == "site_photo"), None)
            if submitted_site_photo_item:
                # Create 2 sample file objects for submitted checklist
                for i in range(3, 5):
                    submitted_file_obj = FileObject(
                        storage_bucket="checklist-attachments",
                        storage_key=f"seed/submitted_photo_{i}.jpg",
                        original_filename=f"site_photo_{i}.jpg",
                        content_type="image/jpeg",
                        byte_size=1024 * 60,  # 60KB synthetic
                        sha256_hex=f"synthetic_sha256_submitted_{i:03d}",
                        immutable_flag=True,
                        created_by_user_id=creator_user.id,
                    )
                    db.add(submitted_file_obj)
                    db.flush()

                    # Create attachment linking file to item
                    submitted_attachment = ChecklistAttachment(
                        checklist_instance_id=checklist_instance_submitted.id,
                        checklist_instance_item_id=submitted_site_photo_item.id,
                        file_object_id=submitted_file_obj.id,
                        uploaded_by_user_id=creator_user.id,
                        uploaded_at_utc=datetime.now(timezone.utc),
                    )
                    db.add(submitted_attachment)

                print("    Created 2 file objects and attachments for submitted checklist")

            # Create instance-level location for submitted checklist
            submitted_location = ChecklistLocation(
                checklist_instance_id=checklist_instance_submitted.id,
                checklist_instance_item_id=None,  # Instance-level
                latitude=59.3293,  # Stockholm coordinates
                longitude=18.0686,
                accuracy_meters=5.0,
                captured_by_user_id=creator_user.id,
                captured_at_utc=datetime.now(timezone.utc),
            )
            db.add(submitted_location)
            print("    Created instance-level location for submitted checklist")

    db.commit()

    # Seed ingestion records with linked file_objects
    from app.models.ingestion import IngestionRecord, IngestionRowResult, ValidationIssue

    # Check if ingestion seed data already exists
    existing_ingestion = db.query(IngestionRecord).filter(IngestionRecord.id == 1).first()
    if not existing_ingestion and admin_user:
        # Get mapping version and validation rule set (use v2.0 active version)
        mapping_version = db.query(MappingVersion).filter(
            MappingVersion.version_label == "v2.0",
            MappingVersion.status == "active"
        ).first()
        validation_rule_set = db.query(ValidationRuleSet).filter(
            ValidationRuleSet.rule_set_code == "SITE_DATA_RULES_V1"
        ).first()

        if mapping_version and validation_rule_set:
            # Create file objects for ingestion raw files
            # File 1: SYN-ING-0107 - completed ingestion uploaded by ASP user
            file_obj_completed = FileObject(
                storage_bucket="ingestion-raw-files",
                storage_key="seed/SYN-ING-0107.xlsx",
                original_filename="site_data_batch_0107.xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                byte_size=1024 * 150,  # 150KB synthetic
                sha256_hex="synthetic_sha256_ingestion_completed_0107",
                immutable_flag=True,
                created_by_user_id=asp_user.id if asp_user else admin_user.id,
            )
            db.add(file_obj_completed)
            db.flush()
            print("  Created file object for completed ingestion")

            # Create ingestion record SYN-ING-0107 (completed with row results) uploaded by ASP user
            ingestion_completed = IngestionRecord(
                mapping_version_id=mapping_version.id,
                validation_rule_set_id=validation_rule_set.id,
                raw_file_object_id=file_obj_completed.id,
                status="completed",
                source_filename="site_data_batch_0107.xlsx",
                uploaded_by_user_id=asp_user.id if asp_user else admin_user.id,
                uploaded_at_utc=datetime.now(timezone.utc),
                validation_started_at_utc=datetime.now(timezone.utc),
                validation_completed_at_utc=datetime.now(timezone.utc),
                accepted_count=1190,
                rejected_count=22,
                warning_count=36,
            )
            db.add(ingestion_completed)
            db.flush()
            print("  Created ingestion record: SYN-ING-0107 (completed, 1190 accepted, 36 warnings, 22 rejected)")

            # Create sample row results for SYN-ING-0107
            # 1190 accepted, 36 accepted_with_warning, 22 rejected = 1248 total
            # Create a representative sample of each outcome type

            # Accepted rows (sample)
            for row_num in range(1, 11):
                row_result = IngestionRowResult(
                    ingestion_id=ingestion_completed.id,
                    row_number=row_num,
                    target_record_key=f"SITE-{row_num:04d}",
                    mapped_payload_json=json.dumps({
                        "site_id": f"SITE-{row_num:04d}",
                        "site_name": f"Site {row_num}",
                        "latitude": 59.3293,
                        "longitude": 18.0686,
                    }),
                    outcome="accepted",
                )
                db.add(row_result)
                db.flush()
            print("    Created 10 sample accepted row results")

            # Accepted with warning rows (sample)
            for row_num in range(11, 17):
                row_result = IngestionRowResult(
                    ingestion_id=ingestion_completed.id,
                    row_number=row_num,
                    target_record_key=f"SITE-{row_num:04d}",
                    mapped_payload_json=json.dumps({
                        "site_id": f"SITE-{row_num:04d}",
                        "site_name": f"This is a very long site name that exceeds recommended length limits for site {row_num}",
                        "latitude": 59.3293,
                        "longitude": 18.0686,
                    }),
                    outcome="accepted_with_warning",
                )
                db.add(row_result)
                db.flush()

                # Create validation issue for warning
                issue = ValidationIssue(
                    ingestion_id=ingestion_completed.id,
                    ingestion_row_result_id=row_result.id,
                    issue_scope="row",
                    issue_code="SITE_NAME_LENGTH",
                    severity="warning",
                    message="Site name exceeds recommended length",
                    rule_code="SITE_NAME_LENGTH",
                )
                db.add(issue)
            print("    Created 6 sample accepted_with_warning row results with issues")

            # Rejected rows (sample)
            for row_num in range(17, 23):
                row_result = IngestionRowResult(
                    ingestion_id=ingestion_completed.id,
                    row_number=row_num,
                    target_record_key=f"SITE-{row_num:04d}",
                    mapped_payload_json=json.dumps({
                        "site_id": f"SITE-{row_num:04d}",
                        "site_name": f"Invalid Site {row_num}",
                        "latitude": 95.0,  # Out of range
                        "longitude": 18.0686,
                    }),
                    outcome="rejected",
                )
                db.add(row_result)
                db.flush()

                # Create validation issue for error
                issue = ValidationIssue(
                    ingestion_id=ingestion_completed.id,
                    ingestion_row_result_id=row_result.id,
                    issue_scope="row",
                    issue_code="LATITUDE_RANGE",
                    severity="error",
                    message="Invalid latitude: out of range",
                    rule_code="LATITUDE_RANGE",
                )
                db.add(issue)
            print("    Created 6 sample rejected row results with issues")

            # Rejected row with missing required field (sample)
            for row_num in range(23, 27):
                row_result = IngestionRowResult(
                    ingestion_id=ingestion_completed.id,
                    row_number=row_num,
                    target_record_key=f"SITE-{row_num:04d}",
                    mapped_payload_json=json.dumps({
                        "site_id": f"SITE-{row_num:04d}",
                        # Missing site_name
                        "latitude": 59.3293,
                        "longitude": 18.0686,
                    }),
                    outcome="rejected",
                )
                db.add(row_result)
                db.flush()

                # Create validation issue for missing field
                issue = ValidationIssue(
                    ingestion_id=ingestion_completed.id,
                    ingestion_row_result_id=row_result.id,
                    issue_scope="row",
                    issue_code="required_field_missing",
                    severity="error",
                    message="Missing required field: site_name",
                    rule_code=None,
                )
                db.add(issue)
            print("    Created 4 sample rejected row results with missing field issues")

            # File 2: SYN-ING-0105 - failed structural validation
            file_obj_failed = FileObject(
                storage_bucket="ingestion-raw-files",
                storage_key="seed/SYN-ING-0105.xlsx",
                original_filename="site_data_batch_0105.xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                byte_size=1024 * 80,  # 80KB synthetic
                sha256_hex="synthetic_sha256_ingestion_failed_0105",
                immutable_flag=True,
                created_by_user_id=admin_user.id,
            )
            db.add(file_obj_failed)
            db.flush()
            print("  Created file object for failed ingestion")

            # Create ingestion record SYN-ING-0105 (failed structural validation)
            ingestion_failed = IngestionRecord(
                mapping_version_id=mapping_version.id,
                validation_rule_set_id=validation_rule_set.id,
                raw_file_object_id=file_obj_failed.id,
                status="failed",
                source_filename="site_data_batch_0105.xlsx",
                uploaded_by_user_id=admin_user.id,
                uploaded_at_utc=datetime.now(timezone.utc),
                failure_detail="Required sheet 'Sites' not found",
            )
            db.add(ingestion_failed)
            db.flush()
            print("  Created ingestion record: SYN-ING-0105 (failed, missing required sheet)")

            # Create generated report for SYN-ING-0107
            from app.models.ingestion import GeneratedReport

            # Create report file object
            report_file_obj = FileObject(
                storage_bucket="ingestion-reports",
                storage_key="seed/report_1.csv",
                original_filename="report_1.csv",
                content_type="text/csv",
                byte_size=1024 * 128,  # 128KB synthetic
                sha256_hex="synthetic_sha256_report_0107",
                immutable_flag=True,
                created_by_user_id=admin_user.id,
            )
            db.add(report_file_obj)
            db.flush()
            print("  Created report file object for SYN-ING-0107")

            # Create generated report record
            generated_report = GeneratedReport(
                ingestion_id=ingestion_completed.id,
                file_object_id=report_file_obj.id,
                report_type="csv",
                generated_at_utc=datetime(2026, 11, 12, 9, 15, 0, tzinfo=timezone.utc),
                generated_by_user_id=admin_user.id,
            )
            db.add(generated_report)
            db.flush()
            print("  Created generated report for SYN-ING-0107 (CSV, 128KB, 2026-11-12T09:15Z)")

    db.commit()

    print("Seed data complete!")


if __name__ == "__main__":
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
