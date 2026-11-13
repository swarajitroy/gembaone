import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ChecklistExecutionPage } from '../pages/ChecklistExecutionPage'
import { apiClient } from '../lib/api-client'

vi.mock('../lib/api-client')
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: '1' }),
    useNavigate: () => vi.fn()
  }
})
vi.mock('../lib/auth-context', () => ({
  useAuth: () => ({ user: { id: 1, email: 'test@example.com', role_codes: ['field_engineer'] }, logout: vi.fn() })
}))

describe('ChecklistExecutionPage', () => {
  const mockChecklist = {
    instance: {
      id: 1,
      template_version_id: 1,
      title: 'SYN-CL-0042',
      status: 'draft',
      visibility_trace_json: null,
      created_by_user_id: 1,
      created_at_utc: '2026-11-12T10:00:00Z',
      submitted_by_user_id: null,
      submitted_at_utc: null
    },
    items: [
      {
        id: 1,
        checklist_instance_id: 1,
        template_item_id: 1,
        item_key: 'site_access',
        label: 'Site access condition',
        item_type: 'select',
        display_order: 1,
        is_required: true,
        evidence_required: false,
        location_mode: 'none',
        condition_snapshot_json: null
      }
    ],
    locations: [],
    template_version: {
      id: 1,
      template_id: 1,
      version_number: 1,
      version_label: 'v1.0',
      status: 'published'
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(apiClient.get).mockImplementation(() => new Promise(() => {}))
    
    render(
      <BrowserRouter>
        <ChecklistExecutionPage />
      </BrowserRouter>
    )
    
    expect(screen.getByText(/loading checklist/i)).toBeInTheDocument()
  })

  it('renders checklist execution form after loading', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockChecklist)
    
    render(
      <BrowserRouter>
        <ChecklistExecutionPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent('SYN-CL-0042')
    })
    
    const submitButtons = screen.getAllByRole('button', { name: /submit checklist/i })
    expect(submitButtons.length).toBeGreaterThan(0)
  })

  it('displays submitted state when checklist is submitted', async () => {
    const submittedChecklist = {
      ...mockChecklist,
      instance: {
        ...mockChecklist.instance,
        status: 'submitted',
        submitted_by_user_id: 1,
        submitted_at_utc: '2026-11-12T11:00:00Z'
      }
    }
    
    vi.mocked(apiClient.get).mockResolvedValue(submittedChecklist)
    
    render(
      <BrowserRouter>
        <ChecklistExecutionPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      const submittedElements = screen.getAllByText(/submitted/i)
      expect(submittedElements.length).toBeGreaterThan(0)
    })
  })

  it('handles error state', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Failed to load'))
    
    render(
      <BrowserRouter>
        <ChecklistExecutionPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument()
    })
  })
})
