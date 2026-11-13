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
import { Checkmark, Information, ErrorFilled } from '@carbon/icons-react'
import { IngestionRecord } from '../../types/ingestions'

interface IngestionsTableProps {
  ingestions: IngestionRecord[]
}

export function IngestionsTable({ ingestions }: IngestionsTableProps) {
  const headers = [
    { key: 'id', header: 'Ingestion ID' },
    { key: 'filename', header: 'File name' },
    { key: 'status', header: 'Status' },
    { key: 'counts', header: 'Accepted / warning / rejected' },
    { key: 'submitted', header: 'Submitted at' },
    { key: 'results', header: 'Results' },
  ]

  const rows = ingestions.map((ingestion) => ({
    id: String(ingestion.id),
    filename: ingestion.source_filename,
    status: ingestion.status,
    counts:
      ingestion.status === 'completed'
        ? `${ingestion.accepted_count.toLocaleString()} / ${ingestion.warning_count} / ${ingestion.rejected_count}`
        : 'Not ready',
    submitted: new Date(ingestion.uploaded_at).toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    results: ingestion.id,
  }))

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <Tag type="green" size="sm">
            <Checkmark size={12} className="mr-1" />
            Completed
          </Tag>
        )
      case 'validating':
        return (
          <Tag type="cyan" size="sm">
            <Information size={12} className="mr-1" />
            Validating
          </Tag>
        )
      case 'failed':
        return (
          <Tag type="red" size="sm">
            <ErrorFilled size={12} className="mr-1" />
            Failed
          </Tag>
        )
      default:
        return (
          <Tag type="gray" size="sm">
            {status}
          </Tag>
        )
    }
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
                    ) : cell.info.header === 'results' ? (
                      <Link to={`/ingestions/${cell.value}`} className="text-blue-600 hover:underline">
                        View results for {cell.value}
                      </Link>
                    ) : cell.info.header === 'id' ? (
                      <span className="font-mono text-sm">{cell.value}</span>
                    ) : cell.info.header === 'filename' ? (
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
