// Template type definitions

export interface TemplateItem {
  id: number
  template_version_id: number
  item_key: string
  label: string
  item_type: 'text' | 'number' | 'boolean' | 'date' | 'single_select' | 'multi_select' | 'file'
  display_order: number
  is_required: boolean
  evidence_required: boolean
  location_mode: 'none' | 'optional' | 'required'
  options_json: { choices?: string[] } | null
  condition?: ItemCondition | null
  created_at_utc: string
}

export interface ItemCondition {
  id: number
  template_item_id: number
  source_item_key: string
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than'
  expected_value: string
  created_at_utc: string
}

export interface TemplateVersion {
  id: number
  template_id: number
  version_number: number
  version_label: string
  status: 'draft' | 'published' | 'superseded'
  published_at_utc: string | null
  published_by_user_id: number | null
  items?: TemplateItem[]
  created_at_utc: string
}

export interface Template {
  id: number
  template_code: string
  name: string
  description: string | null
  current_version_id: number | null
  status: 'active' | 'retired'
  created_by_user_id: number
  created_at_utc: string
  updated_at_utc: string
}

export interface TemplateWithVersions extends Template {
  versions: TemplateVersion[]
  active_version?: TemplateVersion
  draft_version?: TemplateVersion
}

// Create/update request types
export interface CreateTemplateItemRequest {
  item_key: string
  label: string
  item_type: 'text' | 'number' | 'boolean' | 'date' | 'single_select' | 'multi_select' | 'file'
  display_order: number
  is_required: boolean
  evidence_required: boolean
  location_mode: 'none' | 'optional' | 'required'
  options?: { choices?: string[] }
  condition?: {
    source_item_key: string
    operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than'
    expected_value: string
  }
}

export interface PublishVersionRequest {
  version_label: string
  items: CreateTemplateItemRequest[]
}
