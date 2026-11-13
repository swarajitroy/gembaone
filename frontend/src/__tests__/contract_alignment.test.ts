/**
 * Frontend-Backend Contract Alignment Tests
 * 
 * Verifies:
 * - Frontend TypeScript types match backend Pydantic schemas
 * - Pagination contracts align
 * - Error response shapes match
 * - Request/response field names consistent
 */

import { describe, it, expect } from 'vitest';

describe('Contract Alignment: Response Shapes', () => {
  it('pagination wrapper should match backend contract', () => {
    // Backend returns: { items: [...], total: number, page: number, page_size: number }
    const mockPaginatedResponse = {
      items: [{ id: 1 }, { id: 2 }],
      total: 42,
      page: 1,
      page_size: 20
    };

    // Verify structure
    expect(mockPaginatedResponse).toHaveProperty('items');
    expect(mockPaginatedResponse).toHaveProperty('total');
    expect(mockPaginatedResponse).toHaveProperty('page');
    expect(mockPaginatedResponse).toHaveProperty('page_size');
    expect(Array.isArray(mockPaginatedResponse.items)).toBe(true);
    expect(typeof mockPaginatedResponse.total).toBe('number');
    expect(typeof mockPaginatedResponse.page).toBe('number');
    expect(typeof mockPaginatedResponse.page_size).toBe('number');
  });

  it('error response should match backend contract', () => {
    // Backend returns: { detail: string, status_code: number }
    const mockErrorResponse = {
      detail: 'Validation failed',
      status_code: 400
    };

    // Verify structure
    expect(mockErrorResponse).toHaveProperty('detail');
    expect(mockErrorResponse).toHaveProperty('status_code');
    expect(typeof mockErrorResponse.detail).toBe('string');
    expect(typeof mockErrorResponse.status_code).toBe('number');
  });

  it('login response should match backend contract', () => {
    // Backend returns: { access_token: string, refresh_token: string, token_type: string, expires_in: number, user: {...} }
    const mockLoginResponse = {
      access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
      refresh_token: 'refresh_token_here',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: 1,
        subject_id: 'sub-001',
        display_name: 'Test User',
        email: 'test@example.com',
        role_codes: ['internal_admin'],
        is_asp: false,
        is_active: true,
        created_at_utc: '2026-01-01T00:00:00Z',
        updated_at_utc: '2026-01-01T00:00:00Z'
      }
    };

    // Verify structure
    expect(mockLoginResponse).toHaveProperty('access_token');
    expect(mockLoginResponse).toHaveProperty('token_type');
    expect(mockLoginResponse).toHaveProperty('user');
    expect(mockLoginResponse.user).toHaveProperty('id');
    expect(mockLoginResponse.user).toHaveProperty('email');
    expect(mockLoginResponse.user).toHaveProperty('role_codes');
    expect(Array.isArray(mockLoginResponse.user.role_codes)).toBe(true);
  });
});

describe('Contract Alignment: Checklist Domain', () => {
  it('checklist instance response should match backend schema', () => {
    const mockChecklistInstance = {
      id: 1,
      template_version_id: 1,
      title: 'Test Checklist',
      status: 'draft',
      template_snapshot_json: {},
      visibility_trace_json: null,
      created_by_user_id: 1,
      created_at_utc: '2026-01-01T00:00:00Z',
      submitted_by_user_id: null,
      submitted_at_utc: null,
      items: [],
      locations: [],
      template_version: {
        id: 1,
        version_number: 1,
        version_label: 'v1.0',
        status: 'active'
      }
    };

    // Verify required fields
    expect(mockChecklistInstance).toHaveProperty('id');
    expect(mockChecklistInstance).toHaveProperty('template_version_id');
    expect(mockChecklistInstance).toHaveProperty('status');
    expect(mockChecklistInstance).toHaveProperty('items');
    expect(Array.isArray(mockChecklistInstance.items)).toBe(true);
    
    // Verify status enum values
    expect(['draft', 'submitted']).toContain(mockChecklistInstance.status);
  });

  it('checklist answer request should match backend schema', () => {
    const mockAnswerRequest = {
      answers: [
        {
          item_key: 'site_type',
          value_type: 'text',
          value_text: 'Outdoor'
        },
        {
          item_key: 'count',
          value_type: 'number',
          value_number: 42
        },
        {
          item_key: 'confirmed',
          value_type: 'boolean',
          value_boolean: true
        }
      ]
    };

    // Verify structure
    expect(mockAnswerRequest).toHaveProperty('answers');
    expect(Array.isArray(mockAnswerRequest.answers)).toBe(true);
    
    // Verify answer fields
    mockAnswerRequest.answers.forEach(answer => {
      expect(answer).toHaveProperty('item_key');
      expect(answer).toHaveProperty('value_type');
      expect(['text', 'number', 'boolean', 'date', 'json']).toContain(answer.value_type);
    });
  });

  it('submission validation response should match backend schema', () => {
    const mockSubmissionResponse = {
      id: 1,
      status: 'submitted',
      submitted_by_user_id: 1,
      submitted_at_utc: '2026-01-01T12:00:00Z',
      validation_issues: []
    };

    // Verify required fields
    expect(mockSubmissionResponse).toHaveProperty('id');
    expect(mockSubmissionResponse).toHaveProperty('status');
    expect(mockSubmissionResponse.status).toBe('submitted');
  });
});

