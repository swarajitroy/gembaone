import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ChecklistReviewPage } from '../pages/ChecklistReviewPage'
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
  useAuth: () => ({ user: { id: 1, email: 'test@example.com', role_codes: ['reviewer'] }, logout: vi.fn() })
}))

describe('ChecklistReviewPage', () => {
  const mockChecklist = {
    instance: {
      id: 1,
      template_version_id: 1,
      title: 'SYN-CL-0041',
      status: 'submitted',
      visibility_trace_json: '{}',
      created_by_user_id: 1,
      created_at_utc: '2026-11-12T08:00:00Z',
      submitted_by_user_id: 1,
      submitted_at_utc: '2026-11-12T10:30:00Z'
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
    locations: [
      {
        id: 1,
        checklist_instance_id: 1,
        checklist_instance_item_id: null,
        latitude: 59.3293,
        longitude: 18.0686,
        accuracy_meters: 10,
        captured_by_user_id: 1,
        captured_at_utc: '2026-11-12T09:16:00Z'
      }
    ],
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
        <ChecklistReviewPage />
      </BrowserRouter>
    )
    
    expect(screen.getByText(/loading checklist/i)).toBeInTheDocument()
  })

  it('renders review page with tabs after loading', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockChecklist)
    
    render(
      <BrowserRouter>
        <ChecklistReviewPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/review:/i)).toBeInTheDocument()
    })
    
    expect(screen.getByRole('tab', { name: /answers/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /evidence/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /locations/i })).toBeInTheDocument()
  })

  it('displays submitted tag and read-only indicator', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockChecklist)
    
    render(
      <BrowserRouter>
        <ChecklistReviewPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      const submittedElements = screen.getAllByText(/submitted/i)
      const readOnlyElements = screen.getAllByText(/read-only/i)
      expect(submittedElements.length).toBeGreaterThan(0)
      expect(readOnlyElements.length).toBeGreaterThan(0)
    })
  })

  it('displays locations table', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockChecklist)
    
    render(
      <BrowserRouter>
        <ChecklistReviewPage />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/whole checklist/i)).toBeInTheDocument()
    })
  })
})
