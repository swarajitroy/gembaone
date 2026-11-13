import { Link } from 'react-router-dom'
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Tag
} from '@carbon/react'
import { Checkmark, Information } from '@carbon/icons-react'
import { ChecklistListItem } from '../../types/checklists'

interface ChecklistsTableProps {
  checklists: ChecklistListItem[]
}

export function ChecklistsTable({ checklists }: ChecklistsTableProps) {
  const headers = [
    { key: 'id', header: 'Checklist ID' },
    { key: 'template', header: 'Template and version' },
    { key: 'status', header: 'Status' },
    { key: 'submitter', header: 'Started by' },
    { key: 'submitted', header: 'Submitted at' },
    { key: 'open', header: 'Open' },
  ]

  const rows = checklists.map((checklist) => ({
    id: checklist.id,
    template: `${checklist.template_name} · ${checklist.template_version_label}`,
    status: checklist.status,
    submitter: checklist.created_by_display_name,
    submitted: checklist.submitted_at_utc || 'Not yet',
    open: checklist.id,
  }))

  const getStatusTag = (status: string) => {
    if (status === 'submitted') {
      return (
        <Tag type="green" size="sm">
          <Checkmark size={12} className="mr-1" />
          Submitted
        </Tag>
      )
    }
    return (
      <Tag type="cyan" size="sm">
        <Information size={12} className="mr-1" />
        In progress
      </Tag>
    )
  }

  return (
    <DataTable rows={rows} headers={headers}>
      {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
        <Table {...getTableProps()}>
          <TableHead>
            <TableRow>
              {headers.map((header) => (
                <TableHeader {...getHeaderProps({ header })} key={header.key}>
                  {header.header}
                </TableHeader>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow {...getRowProps({ row })} key={row.id}>
                {row.cells.map((cell) => (
                  <TableCell key={cell.id}>
                    {cell.info.header === 'status' ? (
                      getStatusTag(cell.value as string)
                    ) : cell.info.header === 'open' ? (
                      <Link to={`/checklists/${cell.value}`} className="text-blue-600 hover:underline">
                        Open {cell.value}
                      </Link>
                    ) : cell.info.header === 'id' ? (
                      <span className="font-mono text-sm">{cell.value}</span>
                    ) : (
                      cell.value
                    )}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </DataTable>
  )
}
