import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Layout } from '../components/layout/Layout'
import { 
  Breadcrumb, 
  BreadcrumbItem, 
  Tag,
  InlineNotification,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Grid,
  Column,
  Stack
} from '@carbon/react'
import { apiClient } from '../lib/api-client'
import { EvidenceGallery } from '../components/checklists/EvidenceGallery'
import styles from './ChecklistReviewPage.module.scss'

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

interface Answer {
  id: number
  checklist_instance_item_id: number
  value_type: string
  value_text: string | null
  value_number: number | null
  value_boolean: boolean | null
  value_date: string | null
  value_json: string | null
}

interface Attachment {
  id: number
  file_object_id: number
  original_filename: string
  content_type: string
  byte_size: number
  uploaded_by_user_id: number
  uploaded_at_utc: string
}

export function ChecklistReviewPage() {
  const { id } = useParams<{ id: string }>()
  const [checklist, setChecklist] = useState<ChecklistDetail | null>(null)
  const [answers, setAnswers] = useState<Answer[]>([])
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
      
      // Mock answers for demo - in real implementation, these would come from the backend
      setAnswers([])
      setAttachments([])
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

  const isSubmitted = checklist.instance.status === 'submitted'
  const visibilityTrace = checklist.instance.visibility_trace_json 
    ? JSON.parse(checklist.instance.visibility_trace_json) 
    : {}

  return (
    <Layout>
      <Stack gap={6}>
        <Breadcrumb noTrailingSlash>
          <BreadcrumbItem href="/">Home</BreadcrumbItem>
          <BreadcrumbItem href="/checklists">Checklists</BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>{checklist.instance.title}</BreadcrumbItem>
        </Breadcrumb>

        <div className={styles.pageHead}>
          <h1 className="cds--productive-heading-05">
            Review: {checklist.instance.title}
          </h1>
          {isSubmitted && <Tag type="green">Submitted</Tag>}
          <Tag type="blue">Template {checklist.template_version.version_label}</Tag>
          <Tag type="gray">Read-only</Tag>
        </div>

        <InlineNotification
          kind="info"
          title="This record is read-only"
          subtitle="Reviewers can view but not change or delete submissions. All answers, photos and locations in this demo are synthetic."
          lowContrast
        />

        <Grid>
          <Column lg={10} md={8} sm={4}>
            <Tabs>
              <TabList aria-label="Checklist record sections" contained>
                <Tab>Answers</Tab>
                <Tab>Evidence</Tab>
                <Tab>Locations</Tab>
              </TabList>
              <TabPanels>
                <TabPanel>
                  <Stack gap={5} className={styles.tabContent}>
                    <h2 className="cds--productive-heading-03">Answers</h2>
                    
                    <div role="list">
                      {checklist.items.map(item => {
                        const itemVisibility = visibilityTrace[item.item_key] || { visible: true, has_condition: false }
                        const answer = answers.find(a => a.checklist_instance_item_id === item.id)
                        
                        return (
                          <div 
                            key={item.id} 
                            role="listitem"
                            className={styles.answerItem}
                          >
                            <div>
                              <div className="cds--label-01">
                                {item.label}
                              </div>
                              <span className={`cds--label ${styles.answerLabel}`}>
                                {item.item_key}
                              </span>
                              {itemVisibility.has_condition && (
                                <>
                                  <div className={styles.answerTags}>
                                    <Tag type="cyan">Conditional</Tag>
                                  </div>
                                  <span className={`cds--label ${styles.answerWhy}`}>
                                    Shown because of condition
                                  </span>
                                </>
                              )}
                            </div>
                            <div>
                              {answer ? (
                                <span>
                                  {answer.value_text || 
                                   answer.value_number?.toString() || 
                                   answer.value_boolean?.toString() || 
                                   answer.value_date || 
                                   'N/A'}
                                </span>
                              ) : (
                                <span className={`cds--label ${styles.answerLabel}`}>
                                  Not answered
                                </span>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </Stack>
                </TabPanel>

                <TabPanel>
                  <Stack gap={5} className={styles.tabContent}>
                    <h2 className="cds--productive-heading-03">Evidence</h2>
                    <EvidenceGallery attachments={attachments} />
                  </Stack>
                </TabPanel>

                <TabPanel>
                  <Stack gap={5} className={styles.tabContent}>
                    <h2 className="cds--productive-heading-03">
                      Locations <Tag type="red">Sensitive data</Tag>
                    </h2>
                    
                    <div className={styles.tableWrap}>
                      <table className="cds--data-table">
                        <thead>
                          <tr>
                            <th>Level</th>
                            <th>Item</th>
                            <th>Latitude</th>
                            <th>Longitude</th>
                            <th>Accuracy</th>
                            <th>Captured at</th>
                          </tr>
                        </thead>
                        <tbody>
                          {checklist.locations.map(loc => (
                            <tr key={loc.id}>
                              <td>{loc.checklist_instance_item_id === null ? 'Checklist' : 'Item'}</td>
                              <td>
                                {loc.checklist_instance_item_id === null 
                                  ? 'Whole checklist' 
                                  : checklist.items.find(i => i.id === loc.checklist_instance_item_id)?.label || 'Unknown'}
                              </td>
                              <td className="cds--type-mono">{loc.latitude.toFixed(4)}</td>
                              <td className="cds--type-mono">{loc.longitude.toFixed(4)}</td>
                              <td>±{loc.accuracy_meters} m</td>
                              <td>{new Date(loc.captured_at_utc).toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Stack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </Column>

          <Column lg={6} md={8} sm={4}>
            <Stack gap={5}>
              <div className={`cds--tile ${styles.tile}`}>
                <h2 className={`cds--productive-heading-03 ${styles.tileHeading}`}>
                  Submission metadata
                </h2>
                <dl className={styles.metadataList}>
                  <dt className="cds--label">Checklist ID</dt>
                  <dd className={`${styles.metadataLabel} cds--type-mono`}>{checklist.instance.title}</dd>
                  
                  <dt className="cds--label">Template</dt>
                  <dd className={styles.metadataLabel}>{checklist.instance.title.split(' - ')[0]}</dd>
                  
                  <dt className="cds--label">Template version</dt>
                  <dd className={styles.metadataLabel}>{checklist.template_version.version_label}</dd>
                  
                  <dt className="cds--label">Created at</dt>
                  <dd className={styles.metadataLabel}>{new Date(checklist.instance.created_at_utc).toLocaleString()}</dd>
                  
                  {checklist.instance.submitted_at_utc && (
                    <>
                      <dt className="cds--label">Submitted at</dt>
                      <dd className={styles.metadataLabel}>{new Date(checklist.instance.submitted_at_utc).toLocaleString()}</dd>
                    </>
                  )}
                  
                  <dt className="cds--label">Status</dt>
                  <dd className={styles.metadataLabel}>
                    {isSubmitted ? 'Submitted' : 'In progress'}
                  </dd>
                </dl>
              </div>

              <div className={`cds--tile ${styles.tile}`}>
                <h2 className={`cds--productive-heading-03 ${styles.tileHeading}`}>
                  What your role can see
                </h2>
                <p className="cds--body-01">
                  Answers, evidence and locations of submitted checklists. You cannot edit, approve, reject or delete.
                </p>
                <p className={`cds--label cds--label-01 ${styles.roleNote}`}>
                  Views of this record are recorded in the audit trail.
                </p>
              </div>
            </Stack>
          </Column>
        </Grid>
      </Stack>
    </Layout>
  )
}
