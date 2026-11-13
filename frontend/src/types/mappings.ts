export interface MappingEntry {
  id: number
  mapping_version_id: number
  source_column: string
  target_field: string
  target_type: 'string' | 'number' | 'date' | 'boolean'
  is_required: boolean
  transform_expression: string | null
  created_at_utc: string
}

export interface MappingVersion {
  id: number
  mapping_definition_id: number
  version_number: number
  version_label: string
  status: 'active' | 'superseded'
  published_at_utc: string | null
  published_by_user_id: number | null
  created_at_utc: string
  entries: MappingEntry[]
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
  current_version: MappingVersion
}

export interface MappingListResponse {
  items: MappingDefinition[]
  total: number
}

export interface MappingEntryRequest {
  source_column: string
  target_field: string
  target_type: 'string' | 'number' | 'date' | 'boolean'
  is_required: boolean
  transform_expression?: string | null
}

export interface PublishMappingVersionRequest {
  version_label: string
  entries: MappingEntryRequest[]
}
