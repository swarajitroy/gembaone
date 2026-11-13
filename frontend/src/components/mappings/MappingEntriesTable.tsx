import { useState } from 'react'
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TextInput,
  Select,
  SelectItem,
  Checkbox,
  Button,
} from '@carbon/react'
import { Add, ArrowUp, ArrowDown } from '@carbon/icons-react'
import type { MappingEntryRequest } from '../../types/mappings'
import styles from './MappingEntriesTable.module.scss'

interface MappingEntriesTableProps {
  entries: MappingEntryRequest[]
  onEntriesChange: (entries: MappingEntryRequest[]) => void
}

const TARGET_TYPE_OPTIONS = [
  { value: 'string', label: 'text' },
  { value: 'number', label: 'number' },
  { value: 'date', label: 'date' },
  { value: 'boolean', label: 'boolean' },
]

export default function MappingEntriesTable({
  entries,
  onEntriesChange,
}: MappingEntriesTableProps) {
  const [newEntry, setNewEntry] = useState<MappingEntryRequest>({
    source_column: '',
    target_field: '',
    target_type: 'string',
    is_required: false,
  })

  const handleEntryChange = (
    index: number,
    field: keyof MappingEntryRequest,
    value: string | boolean
  ) => {
    const updated = [...entries]
    updated[index] = { ...updated[index], [field]: value }
    onEntriesChange(updated)
  }

  const handleMoveUp = (index: number) => {
    if (index === 0) return
    const updated = [...entries]
    ;[updated[index - 1], updated[index]] = [updated[index], updated[index - 1]]
    onEntriesChange(updated)
  }

  const handleMoveDown = (index: number) => {
    if (index === entries.length - 1) return
    const updated = [...entries]
    ;[updated[index], updated[index + 1]] = [updated[index + 1], updated[index]]
    onEntriesChange(updated)
  }

  const handleAddEntry = () => {
    if (!newEntry.source_column || !newEntry.target_field) return
    onEntriesChange([...entries, newEntry])
    setNewEntry({
      source_column: '',
      target_field: '',
      target_type: 'string',
      is_required: false,
    })
  }

  const headers = [
    { key: 'source_column', header: 'Source column' },
    { key: 'target_field', header: 'Target field' },
    { key: 'target_type', header: 'Target type' },
    { key: 'is_required', header: 'Required' },
    { key: 'order', header: 'Order' },
  ]

  const rows = entries.map((entry, index) => ({
    id: String(index),
    ...entry,
  }))

  return (
    <div className={styles.tableContainer}>
      <div className={styles.toolbar}>
        <span className={styles.toolbarTitle}>Source column to target field</span>
        <span className={styles.toolbarNote}>{entries.length} entries</span>
      </div>
      <DataTable rows={rows} headers={headers}>
        {({ headers: tableHeaders, getHeaderProps, getTableProps }) => (
          <Table {...getTableProps()} aria-label="Mapping entries table">
            <TableHead>
              <TableRow>
                {tableHeaders.map((header) => (
                  <TableHeader {...getHeaderProps({ header })} key={header.key}>
                    {header.header}
                  </TableHeader>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {entries.map((entry, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <TextInput
                      id={`source-column-${index}`}
                      labelText=""
                      hideLabel
                      value={entry.source_column}
                      onChange={(e) =>
                        handleEntryChange(index, 'source_column', e.target.value)
                      }
                      size="sm"
                      className={styles.cellInput}
                    />
                  </TableCell>
                  <TableCell>
                    <TextInput
                      id={`target-field-${index}`}
                      labelText=""
                      hideLabel
                      value={entry.target_field}
                      onChange={(e) =>
                        handleEntryChange(index, 'target_field', e.target.value)
                      }
                      size="sm"
                      className={styles.cellInputMono}
                    />
                  </TableCell>
                  <TableCell>
                    <Select
                      id={`target-type-${index}`}
                      labelText=""
                      hideLabel
                      value={entry.target_type}
                      onChange={(e) =>
                        handleEntryChange(
                          index,
                          'target_type',
                          e.target.value as 'string' | 'number' | 'date' | 'boolean'
                        )
                      }
                      size="sm"
                      className={styles.cellSelect}
                    >
                      {TARGET_TYPE_OPTIONS.map((option) => (
                        <SelectItem
                          key={option.value}
                          value={option.value}
                          text={option.label}
                        />
                      ))}
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Checkbox
                      id={`is-required-${index}`}
                      labelText={entry.is_required ? 'Yes' : 'No'}
                      checked={entry.is_required}
                      onChange={(_, { checked }) =>
                        handleEntryChange(index, 'is_required', checked)
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <div className={styles.orderButtons}>
                      <Button
                        kind="ghost"
                        size="sm"
                        hasIconOnly
                        iconDescription={`Move ${entry.source_column} up`}
                        renderIcon={ArrowUp}
                        onClick={() => handleMoveUp(index)}
                        disabled={index === 0}
                      />
                      <Button
                        kind="ghost"
                        size="sm"
                        hasIconOnly
                        iconDescription={`Move ${entry.source_column} down`}
                        renderIcon={ArrowDown}
                        onClick={() => handleMoveDown(index)}
                        disabled={index === entries.length - 1}
                      />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              <TableRow>
                <TableCell>
                  <TextInput
                    id="new-source-column"
                    labelText=""
                    hideLabel
                    placeholder="Source column"
                    value={newEntry.source_column}
                    onChange={(e) =>
                      setNewEntry({ ...newEntry, source_column: e.target.value })
                    }
                    size="sm"
                    className={styles.cellInput}
                  />
                </TableCell>
                <TableCell>
                  <TextInput
                    id="new-target-field"
                    labelText=""
                    hideLabel
                    placeholder="Target field"
                    value={newEntry.target_field}
                    onChange={(e) =>
                      setNewEntry({ ...newEntry, target_field: e.target.value })
                    }
                    size="sm"
                    className={styles.cellInputMono}
                  />
                </TableCell>
                <TableCell>
                  <span className={styles.typeHint}>text, number, boolean or date</span>
                </TableCell>
                <TableCell>
                  <span>Optional</span>
                </TableCell>
                <TableCell>
                  <Button
                    kind="tertiary"
                    size="sm"
                    renderIcon={Add}
                    onClick={handleAddEntry}
                    disabled={!newEntry.source_column || !newEntry.target_field}
                  >
                    Add mapping entry
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        )}
      </DataTable>
    </div>
  )
}
