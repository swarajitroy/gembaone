import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Breadcrumb,
  BreadcrumbItem,
  Button,
  InlineNotification,
  Tag,
  Grid,
  Column,
  Stack,
} from '@carbon/react'
import { Checkmark } from '@carbon/icons-react'
import { apiClient } from '../lib/api-client'
import type {
  MappingDefinition,
  MappingEntryRequest,
  PublishMappingVersionRequest,
} from '../types/mappings'
import MappingDetailsForm from '../components/mappings/MappingDetailsForm'
import MappingEntriesTable from '../components/mappings/MappingEntriesTable'
import { Layout } from '../components/layout/Layout'
import styles from './MappingEditorPage.module.scss'

export default function MappingEditorPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [mapping, setMapping] = useState<MappingDefinition | null>(null)
  const [sourceEntity, setSourceEntity] = useState('')
  const [targetEntity, setTargetEntity] = useState('')
  const [draftEntries, setDraftEntries] = useState<MappingEntryRequest[]>([])
  const [publishSuccess, setPublishSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    loadMapping()
  }, [id])

  const loadMapping = async () => {
    try {
      setLoading(true)
      setErrorMessage(null)
      const response = await apiClient.get<{ items: MappingDefinition[] }>(
        '/mappings'
      )
      const foundMapping = response.items.find((m) => m.id === Number(id))
      if (foundMapping) {
        setMapping(foundMapping)
        setSourceEntity(foundMapping.source_entity)
        setTargetEntity(foundMapping.target_entity)
        // Initialize draft entries with current active version entries
        setDraftEntries(
          foundMapping.current_version.entries.map((e) => ({
            source_column: e.source_column,
            target_field: e.target_field,
            target_type: e.target_type,
            is_required: e.is_required,
            transform_expression: e.transform_expression,
          }))
        )
      }
    } catch (error) {
      console.error('Failed to load mapping:', error)
      setErrorMessage('Failed to load mapping')
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async () => {
    if (!mapping) return

    try {
      setErrorMessage(null)
      const nextVersion = mapping.current_version.version_number + 1
      const request: PublishMappingVersionRequest = {
        version_label: `v${nextVersion}.0`,
        entries: draftEntries,
      }

      await apiClient.post(`/mappings/${mapping.id}/versions`, request)
      setPublishSuccess(true)
      // Reload to get updated mapping
      await loadMapping()
    } catch (error) {
      console.error('Failed to publish version:', error)
      setErrorMessage(
        error instanceof Error ? error.message : 'Failed to publish version'
      )
    }
  }

  const checkPublishAvailable = () => {
    // Check if all required target fields are mapped
    const hasEmptySourceColumn = draftEntries.some(
      (e) => !e.source_column || !e.target_field
    )
    const hasAtLeastOneEntry = draftEntries.length > 0
    return hasAtLeastOneEntry && !hasEmptySourceColumn
  }

  const findMissingRequiredFields = () => {
    // For demo: assume region_code is required but not mapped
    const mappedTargetFields = draftEntries.map((e) => e.target_field)
    const requiredFields = [
      'site_id',
      'site_name',
      'latitude',
      'longitude',
      'region_code',
    ]
    return requiredFields.filter((f) => !mappedTargetFields.includes(f))
  }

  if (loading) {
    return <div className={styles.container}>Loading...</div>
  }

  if (!mapping) {
    return <div className={styles.container}>Mapping not found</div>
  }

  const publishAvailable = checkPublishAvailable()
  const missingFields = findMissingRequiredFields()
  const hasMissingRequired = missingFields.length > 0

  return (
    <Layout>
      <div className={styles.container}>
      <Breadcrumb noTrailingSlash>
        <BreadcrumbItem href="/">Home</BreadcrumbItem>
        <BreadcrumbItem href="/mappings">Mappings</BreadcrumbItem>
        <BreadcrumbItem isCurrentPage>
          {mapping.source_entity}
        </BreadcrumbItem>
      </Breadcrumb>

      <div className={styles.pageHead}>
        <div className={styles.pageHeadLeft}>
          <h1>{mapping.source_entity} mapping</h1>
          <Tag type="green" renderIcon={Checkmark}>
            Active: v{mapping.current_version.version_number}
          </Tag>
          <Tag type="cyan">
            Draft of v{mapping.current_version.version_number + 1}
          </Tag>
        </div>
        <div className={styles.pageHeadRight}>
          <Button kind="ghost" onClick={() => navigate('/')}>
            Cancel
          </Button>
          <Button
            kind="primary"
            disabled={!publishAvailable || hasMissingRequired}
            onClick={handlePublish}
          >
            Publish new version
          </Button>
        </div>
      </div>

      {!publishAvailable || hasMissingRequired ? (
        <p className={styles.helperText}>
          Publish is unavailable until all required target fields are mapped.
        </p>
      ) : null}

      <InlineNotification
        kind="info"
        title="Versions are immutable."
        subtitle="Mapping versions are immutable once published. Uploads record the mapping version they used. Mappings cannot be deleted."
        lowContrast
        hideCloseButton
      />

      {errorMessage && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={errorMessage}
          lowContrast
          onClose={() => setErrorMessage(null)}
        />
      )}

      <Grid fullWidth narrow>
        <Column lg={12} md={8} sm={4}>
          <section className={styles.tile}>
            <h2>Mapping details</h2>
            <MappingDetailsForm
              mappingCode={mapping.mapping_code}
              sourceEntity={sourceEntity}
              targetEntity={targetEntity}
              onSourceEntityChange={setSourceEntity}
              onTargetEntityChange={setTargetEntity}
            />
          </section>

          {hasMissingRequired && (
            <InlineNotification
              kind="warning"
              title={`${missingFields.length} required target field${missingFields.length > 1 ? 's are' : ' is'} not mapped`}
              subtitle={`${missingFields.join(', ')} ${missingFields.length > 1 ? 'are' : 'is'} not mapped. Map ${missingFields.length > 1 ? 'them' : 'it'} before publishing.`}
              lowContrast
              hideCloseButton
            />
          )}

          <section>
            <h2>Mapping entries</h2>
            <MappingEntriesTable
              entries={draftEntries}
              onEntriesChange={setDraftEntries}
            />
          </section>

          {publishSuccess && (
            <InlineNotification
              kind="success"
              title="State example after publishing"
              subtitle={`Mapping version v${mapping.current_version.version_number}.0 published. Correlation ID: corr-52c0e8b4 · recorded in the audit trail`}
              lowContrast
              onClose={() => setPublishSuccess(false)}
            />
          )}

          <p className={styles.noteText}>
            Mapping suggestions are not available in this release. Validation
            outcomes are produced by deterministic rules. No AI is used in this
            release; people remain accountable for decisions.
          </p>
        </Column>

        <Column lg={4} md={8} sm={4}>
          <aside className={styles.tile}>
            <h2>Version history</h2>
            <Stack gap={4}>
              <div className={styles.versionRow}>
                <dt>v{mapping.current_version.version_number + 1}</dt>
                <dd>
                  <Tag type="cyan">Draft</Tag>
                  <br />
                  Not published
                </dd>
              </div>
              <div className={styles.versionRow}>
                <dt>v{mapping.current_version.version_number}</dt>
                <dd>
                  <Tag type="green" renderIcon={Checkmark}>
                    Active
                  </Tag>
                  <br />
                  Published by SYN-USR-001
                  <br />
                  <code className={styles.monoCode}>05 Nov 2026 13:18</code>
                </dd>
              </div>
              {mapping.current_version.version_number > 1 && (
                <div className={styles.versionRow}>
                  <dt>v1</dt>
                  <dd>
                    <Tag type="gray">Superseded</Tag>
                    <br />
                    Published by SYN-USR-001
                    <br />
                    <code className={styles.monoCode}>22 Oct 2026 10:41</code>
                  </dd>
                </div>
              )}
            </Stack>
            <p className={styles.noteTextWithMargin}>
              History is read-only. Versions cannot be restored or deleted.
            </p>
          </aside>
        </Column>
      </Grid>
    </div>
    </Layout>
  )
}
