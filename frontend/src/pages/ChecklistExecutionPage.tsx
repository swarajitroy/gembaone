import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Layout } from '../components/layout/Layout'
import { 
  Breadcrumb, 
  BreadcrumbItem, 
  Button, 
  Tag,
  InlineNotification,
  Grid,
  Column,
  Stack
} from '@carbon/react'
import { apiClient } from '../lib/api-client'
import { ChecklistForm } from '../components/checklists/ChecklistForm'
import { LocationDisplay } from '../components/checklists/LocationDisplay'
import styles from './ChecklistExecutionPage.module.scss'

interface ChecklistInstance {
  id: number
  template_version_id: number
  title: string
  status: string
  visibility_trace_json: string | null
  created_by_user_id: number
  created_at_utc: string
  submitted_by_user_id: number | null
  submitted_at_utc: string | null
}

interface ChecklistItem {
  id: number
  checklist_instance_id: number
  template_item_id: number
  item_key: string
  label: string
  item_type: string
  display_order: number
  is_required: boolean
  evidence_required: boolean
  location_mode: string
  condition_snapshot_json: string | null
}

interface ChecklistLocation {
  id: number
  checklist_instance_id: number
  checklist_instance_item_id: number | null
  latitude: number
  longitude: number
  accuracy_meters: number
  captured_by_user_id: number
  captured_at_utc: string
}

interface TemplateVersion {
  id: number
  template_id: number
  version_number: number
  version_label: string
  status: string
}

interface ChecklistDetail {
  instance: ChecklistInstance
  items: ChecklistItem[]
  locations: ChecklistLocation[]
  template_version: TemplateVersion
}

interface SubmissionResponse {
  status: string
  submitted_by: number
  submitted_at: string
  validation_issues: ValidationIssue[]
}

interface ValidationIssue {
  item_id: number
  code: string
  message: string
  severity: string
}

