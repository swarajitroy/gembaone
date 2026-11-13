import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { HomePage } from '../pages/HomePage'
import { apiClient } from '../lib/api-client'

const mockUser = {
  id: 1,
  subject_id: 'syn.admin',
  display_name: 'Admin User',
  email: 'admin@example.com',
  role_codes: ['internal_admin'],
  is_asp: false,
  is_active: true,
  created_at_utc: '2024-11-12T10:00:00Z',
  updated_at_utc: '2024-11-12T10:00:00Z',
}

vi.mock('../lib/auth-context', () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}))

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

const mockChecklists = [
  {
    id: 'SYN-CL-0042',
    template_name: 'SYN Tower Site Survey',
    template_version_label: 'v3',
    status: 'draft' as const,
    created_by_display_name: 'SYN field engineer',
    submitted_at_utc: null,
  },
  {
    id: 'SYN-CL-0041',
    template_name: 'SYN Rooftop Safety Walk',
    template_version_label: 'v1',
    status: 'submitted' as const,
    created_by_display_name: 'SYN field engineer',
    submitted_at_utc: '2026-11-11T16:40:00Z',
  },
]

const mockIngestions = [
  {
    id: 'SYN-ING-0107',
    status: 'completed' as const,
    source_filename: 'SYN_site_inventory_batch07.xlsx',
    uploaded_by: 1,
    uploaded_at: '2026-11-12T08:52:00Z',
    accepted_count: 1190,
    rejected_count: 22,
    warning_count: 36,
    failure_detail: null,
  },
  {
    id: 'SYN-ING-0108',
    status: 'validating' as const,
    source_filename: 'SYN_site_inventory_batch08.xlsx',
    uploaded_by: 1,
    uploaded_at: '2026-11-12T09:20:00Z',
    accepted_count: 0,
    rejected_count: 0,
    warning_count: 0,
    failure_detail: null,
  },
]

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders home page with user information', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ items: [], total: 0 })

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { name: /^home$/i })).toBeInTheDocument()
    expect(screen.getByText(/signed in as admin user/i)).toBeInTheDocument()
    // Check for internal admin tag presence (multiple instances expected)
    const internalAdminTags = screen.getAllByText(/internal admin/i)
    expect(internalAdminTags.length).toBeGreaterThan(0)
  })

  it('displays dashboard tiles', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ items: [], total: 0 })

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    // Verify dashboard tiles are present by checking for all their text content
    const tiles = screen.getAllByText('Checklist templates')
    expect(tiles.length).toBeGreaterThan(0)
    expect(screen.getByText('2 active · 1 retired')).toBeInTheDocument()
    expect(screen.getByText('3 in progress · 5 submitted')).toBeInTheDocument()
    expect(screen.getByText('1 validating · 4 completed · 1 failed')).toBeInTheDocument()
  })

  it('loads and displays recent checklists', async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === '/checklists') {
        return Promise.resolve({ items: mockChecklists, total: mockChecklists.length })
      }
      return Promise.resolve({ items: [], total: 0 })
    })

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('SYN-CL-0042')).toBeInTheDocument()
      expect(screen.getByText(/syn tower site survey/i)).toBeInTheDocument()
      expect(screen.getByText('In progress')).toBeInTheDocument()
      expect(screen.getByText('Submitted')).toBeInTheDocument()
    })
  })

  it('loads and displays recent ingestions', async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === '/ingestions') {
        return Promise.resolve({ items: mockIngestions, total: mockIngestions.length })
      }
      return Promise.resolve({ items: [], total: 0 })
    })

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('SYN-ING-0107')).toBeInTheDocument()
      expect(screen.getByText('SYN_site_inventory_batch07.xlsx')).toBeInTheDocument()
      expect(screen.getByText('Completed')).toBeInTheDocument()
      expect(screen.getByText('Validating')).toBeInTheDocument()
    })
  })

  it('shows loading state while fetching data', () => {
    vi.mocked(apiClient.get).mockImplementation(() => new Promise(() => {}))

    const { container } = render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    const loadingElements = container.querySelectorAll('[aria-busy="true"]')
    expect(loadingElements.length).toBeGreaterThan(0)
  })

  it('displays error message when checklists fail to load', async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === '/checklists') {
        return Promise.reject(new Error('Failed to fetch'))
      }
      return Promise.resolve({ items: [], total: 0 })
    })

    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/failed to load checklists/i)).toBeInTheDocument()
    })
  })

  it('displays role view information', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ items: [], total: 0 })

    const { container } = render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { name: /role view/i })).toBeInTheDocument()
    expect(container.textContent).toContain('No role can delete records')
  })
})