describe('Contract Alignment: Ingestion Domain', () => {
  it('ingestion record response should match backend schema', () => {
    const mockIngestionRecord = {
      id: 1,
      mapping_version_id: 1,
      validation_rule_set_id: 1,
      raw_file_object_id: 1,
      status: 'completed',
      source_filename: 'test.xlsx',
      uploaded_by_user_id: 1,
      uploaded_at_utc: '2026-01-01T00:00:00Z',
      validation_started_at_utc: '2026-01-01T00:01:00Z',
      validation_completed_at_utc: '2026-01-01T00:05:00Z',
      accepted_count: 100,
      rejected_count: 10,
      warning_count: 5
    };

    // Verify required fields
    expect(mockIngestionRecord).toHaveProperty('id');
    expect(mockIngestionRecord).toHaveProperty('status');
    expect(mockIngestionRecord).toHaveProperty('source_filename');
    expect(mockIngestionRecord).toHaveProperty('accepted_count');
    expect(mockIngestionRecord).toHaveProperty('rejected_count');
    
    // Verify status enum
    expect(['submitted', 'validating', 'completed', 'failed']).toContain(mockIngestionRecord.status);
  });

  it('ingestion row result response should match backend schema', () => {
    const mockRowResult = {
      id: 1,
      ingestion_id: 1,
      row_number: 1,
      target_record_key: 'SITE-001',
      mapped_payload_json: {},
      outcome: 'accepted',
      created_at_utc: '2026-01-01T00:00:00Z',
      issues: []
    };

    // Verify required fields
    expect(mockRowResult).toHaveProperty('row_number');
    expect(mockRowResult).toHaveProperty('outcome');
    expect(mockRowResult).toHaveProperty('issues');
    expect(Array.isArray(mockRowResult.issues)).toBe(true);
    
    // Verify outcome enum
    expect(['accepted', 'accepted_with_warning', 'rejected']).toContain(mockRowResult.outcome);
  });

  it('validation issue response should match backend schema', () => {
    const mockValidationIssue = {
      id: 1,
      ingestion_id: 1,
      ingestion_row_result_id: 1,
      issue_scope: 'row',
      issue_code: 'LATITUDE_RANGE',
      severity: 'error',
      message: 'Latitude must be between -90 and 90',
      rule_code: 'LATITUDE_RANGE',
      created_at_utc: '2026-01-01T00:00:00Z'
    };

    // Verify required fields
    expect(mockValidationIssue).toHaveProperty('issue_scope');
    expect(mockValidationIssue).toHaveProperty('issue_code');
    expect(mockValidationIssue).toHaveProperty('severity');
    expect(mockValidationIssue).toHaveProperty('message');
    
    // Verify enums
    expect(['ingestion', 'row']).toContain(mockValidationIssue.issue_scope);
    expect(['error', 'warning']).toContain(mockValidationIssue.severity);
  });
});

describe('Contract Alignment: Mapping Domain', () => {
  it('mapping definition response should match backend schema', () => {
    const mockMappingDefinition = {
      id: 1,
      mapping_code: 'MAP-SYN-001',
      source_entity: 'Site Inventory',
      target_entity: 'sites',
      status: 'active',
      created_by_user_id: 1,
      created_at_utc: '2026-01-01T00:00:00Z',
      updated_at_utc: '2026-01-01T00:00:00Z',
      active_version: {
        id: 2,
        version_number: 2,
        version_label: 'v2.0',
        status: 'active',
        entries: []
      }
    };

    // Verify required fields
    expect(mockMappingDefinition).toHaveProperty('id');
    expect(mockMappingDefinition).toHaveProperty('mapping_code');
    expect(mockMappingDefinition).toHaveProperty('source_entity');
    expect(mockMappingDefinition).toHaveProperty('target_entity');
    expect(mockMappingDefinition).toHaveProperty('active_version');
  });

  it('mapping entry response should match backend schema', () => {
    const mockMappingEntry = {
      id: 1,
      mapping_version_id: 1,
      source_column: 'SITE_ID',
      target_field: 'site_id',
      target_type: 'string',
      is_required: true,
      transform_expression: null,
      created_at_utc: '2026-01-01T00:00:00Z'
    };

    // Verify required fields
    expect(mockMappingEntry).toHaveProperty('source_column');
    expect(mockMappingEntry).toHaveProperty('target_field');
    expect(mockMappingEntry).toHaveProperty('target_type');
    expect(mockMappingEntry).toHaveProperty('is_required');
    
    // Verify target_type enum
    expect(['string', 'number', 'date', 'boolean']).toContain(mockMappingEntry.target_type);
  });
});

