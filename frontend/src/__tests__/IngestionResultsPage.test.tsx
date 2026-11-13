import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import IngestionResultsPage from '../pages/IngestionResultsPage';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('IngestionResultsPage', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === '/ingestions/107') {
        return {
          id: 107,
          status: 'completed',
          source_filename: 'site_data_batch_0107.xlsx',
          mapping_version_id: 1,
          uploaded_at: '2026-11-12T10:30:00Z',
          validation_started_at: '2026-11-12T10:30:05Z',
          validation_completed_at: '2026-11-12T10:30:15Z',
          accepted_count: 1190,
          rejected_count: 22,
          warning_count: 36,
        };
      }
      if (path.includes('/ingestions/107/results')) {
        return {
          items: [
            {
              row_number: 1,
              outcome: 'accepted',
              target_record_key: 'SITE-0001',
              issues: [],
            },
            {
              row_number: 2,
              outcome: 'accepted_with_warning',
              target_record_key: 'SITE-0002',
              issues: [
                {
                  code: 'SITE_NAME_LENGTH',
                  severity: 'warning',
                  message: 'Site name exceeds recommended length',
                  rule_code: 'SITE_NAME_LENGTH',
                },
              ],
            },
          ],
          total: 1248,
        };
      }
      throw new Error(`Unknown endpoint: ${path}`);
    });
  });

  it('renders results page heading', async () => {
    window.history.pushState({}, 'Test page', '/ingestions/107');
    
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/ingestions/:id" element={<IngestionResultsPage />} />
        </Routes>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /ingestion syn-ing-0107/i })).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('renders status tag', async () => {
    window.history.pushState({}, 'Test page', '/ingestions/107');
    
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/ingestions/:id" element={<IngestionResultsPage />} />
        </Routes>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('renders download buttons', async () => {
    window.history.pushState({}, 'Test page', '/ingestions/107');
    
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/ingestions/:id" element={<IngestionResultsPage />} />
        </Routes>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /download raw file/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /download result report/i })).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('renders summary tiles', async () => {
    window.history.pushState({}, 'Test page', '/ingestions/107');
    
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/ingestions/:id" element={<IngestionResultsPage />} />
        </Routes>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/rows processed/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // These are part of the tiles, should be visible once tiles load
    const acceptedElements = screen.getAllByText(/accepted/i);
    expect(acceptedElements.length).toBeGreaterThan(0);
    const rejectedElements = screen.getAllByText(/rejected/i);
    expect(rejectedElements.length).toBeGreaterThan(0);
  });

  it('renders row results table', async () => {
    window.history.pushState({}, 'Test page', '/ingestions/107');
    
    render(
      <BrowserRouter>
        <Routes>
          <Route path="/ingestions/:id" element={<IngestionResultsPage />} />
        </Routes>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/row-level results/i)).toBeInTheDocument();
    }, { timeout: 3000 });
    
    // Check for table headers which should be present once the heading appears
    const outcomeElements = screen.getAllByText(/outcome/i);
    expect(outcomeElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/target record key/i)).toBeInTheDocument();
  });
});
