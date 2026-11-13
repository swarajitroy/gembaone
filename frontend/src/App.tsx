import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './lib/auth-context'
import { RequireAuth } from './components/auth/RequireAuth'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { TemplatesPage } from './pages/TemplatesPage'
import { TemplateBuilderPage } from './pages/TemplateBuilderPage'
import { ChecklistsPage } from './pages/ChecklistsPage'
import { ChecklistExecutionPage } from './pages/ChecklistExecutionPage'
import { ChecklistReviewPage } from './pages/ChecklistReviewPage'
import { IngestionsPage } from './pages/IngestionsPage'
import IngestionUploadPage from './pages/IngestionUploadPage'
import IngestionResultsPage from './pages/IngestionResultsPage'
import { MappingsPage } from './pages/MappingsPage'
import MappingEditorPage from './pages/MappingEditorPage'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <RequireAuth>
                <HomePage />
              </RequireAuth>
            }
          />
          <Route
            path="/templates"
            element={
              <RequireAuth allowedRoles={['internal_admin', 'field_engineer']}>
                <TemplatesPage />
              </RequireAuth>
            }
          />
          <Route
            path="/templates/:id"
            element={
              <RequireAuth allowedRoles={['internal_admin', 'field_engineer']}>
                <TemplateBuilderPage />
              </RequireAuth>
            }
          />
          <Route
            path="/checklists"
            element={
              <RequireAuth>
                <ChecklistsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/checklists/:id"
            element={
              <RequireAuth>
                <ChecklistExecutionPage />
              </RequireAuth>
            }
          />
          <Route
            path="/checklists/:id/review"
            element={
              <RequireAuth>
                <ChecklistReviewPage />
              </RequireAuth>
            }
          />
          <Route
            path="/ingestions"
            element={
              <RequireAuth>
                <IngestionsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/ingestions/upload"
            element={
              <RequireAuth>
                <IngestionUploadPage />
              </RequireAuth>
            }
          />
          <Route
            path="/ingestions/:id"
            element={
              <RequireAuth>
                <IngestionResultsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/mappings"
            element={
              <RequireAuth allowedRoles={['internal_admin']}>
                <MappingsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/mappings/:id"
            element={
              <RequireAuth allowedRoles={['internal_admin']}>
                <MappingEditorPage />
              </RequireAuth>
            }
          />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
