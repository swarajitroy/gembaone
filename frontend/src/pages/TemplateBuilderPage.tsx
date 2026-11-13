import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Breadcrumb,
  BreadcrumbItem,
  Button,
  InlineNotification,
  Accordion,
  AccordionItem,
  Tag,
  TextInput,
  TextArea,
  Select,
  SelectItem,
  NumberInput,
  Toggle,
  RadioButtonGroup,
  RadioButton
} from '@carbon/react'
import { Layout } from '../components/layout/Layout'
import type { Template, TemplateItem } from '../types/templates'

export function TemplateBuilderPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [template, setTemplate] = useState<Template | null>(null)
  const [items, setItems] = useState<TemplateItem[]>([])
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [publishSuccess, setPublishSuccess] = useState(false)

  useEffect(() => {
    loadTemplate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  async function loadTemplate() {
    if (!id) return
    
    try {
      setLoading(true)
      // Mock template data - the handoff file doesn't include a GET single template endpoint yet
      // This will be replaced when the backend implements GET /api/v1/checklist-templates/{id}
      const data: Template = {
        id: parseInt(id),
        template_code: 'TPL-SYN-001',
        name: 'SYN Tower Site Survey',
        description: 'Standard tower site survey for SYN operations',
        status: 'active',
        current_version_id: 4,
        created_by_user_id: 1,
        created_at_utc: '2024-01-15T10:00:00Z',
        updated_at_utc: '2024-03-20T14:30:00Z'
      }
      setTemplate(data)
      
      // For now, we'll work with mock items since the full API might not return items
      // In production, this would come from the API
      setItems([
        {
          id: 1,
          template_version_id: data.current_version_id || 0,
          item_key: 'site_access_condition',
          label: 'Site access condition',
          item_type: 'single_select',
          display_order: 1,
          is_required: true,
          evidence_required: false,
          location_mode: 'none',
          options_json: { choices: ['Clear', 'Obstructed'] },
          condition: null,
          created_at_utc: new Date().toISOString()
        },
        {
          id: 2,
          template_version_id: data.current_version_id || 0,
          item_key: 'describe_obstruction',
          label: 'Describe obstruction',
          item_type: 'text',
          display_order: 2,
          is_required: true,
          evidence_required: true,
          location_mode: 'none',
          options_json: null,
          condition: {
            id: 1,
            template_item_id: 2,
            source_item_key: 'site_access_condition',
            operator: 'equals',
            expected_value: 'Obstructed',
            created_at_utc: new Date().toISOString()
          },
          created_at_utc: new Date().toISOString()
        }
      ])
      
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load template')
    } finally {
      setLoading(false)
    }
  }

  function validateItems(): string[] {
    const errors: string[] = []
    const itemsByKey = new Map(items.map(item => [item.item_key, item]))
    
    items.forEach(item => {
      if (item.condition) {
        const sourceItem = itemsByKey.get(item.condition.source_item_key)
        if (!sourceItem) {
          errors.push(`Item "${item.label}": Source item "${item.condition.source_item_key}" not found`)
        } else if (sourceItem.display_order >= item.display_order) {
          errors.push(`Item "${item.label}": Source item must appear before this item`)
        }
      }
    })
    
    return errors
  }

  async function handlePublish() {
    const errors = validateItems()
    setValidationErrors(errors)
    
    if (errors.length > 0) {
      return
    }
    
    try {
      setPublishing(true)
      
      // Mock publish action - simulate API call delay
      // In production, this would call: POST /api/v1/checklist-templates/{id}/versions
      await new Promise(resolve => setTimeout(resolve, 500))
      
      setPublishSuccess(true)
      setValidationErrors([])
      setTimeout(() => setPublishSuccess(false), 5000)
      
      // Refresh template data
      await loadTemplate()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish version')
    } finally {
      setPublishing(false)
    }
  }

  function handleRetire() {
    navigate('/')
  }

  function handleCancel() {
    navigate('/')
  }

  if (loading) {
    return (
      <Layout>
        <div className="p-8">Loading...</div>
      </Layout>
    )
  }

  if (!template) {
    return (
      <Layout>
        <div className="p-8">Template not found</div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="p-8 max-w-7xl mx-auto">
        <Breadcrumb noTrailingSlash className="mb-4">
          <BreadcrumbItem>
            <a href="/">Home</a>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <a href="/templates">Checklist templates</a>
          </BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>
            {template.name}
          </BreadcrumbItem>
        </Breadcrumb>

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-normal">{template.name}</h1>
            <Tag type="cyan">Draft of v4</Tag>
            <Tag type="green">Active: v3</Tag>
          </div>
          <div className="flex gap-2">
            <Button kind="ghost" onClick={handleCancel}>
              Cancel
            </Button>
            <Button kind="secondary" onClick={handleRetire}>
              Retire template
            </Button>
            <Button kind="primary" onClick={handlePublish} disabled={publishing}>
              Publish new version
            </Button>
          </div>
        </div>

        {error && (
          <InlineNotification
            kind="error"
            title="Error"
            subtitle={error}
            lowContrast
            className="mb-4"
          />
        )}

        <InlineNotification
          kind="info"
          title="Versions are immutable."
          subtitle="Published versions cannot be changed. Publishing creates a new version; existing checklists keep the version they started from. Templates cannot be deleted."
          lowContrast
          hideCloseButton
          className="mb-4"
        />

        {validationErrors.length > 0 && (
          <InlineNotification
            kind="error"
            title={`${validationErrors.length} problem${validationErrors.length > 1 ? 's' : ''} must be fixed before publishing`}
            subtitle={validationErrors.join(' | ')}
            lowContrast
            hideCloseButton
            className="mb-4"
          />
        )}

        {publishSuccess && (
          <InlineNotification
            kind="success"
            title="Version v4 published."
            subtitle="Correlation ID: corr-7a41c0e9 · recorded in the audit trail"
            lowContrast
            className="mb-4"
          />
        )}

        <div className="grid grid-cols-12 gap-8">
          <div className="col-span-8">
            <section className="bg-gray-100 p-6 mb-6">
              <h2 className="text-xl font-normal mb-4">Template details</h2>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <TextInput
                    id="template-name"
                    labelText="Template name (required)"
                    value={template.name}
                    readOnly
                    helperText="Shown to field engineers when they pick a template."
                  />
                </div>
                <div>
                  <TextInput
                    id="template-code"
                    labelText="Template code"
                    value={template.template_code}
                    readOnly
                    helperText="Assigned on creation. Read-only."
                  />
                </div>
              </div>

              <TextArea
                id="template-description"
                labelText="Description (optional)"
                value={template.description || ''}
                readOnly
                rows={3}
              />
            </section>

            <section className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-normal">Items</h2>
                <div className="flex gap-2">
                  <Button kind="secondary" size="sm">
                    Expand all
                  </Button>
                  <Button kind="ghost" size="sm">
                    Collapse all
                  </Button>
                  <Button kind="primary" size="sm">
                    Add item
                  </Button>
                </div>
              </div>

              <Accordion>
                {items.map((item) => (
                  <AccordionItem
                    key={item.id}
                    title={
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{item.display_order}. {item.label}</span>
                        <Tag type="gray" size="sm">{item.item_type}</Tag>
                        {item.is_required && <Tag type="blue" size="sm">Required</Tag>}
                        {item.evidence_required && <Tag type="purple" size="sm">Photo evidence</Tag>}
                        {item.condition && <Tag type="cyan" size="sm">Conditional</Tag>}
                      </div>
                    }
                  >
                    <div className="p-4">
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <TextInput
                          id={`item-key-${item.id}`}
                          labelText="Item key"
                          value={item.item_key}
                          readOnly
                        />
                        <TextInput
                          id={`item-label-${item.id}`}
                          labelText="Label (required)"
                          value={item.label}
                          readOnly
                        />
                        <Select
                          id={`item-type-${item.id}`}
                          labelText="Item type"
                          value={item.item_type}
                          disabled
                        >
                          <SelectItem value="text" text="text" />
                          <SelectItem value="number" text="number" />
                          <SelectItem value="boolean" text="boolean" />
                          <SelectItem value="date" text="date" />
                          <SelectItem value="single_select" text="single_select" />
                          <SelectItem value="multi_select" text="multi_select" />
                          <SelectItem value="file" text="file" />
                        </Select>
                      </div>

                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <NumberInput
                          id={`display-order-${item.id}`}
                          label="Display order"
                          value={item.display_order}
                          readOnly
                        />
                        <div>
                          <label className="block text-xs mb-2">Required</label>
                          <Toggle
                            id={`required-${item.id}`}
                            labelText={item.is_required ? 'On' : 'Off'}
                            toggled={item.is_required}
                            disabled
                            size="sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs mb-2">Options</label>
                          <div className="flex gap-2 flex-wrap">
                            {item.options_json?.choices?.map((choice, i) => (
                              <Tag key={i} type="gray" size="sm">{choice}</Tag>
                            ))}
                          </div>
                        </div>
                      </div>

                      <fieldset className="border border-gray-300 p-4 mb-4">
                        <legend className="text-xs px-2">Evidence and location</legend>
                        <div className="mb-2">
                          <Toggle
                            id={`evidence-${item.id}`}
                            labelText="Evidence required (photo or file)"
                            toggled={item.evidence_required}
                            disabled
                            size="sm"
                          />
                        </div>
                        <RadioButtonGroup
                          name={`location-mode-${item.id}`}
                          legendText="Location mode"
                          valueSelected={item.location_mode}
                        >
                          <RadioButton id={`location-none-${item.id}`} labelText="None" value="none" disabled />
                          <RadioButton id={`location-optional-${item.id}`} labelText="Optional" value="optional" disabled />
                          <RadioButton id={`location-required-${item.id}`} labelText="Required" value="required" disabled />
                        </RadioButtonGroup>
                      </fieldset>

                      {item.condition ? (
                        <fieldset className="border border-gray-300 p-4 mb-4">
                          <legend className="text-xs px-2">Show this item only when…</legend>
                          <div className="grid grid-cols-3 gap-4">
                            <Select
                              id={`condition-source-${item.id}`}
                              labelText="Source item"
                              value={item.condition.source_item_key}
                              disabled
                            >
                              <SelectItem value={item.condition.source_item_key} text={item.condition.source_item_key} />
                            </Select>
                            <Select
                              id={`condition-operator-${item.id}`}
                              labelText="Operator"
                              value={item.condition.operator}
                              disabled
                            >
                              <SelectItem value="equals" text="equals" />
                              <SelectItem value="not_equals" text="not_equals" />
                              <SelectItem value="contains" text="contains" />
                              <SelectItem value="greater_than" text="greater_than" />
                              <SelectItem value="less_than" text="less_than" />
                            </Select>
                            <TextInput
                              id={`condition-value-${item.id}`}
                              labelText="Expected value"
                              value={item.condition.expected_value}
                              readOnly
                            />
                          </div>
                        </fieldset>
                      ) : (
                        <fieldset className="border border-gray-300 p-4 mb-4">
                          <legend className="text-xs px-2">Show this item only when…</legend>
                          <p className="text-sm text-gray-600">No condition. This item is always shown.</p>
                        </fieldset>
                      )}
                    </div>
                  </AccordionItem>
                ))}
              </Accordion>

              <p className="text-xs text-gray-600 mt-2">
                Showing items 1–{items.length} of {items.length}
              </p>
            </section>

            <div className="flex gap-2 mt-6">
              <Button kind="ghost" onClick={handleCancel}>
                Cancel
              </Button>
              <Button kind="primary" onClick={handlePublish} disabled={publishing}>
                Publish new version
              </Button>
            </div>

            <p className="text-xs text-gray-600 mt-2">
              Draft saving is not available in this release. Fix the problem above, then publish.
            </p>
          </div>

          <aside className="col-span-4">
            <section className="bg-gray-100 p-6">
              <h2 className="text-lg font-normal mb-4">Version history</h2>
              
              <dl className="space-y-4">
                <div className="border-t border-gray-300 pt-4">
                  <dt className="font-semibold">Draft v4</dt>
                  <dd className="text-sm text-gray-600 mt-1">
                    <Tag type="cyan" size="sm" className="mb-1">Pending</Tag>
                    <br />
                    Not published
                  </dd>
                </div>

                <div className="border-t border-gray-300 pt-4">
                  <dt className="font-semibold">v3</dt>
                  <dd className="text-sm text-gray-600 mt-1">
                    <Tag type="green" size="sm" className="mb-1">Active</Tag>
                    <br />
                    Published by SYN-USR-001
                    <br />
                    <span className="font-mono text-xs">10 Nov 2026 14:02</span>
                  </dd>
                </div>

                <div className="border-t border-gray-300 pt-4">
                  <dt className="font-semibold">v2</dt>
                  <dd className="text-sm text-gray-600 mt-1">
                    <Tag type="gray" size="sm" className="mb-1">Superseded</Tag>
                    <br />
                    Published by SYN-USR-001
                    <br />
                    <span className="font-mono text-xs">28 Oct 2026 09:47</span>
                  </dd>
                </div>

                <div className="border-t border-gray-300 pt-4">
                  <dt className="font-semibold">v1</dt>
                  <dd className="text-sm text-gray-600 mt-1">
                    <Tag type="gray" size="sm" className="mb-1">Superseded</Tag>
                    <br />
                    Published by SYN-USR-001
                    <br />
                    <span className="font-mono text-xs">14 Oct 2026 16:20</span>
                  </dd>
                </div>
              </dl>

              <p className="text-xs text-gray-600 mt-4">
                History is read-only. Versions cannot be restored or deleted.
              </p>
            </section>
          </aside>
        </div>
      </div>
    </Layout>
  )
}
