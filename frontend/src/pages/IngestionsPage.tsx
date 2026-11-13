import { useEffect, useState } from 'react'
import { Layout } from '../components/layout/Layout'
import { IngestionsTable } from '../components/ingestions/IngestionsTable'
import { IngestionRecord } from '../types/ingestions'
import { apiClient } from '../lib/api-client'
import { InlineNotification, Button, Stack, Grid, Column } from '@carbon/react'
import { Upload } from '@carbon/icons-react'
import { useNavigate } from 'react-router-dom'

export function IngestionsPage() {
  const [ingestions, setIngestions] = useState<IngestionRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    loadIngestions()
  }, [])

  const loadIngestions = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const data = await apiClient.get<{ items: IngestionRecord[] }>('/ingestions')
      setIngestions(data.items || [])
    } catch (err) {
      console.error('Failed to load ingestions:', err)
      setError(err instanceof Error ? err.message : 'Failed to load ingestions')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <Grid>
        <Column lg={16} md={8} sm={4}>
          <Stack gap={6}>
            <div>
              <h1 className="cds--productive-heading-05 mb-4">Excel Ingestion</h1>
              <p className="cds--body-01">Upload and validate Excel workbooks. View processing status and validation results.</p>
            </div>

            <Button
              kind="primary"
              renderIcon={Upload}
              onClick={() => navigate('/ingestions/upload')}
            >
              Upload workbook
            </Button>

            {loading && (
              <p className="cds--body-01">Loading ingestions...</p>
            )}

            {error && (
              <InlineNotification
                kind="error"
                title="Error"
                subtitle={error}
                lowContrast
              />
            )}

            {!loading && !error && ingestions.length === 0 && (
              <p className="cds--body-01">No ingestions yet. Upload your first workbook.</p>
            )}

            {!loading && !error && ingestions.length > 0 && (
              <IngestionsTable ingestions={ingestions} />
            )}
          </Stack>
        </Column>
      </Grid>
    </Layout>
  )
}
