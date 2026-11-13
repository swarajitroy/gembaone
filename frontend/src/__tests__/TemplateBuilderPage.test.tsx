import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { TemplateBuilderPage } from '../pages/TemplateBuilderPage'
import { AuthProvider } from '../lib/auth-context'
import * as apiClient from '../lib/api-client'

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

const mockTemplate = {
  id: 1,
  template_code: 'TPL-SYN-001',
  name: 'SYN Tower Site Survey',
  description: 'Synthetic survey used to demonstrate site access',
  current_version_id: 1,
  status: 'active',
  created_by_user_id: 1,
  created_at_utc: '2024-11-12T09:00:00Z',
  updated_at_utc: '2024-11-12T09:00:00Z'
}

const renderWithProviders = (component: React.ReactElement, initialRoute = '/templates/1') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <AuthProvider>
        <Routes>
          <Route path="/templates/:id" element={component} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('TemplateBuilderPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockTemplate)
  })

  it('should render template name in heading', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: mockTemplate.name })).toBeInTheDocument()
    })
  })

  it('should display template details form', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      expect(screen.getByLabelText(/Template name/i)).toHaveValue(mockTemplate.name)
      expect(screen.getByLabelText(/Template code/i)).toHaveValue(mockTemplate.template_code)
    })
  })

  it('should show info notification about immutability', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      expect(screen.getByText(/Versions are immutable/i)).toBeInTheDocument()
      expect(screen.getByText(/Published versions cannot be changed/i)).toBeInTheDocument()
    })
  })

  it('should display items accordion', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      expect(screen.getByText(/1\. Site access condition/i)).toBeInTheDocument()
      expect(screen.getByText(/2\. Describe obstruction/i)).toBeInTheDocument()
    })
  })

  it('should show version history in sidebar', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Version history/i })).toBeInTheDocument()
      expect(screen.getByText('Draft v4')).toBeInTheDocument()
      expect(screen.getByText('v3')).toBeInTheDocument()
    })
  })

  it('should show publish and cancel buttons', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      const publishButtons = screen.getAllByRole('button', { name: /Publish new version/i })
      expect(publishButtons.length).toBeGreaterThan(0)
      
      const cancelButtons = screen.getAllByRole('button', { name: /Cancel/i })
      expect(cancelButtons.length).toBeGreaterThan(0)
    })
  })

  it('should show tags for item properties', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      const tags = screen.getAllByText(/required|photo evidence|conditional/i)
      expect(tags.length).toBeGreaterThan(0)
    })
  })

  it('should display readonly fields for template details', async () => {
    renderWithProviders(<TemplateBuilderPage />)

    await waitFor(() => {
      const templateName = screen.getByLabelText(/Template name/i) as HTMLInputElement
      expect(templateName).toHaveAttribute('readonly')
      
      const templateCode = screen.getByLabelText(/Template code/i) as HTMLInputElement
      expect(templateCode).toHaveAttribute('readonly')
    })
  })
})
