import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import IngestionUploadPage from '../pages/IngestionUploadPage';

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('IngestionUploadPage', () => {
  it('renders upload page heading', () => {
    render(
      <BrowserRouter>
        <IngestionUploadPage />
      </BrowserRouter>
    );
    expect(screen.getByRole('heading', { name: /upload excel workbook/i })).toBeInTheDocument();
  });

  it('renders ASP restricted access tag', () => {
    render(
      <BrowserRouter>
        <IngestionUploadPage />
      </BrowserRouter>
    );
    expect(screen.getByText(/ASP · restricted access/i)).toBeInTheDocument();
  });

  it('renders file uploader', () => {
    render(
      <BrowserRouter>
        <IngestionUploadPage />
      </BrowserRouter>
    );
    expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
  });

  it('renders mapping version selector', () => {
    render(
      <BrowserRouter>
        <IngestionUploadPage />
      </BrowserRouter>
    );
    expect(screen.getByLabelText(/mapping version/i)).toBeInTheDocument();
  });

  it('renders upload button', () => {
    render(
      <BrowserRouter>
        <IngestionUploadPage />
      </BrowserRouter>
    );
    expect(screen.getByRole('button', { name: /upload and validate/i })).toBeInTheDocument();
  });

  it('renders immutability notification', () => {
    render(
      <BrowserRouter>
        <IngestionUploadPage />
      </BrowserRouter>
    );
    expect(screen.getByText(/uploads are permanent/i)).toBeInTheDocument();
  });
});
