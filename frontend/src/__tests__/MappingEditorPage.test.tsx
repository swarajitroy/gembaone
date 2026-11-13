import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import MappingEditorPage from '../pages/MappingEditorPage'
import { apiClient } from '../lib/api-client'
import { AuthProvider } from '../lib/auth-context'

vi.mock('../lib/api-client')

const mockMappingResponse = {
  items: [
    {
      id: 1,
      mapping_code: 'MAP-SYN-001',
      source_entity: 'SYN Site Inventory',
      target_entity: 'site',
      status: 'active',
      created_by_user_id: 1,
      created_at_utc: '2024-01-15T10:30:00Z',
      updated_at_utc: '2024-01-15T10:30:00Z',
      current_version: {
        id: 2,
        mapping_definition_id: 1,
        version_number: 2,
        version_label: 'v2.0',
        status: 'active',
        published_at_utc: '2024-01-15T11:00:00Z',
        published_by_user_id: 1,
        created_at_utc: '2024-01-15T11:00:00Z',
        entries: [
          {
            id: 5,
            mapping_version_id: 2,
            source_column: 'site_id',
            target_field: 'site_id',
            target_type: 'string' as const,
            is_required: true,
            transform_expression: null,
            created_at_utc: '2024-01-15T11:00:00Z',
          },
          {
            id: 6,
            mapping_version_id: 2,
            source_column: 'site_name',
            target_field: 'site_name',
            target_type: 'string' as const,
            is_required: true,
            transform_expression: null,
            created_at_utc: '2024-01-15T11:00:00Z',
          },
        ],
      },
    },
  ],
}

function renderWithRouter() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/mappings/:id" element={<MappingEditorPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('MappingEditorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Navigate to the route with ID parameter
    window.history.pushState({}, 'Test page', '/mappings/1')
    // Mock localStorage for auth
    localStorage.setItem('access_token', 'mock-token')
  })

  it('renders mapping editor page and calls API', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockMappingResponse)

    renderWithRouter()

    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/mappings')
    })
  })

  it('displays loading state initially', () => {
    vi.mocked(apiClient.get).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithRouter()

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('displays mapping details when loaded', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockMappingResponse)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    })
  })

  it('displays not found when mapping not in response', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ items: [] })

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Mapping not found')).toBeInTheDocument()
    })
  })
})