export function ChecklistExecutionPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [checklist, setChecklist] = useState<ChecklistDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([])

  useEffect(() => {
    loadChecklist()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const loadChecklist = async () => {
    if (!id) return
    
    setLoading(true)
    setError(null)
    
    try {
      const data = await apiClient.get<ChecklistDetail>(`/checklists/${id}`)
      setChecklist(data)
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to load checklist')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!id || !checklist) return
    
    setSubmitting(true)
    setValidationIssues([])
    
    try {
      const response = await apiClient.post<SubmissionResponse>(`/checklists/${id}/submit`)
      
      if (response.validation_issues && response.validation_issues.length > 0) {
        setValidationIssues(response.validation_issues)
      } else {
        // Success - reload checklist to show submitted state
        await loadChecklist()
      }
    } catch (err: unknown) {
      if (err instanceof Error && 'status' in err && 'detail' in err) {
        const apiError = err as unknown as { status: number; detail: string | { validation_issues?: ValidationIssue[] } }
        if (apiError.status === 400 && typeof apiError.detail === 'object') {
          setValidationIssues(apiError.detail.validation_issues || [])
        } else {
          setError(typeof apiError.detail === 'string' ? apiError.detail : 'Submission failed')
        }
      } else {
        setError('Submission failed')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleBackToHome = () => {
    navigate('/')
  }

  if (loading) {
    return (
      <Layout>
        <p className="cds--body-01">Loading checklist...</p>
      </Layout>
    )
  }

  if (error || !checklist) {
    return (
      <Layout>
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error || 'Checklist not found'}
          lowContrast
        />
      </Layout>
    )
  }

  const instanceLocation = checklist.locations.find(loc => loc.checklist_instance_item_id === null)
  const isSubmitted = checklist.instance.status === 'submitted'

  return (
    <Layout>
      <Stack gap={6}>
        <Breadcrumb noTrailingSlash>
          <BreadcrumbItem href="/">Home</BreadcrumbItem>
          <BreadcrumbItem href="/checklists">Checklists</BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>{checklist.instance.title}</BreadcrumbItem>
        </Breadcrumb>

        <div className="cds--grid">
          <div className="cds--row">
            <div className="cds--col">
              <Stack gap={3}>
                <div className={styles.headingGroup}>
                  <h1 className="cds--productive-heading-05">
                    {checklist.instance.title}
                  </h1>
                  <Tag type="blue">Template {checklist.template_version.version_label}</Tag>
                  <Tag type={isSubmitted ? 'green' : 'cyan'}>
                    {isSubmitted ? 'Submitted' : 'In progress'}
                  </Tag>
                </div>
                
                {!isSubmitted && (
                  <Button onClick={handleSubmit} disabled={submitting}>
                    Submit checklist
                  </Button>
                )}
              </Stack>
            </div>
          </div>
        </div>

        <InlineNotification
          kind="info"
          title="Sensitive data"
          subtitle="Photos and locations are sensitive; only authorised roles can view them. All photos, locations and answers in this demo are synthetic."
          lowContrast
        />

        {validationIssues.length > 0 && (
          <InlineNotification
            kind="error"
            title="Submission is blocked"
            subtitle="Fix these items, then submit again"
            lowContrast
          >
            <div>
              <ul className={styles.validationList}>
                {validationIssues.map((issue, idx) => (
                  <li key={idx}>{issue.message}</li>
                ))}
              </ul>
            </div>
          </InlineNotification>
        )}

        {isSubmitted && (
          <InlineNotification
            kind="success"
            title="Checklist submitted"
            subtitle="It is now read-only."
            lowContrast
          />
        )}

        <Grid>
          <Column lg={10} md={8} sm={4}>
            <ChecklistForm
              checklist={checklist}
              onUpdate={loadChecklist}
              readOnly={isSubmitted}
            />

            <Stack gap={3} className={styles.actions}>
              <Button onClick={handleSubmit} disabled={submitting || isSubmitted}>
                Submit checklist
              </Button>
              <Button kind="ghost" onClick={handleBackToHome}>
                Back to Home
              </Button>
            </Stack>
          </Column>

          <Column lg={6} md={8} sm={4}>
            <Stack gap={5}>
              <div className={`cds--tile ${styles.tile}`}>
                <h2 className={`cds--productive-heading-03 ${styles.tileHeading}`}>
                  Checklist location
                </h2>
                <LocationDisplay
                  location={instanceLocation || null}
                  onCapture={async () => {
                    if (!id) return
                    
                    try {
                      // Get current position from browser
                      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                          enableHighAccuracy: true,
                          timeout: 10000,
                          maximumAge: 0
                        })
                      })
                      
                      // Send to API
                      await apiClient.put(`/checklists/${id}/location`, {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy_meters: position.coords.accuracy || 0
                      })
                      
                      // Reload to show captured location
                      await loadChecklist()
                    } catch (err) {
                      if (err instanceof Error) {
                        setError(`Failed to capture location: ${err.message}`)
                      } else {
                        setError('Failed to capture location')
                      }
                    }
                  }}
                  readOnly={isSubmitted}
                />
              </div>

              <div className={`cds--tile ${styles.tile}`}>
                <h2 className={`cds--productive-heading-03 ${styles.tileHeading}`}>
                  This checklist
                </h2>
                <dl className={styles.metadataList}>
                  <dt className="cds--label">Checklist ID</dt>
                  <dd className={styles.metadataLabel}>{checklist.instance.title}</dd>
                  
                  <dt className="cds--label">Template</dt>
                  <dd className={styles.metadataLabel}>
                    {checklist.instance.title.split(' - ')[0]} {checklist.template_version.version_label}
                  </dd>
                  
                  <dt className="cds--label">Status</dt>
                  <dd className={styles.metadataLabel}>
                    {isSubmitted ? 'Submitted' : 'In progress'}
                  </dd>
                </dl>
              </div>
            </Stack>
          </Column>
        </Grid>
      </Stack>
    </Layout>
  )
}