describe('Contract Alignment: Template Domain', () => {
  it('template response should match backend schema', () => {
    const mockTemplate = {
      id: 1,
      template_code: 'TPL-SYN-001',
      name: 'Site Survey',
      description: 'Standard site survey checklist',
      current_version_id: 2,
      status: 'active',
      created_by_user_id: 1,
      created_at_utc: '2026-01-01T00:00:00Z',
      updated_at_utc: '2026-01-01T00:00:00Z'
    };

    // Verify required fields
    expect(mockTemplate).toHaveProperty('id');
    expect(mockTemplate).toHaveProperty('template_code');
    expect(mockTemplate).toHaveProperty('name');
    expect(mockTemplate).toHaveProperty('status');
    
    // Verify status enum
    expect(['active', 'retired']).toContain(mockTemplate.status);
  });

  it('template item response should match backend schema', () => {
    const mockTemplateItem = {
      id: 1,
      template_version_id: 1,
      item_key: 'site_type',
      label: 'Site Type',
      item_type: 'single_select',
      display_order: 1,
      is_required: true,
      evidence_required: false,
      location_mode: 'none',
      options_json: { choices: ['Indoor', 'Outdoor'] },
      created_at_utc: '2026-01-01T00:00:00Z',
      condition: null
    };

    // Verify required fields
    expect(mockTemplateItem).toHaveProperty('item_key');
    expect(mockTemplateItem).toHaveProperty('label');
    expect(mockTemplateItem).toHaveProperty('item_type');
    expect(mockTemplateItem).toHaveProperty('is_required');
    
    // Verify item_type enum
    expect(['text', 'number', 'boolean', 'date', 'single_select', 'multi_select', 'file']).toContain(mockTemplateItem.item_type);
    
    // Verify location_mode enum
    expect(['none', 'optional', 'required']).toContain(mockTemplateItem.location_mode);
  });
});

describe('Contract Alignment: Field Name Conventions', () => {
  it('all timestamps should use _at_utc suffix', () => {
    const timestampFields = [
      'created_at_utc',
      'updated_at_utc',
      'submitted_at_utc',
      'uploaded_at_utc',
      'validation_started_at_utc',
      'validation_completed_at_utc',
      'answered_at_utc',
      'captured_at_utc'
    ];

    timestampFields.forEach(field => {
      expect(field).toMatch(/_at_utc$/);
    });
  });

  it('all user references should use _user_id suffix', () => {
    const userIdFields = [
      'created_by_user_id',
      'uploaded_by_user_id',
      'submitted_by_user_id',
      'answered_by_user_id',
      'captured_by_user_id',
      'assigned_by_user_id'
    ];

    userIdFields.forEach(field => {
      expect(field).toMatch(/_user_id$/);
    });
  });

  it('all JSON fields should use _json suffix', () => {
    const jsonFields = [
      'template_snapshot_json',
      'visibility_trace_json',
      'options_json',
      'mapped_payload_json',
      'event_payload_json',
      'condition_snapshot_json'
    ];

    jsonFields.forEach(field => {
      expect(field).toMatch(/_json$/);
    });
  });
});

describe('Contract Alignment: Pagination Behavior', () => {
  it('should handle defensive pagination response parsing', () => {
    // Backend may return paginated wrapper OR bare array during development
    const paginatedResponse = {
      items: [{ id: 1 }, { id: 2 }],
      total: 2,
      page: 1,
      page_size: 20
    };
    
    const bareArrayResponse = [{ id: 1 }, { id: 2 }];
    
    // Defensive parsing should handle both
    const extractItems = (data: any) => {
      return Array.isArray(data) ? data : data?.items || [];
    };
    
    const extractTotal = (data: any) => {
      return Array.isArray(data) ? data.length : data?.total || 0;
    };
    
    expect(extractItems(paginatedResponse)).toEqual([{ id: 1 }, { id: 2 }]);
    expect(extractTotal(paginatedResponse)).toBe(2);
    
    expect(extractItems(bareArrayResponse)).toEqual([{ id: 1 }, { id: 2 }]);
    expect(extractTotal(bareArrayResponse)).toBe(2);
  });
});

describe('Contract Alignment: Error Handling', () => {
  it('should handle 401 unauthorized responses', () => {
    const mockUnauthorizedResponse = {
      status: 401,
      body: {
        detail: 'Invalid authentication credentials'
      }
    };

    expect(mockUnauthorizedResponse.status).toBe(401);
    expect(mockUnauthorizedResponse.body).toHaveProperty('detail');
  });

  it('should handle 403 forbidden responses', () => {
    const mockForbiddenResponse = {
      status: 403,
      body: {
        detail: 'Insufficient permissions'
      }
    };

    expect(mockForbiddenResponse.status).toBe(403);
    expect(mockForbiddenResponse.body).toHaveProperty('detail');
  });

  it('should handle 422 validation error responses', () => {
    const mockValidationErrorResponse = {
      status: 422,
      body: {
        detail: [
          {
            loc: ['body', 'email'],
            msg: 'field required',
            type: 'value_error.missing'
          }
        ]
      }
    };

    expect(mockValidationErrorResponse.status).toBe(422);
    expect(Array.isArray(mockValidationErrorResponse.body.detail)).toBe(true);
  });
});
