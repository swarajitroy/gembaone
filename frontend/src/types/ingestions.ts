export interface IngestionRecord {
  id: number
  status: 'submitted' | 'validating' | 'completed' | 'failed'
  source_filename: string
  uploaded_by: number
  uploaded_at: string
  accepted_count: number
  rejected_count: number
  warning_count: number
  failure_detail: string | null
  mapping_version_id: number
  validation_rule_set_id: number | null
  raw_file_object_id: number
  validation_started_at: string | null
  validation_completed_at: string | null
}

export interface IngestionListResponse {
  items: IngestionRecord[]
  total: number
}
