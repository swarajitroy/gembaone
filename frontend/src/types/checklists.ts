export interface ChecklistInstance {
  id: string
  template_version_id: number
  title: string
  status: 'draft' | 'submitted'
  template_snapshot_json: unknown
  visibility_trace_json: unknown
  created_by_user_id: number
  created_at_utc: string
  submitted_by_user_id: number | null
  submitted_at_utc: string | null
}

export interface ChecklistListItem {
  id: string
  template_name: string
  template_version_label: string
  status: 'draft' | 'submitted'
  created_by_display_name: string
  submitted_at_utc: string | null
}
