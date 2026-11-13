import { useState } from 'react'
import {
  TextInput,
  NumberInput,
  RadioButtonGroup,
  RadioButton,
  Select,
  SelectItem,
  DatePicker,
  DatePickerInput,
  FileUploader,
  InlineNotification,
  Stack
} from '@carbon/react'
import { ConditionalItemIndicator } from './ConditionalItemIndicator'
import { apiClient } from '../../lib/api-client'
import styles from './ChecklistForm.module.scss'

interface ChecklistFormProps {
  checklist: {
    instance: {
      id: number
      visibility_trace_json: string | null
    }
    items: Array<{
      id: number
      item_key: string
      label: string
      item_type: string
      display_order: number
      is_required: boolean
      evidence_required: boolean
      location_mode: string
      condition_snapshot_json: string | null
    }>
    locations: Array<{
      id: number
      checklist_instance_item_id: number | null
      latitude: number
      longitude: number
      accuracy_meters: number
      captured_at_utc: string
    }>
  }
  onUpdate: () => Promise<void>
  readOnly: boolean
}

interface Answer {
  item_id: number
  value_type: string
  value_text?: string
  value_number?: number
  value_boolean?: boolean
  value_date?: string
  value_json?: string
}

export function ChecklistForm({ checklist, onUpdate, readOnly }: ChecklistFormProps) {
  const [answers, setAnswers] = useState<Record<number, Answer>>({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const visibilityTrace = checklist.instance.visibility_trace_json
    ? JSON.parse(checklist.instance.visibility_trace_json)
    : {}

  const handleAnswerChange = async (itemId: number, answer: Answer) => {
    if (readOnly) return

    setAnswers(prev => ({ ...prev, [itemId]: answer }))
    setSaving(true)
    setError(null)

    try {
      await apiClient.put(`/checklists/${checklist.instance.id}/answers`, {
        answers: [answer]
      })
      await onUpdate()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      }
    } finally {
      setSaving(false)
    }
  }

  const handleFileUpload = async (itemId: number, files: FileList) => {
    if (readOnly || !files.length) return

    const formData = new FormData()
    formData.append('item_id', itemId.toString())
    formData.append('file', files[0])

    try {
      const token = localStorage.getItem('gembaone_access_token')
      const response = await fetch(`/api/v1/checklists/${checklist.instance.id}/attachments`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      await onUpdate()
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      }
    }
  }

  const renderItemInput = (item: typeof checklist.items[0]) => {
    const itemVisibility = visibilityTrace[item.item_key] || { visible: true, required: item.is_required }
    
    if (!itemVisibility.visible) {
      return null
    }

    const hasCondition = item.condition_snapshot_json !== null
    const itemLocation = checklist.locations.find(loc => loc.checklist_instance_item_id === item.id)

    return (
      <div key={item.id} className={styles.fieldMargin}>
        {hasCondition && (
          <ConditionalItemIndicator condition="Shown because condition met" />
        )}

        {item.item_type === 'text' && (
          <TextInput
            id={`item-${item.id}`}
            name={item.item_key}
            labelText={item.label + (item.is_required ? ' (required)' : '')}
            placeholder="Enter text"
            disabled={readOnly}
            invalid={item.is_required && !answers[item.id]}
            invalidText={`${item.label} is required.`}
            onChange={(e) => handleAnswerChange(item.id, {
              item_id: item.id,
              value_type: 'text',
              value_text: e.target.value
            })}
          />
        )}

        {item.item_type === 'number' && (
          <NumberInput
            id={`item-${item.id}`}
            name={item.item_key}
            label={item.label + (item.is_required ? ' (required)' : '')}
            placeholder="Enter number"
            disabled={readOnly}
            invalid={item.is_required && !answers[item.id]}
            invalidText={`${item.label} is required.`}
            onChange={(e) => {
              const input = e.target as HTMLInputElement | undefined
              const value = input?.value || ''
              handleAnswerChange(item.id, {
                item_id: item.id,
                value_type: 'number',
                value_number: value ? parseFloat(value) : undefined
              })
            }}
          />
        )}

        {item.item_type === 'radio' && (
          <RadioButtonGroup
            legendText={item.label + (item.is_required ? ' (required)' : '')}
            name={`item-${item.id}`}
            disabled={readOnly}
            onChange={(value) => handleAnswerChange(item.id, {
              item_id: item.id,
              value_type: 'text',
              value_text: value?.toString() || ''
            })}
          >
            <RadioButton labelText="Yes" value="Yes" id={`item-${item.id}-yes`} />
            <RadioButton labelText="No" value="No" id={`item-${item.id}-no`} />
          </RadioButtonGroup>
        )}

        {item.item_type === 'select' && (
          <Select
            id={`item-${item.id}`}
            name={item.item_key}
            labelText={item.label + (item.is_required ? ' (required)' : '')}
            onChange={(e) => handleAnswerChange(item.id, {
              item_id: item.id,
              value_type: 'text',
              value_text: e.target.value
            })}
          >
            <SelectItem text="Select option" value="" />
            <SelectItem text="Clear" value="Clear" />
            <SelectItem text="Obstructed" value="Obstructed" />
            <SelectItem text="Restricted" value="Restricted" />
          </Select>
        )}

        {item.item_type === 'date' && (
          <DatePicker
            datePickerType="single"
            onChange={(dates) => {
              if (dates[0]) {
                handleAnswerChange(item.id, {
                  item_id: item.id,
                  value_type: 'date',
                  value_date: dates[0].toISOString()
                })
              }
            }}
          >
            <DatePickerInput
              id={`item-${item.id}`}
              labelText={item.label + (item.is_required ? ' (required)' : '')}
              placeholder="mm/dd/yyyy"
              disabled={readOnly}
            />
          </DatePicker>
        )}

        {item.evidence_required && (
          <div className={styles.itemLocation}>
            <FileUploader
              labelTitle={`Upload photo ${item.is_required ? '(required)' : ''}`}
              labelDescription="Images only (.jpg, .png) · up to 10 MB each"
              buttonLabel="Choose photo"
              filenameStatus="edit"
              accept={['.jpg', '.jpeg', '.png']}
              disabled={readOnly}
              onChange={(e) => {
                const input = e.target as HTMLInputElement
                if (input.files) {
                  handleFileUpload(item.id, input.files)
                }
              }}
            />
          </div>
        )}

        {item.location_mode !== 'none' && itemLocation && (
          <div className={styles.itemLocation}>
            <p className="cds--label">Item location captured</p>
            <dl className={styles.locationList}>
              <dt className="cds--label">Latitude</dt>
              <dd className={`${styles.locationLabel} cds--type-mono`}>{itemLocation.latitude.toFixed(4)}</dd>
              <dt className="cds--label">Longitude</dt>
              <dd className={`${styles.locationLabel} cds--type-mono`}>{itemLocation.longitude.toFixed(4)}</dd>
              <dt className="cds--label">Accuracy</dt>
              <dd className={styles.locationLabel}>±{itemLocation.accuracy_meters} m</dd>
            </dl>
          </div>
        )}
      </div>
    )
  }

  // Group items by section (for demo, we'll just render all items)
  return (
    <Stack gap={6}>
      {error && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          lowContrast
        />
      )}

      <fieldset className={styles.fieldset}>
        <legend className={`cds--productive-heading-03 ${styles.legend}`}>
          Checklist Items
        </legend>
        {checklist.items
          .sort((a, b) => a.display_order - b.display_order)
          .map(item => renderItemInput(item))}
      </fieldset>

      {saving && (
        <p className="cds--label" role="status">
          Saving answers…
        </p>
      )}
    </Stack>
  )
}
