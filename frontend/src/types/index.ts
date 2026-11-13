// Type definitions mirroring backend schemas

export interface User {
  id: number
  subject_id: string
  display_name: string
  email: string
  role_codes: string[]
  is_asp: boolean
  is_active: boolean
  created_at_utc: string
  updated_at_utc: string
}

export interface ChecklistTemplate {
  id: number
  template_code: string
  name: string
  description: string | null
  current_version_id: number | null
  status: string
  created_by_user_id: number
  created_at_utc: string
  updated_at_utc: string
}

export interface ChecklistInstance {
  id: number
  template_version_id: number
  title: string
  status: string
  created_by_user_id: number
  created_at_utc: string
  submitted_by_user_id: number | null
  submitted_at_utc: string | null
}

export interface IngestionRecord {
  id: number
  mapping_version_id: number
  validation_rule_set_id: number | null
  raw_file_object_id: number
  status: string
  source_filename: string
  uploaded_by: number
  uploaded_at: string
  accepted_count: number
  rejected_count: number
  warning_count: number
  failure_detail: string | null
  validation_started_at: string | null
  validation_completed_at: string | null
}

export interface MappingDefinition {
  id: number
  mapping_code: string
  source_entity: string
  target_entity: string
  status: string
  created_by_user_id: number
  created_at_utc: string
  updated_at_utc: string
}
