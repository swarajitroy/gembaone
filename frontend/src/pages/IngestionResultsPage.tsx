import React, { useEffect, useState } from 'react';
import {
  Grid,
  Column,
  Breadcrumb,
  BreadcrumbItem,
  Tag,
  InlineNotification,
  Button,
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableContainer,
  TableToolbar,
  TableToolbarContent,
  Pagination,
  Select,
  SelectItem,
  Tile,
  Stack,
} from '@carbon/react';
import { Download, Checkmark, WarningAlt, Error, Information } from '@carbon/icons-react';
import { useParams } from 'react-router-dom';
import { apiClient } from '../lib/api-client';
import styles from './IngestionResultsPage.module.scss';

interface IngestionDetail {
  id: number;
  status: string;
  source_filename: string;
  mapping_version_id: number;
  uploaded_at: string;
  validation_started_at: string | null;
  validation_completed_at: string | null;
  accepted_count: number;
  rejected_count: number;
  warning_count: number;
}

interface RowResult {
  row_number: number;
  outcome: 'accepted' | 'rejected' | 'accepted_with_warning';
  target_record_key: string | null;
  issues: Array<{
    code: string;
    severity: 'error' | 'warning';
    message: string;
    rule_code?: string;
  }>;
}

export default function IngestionResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [ingestion, setIngestion] = useState<IngestionDetail | null>(null);
  const [rowResults, setRowResults] = useState<RowResult[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState(true);
  const [outcomeFilter, setOutcomeFilter] = useState('');

  useEffect(() => {
    loadIngestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (ingestion) {
      loadRowResults();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, page, pageSize, outcomeFilter]);

  const loadIngestion = async () => {
    try {
      const data = await apiClient.get<IngestionDetail>(`/ingestions/${id}`);
      setIngestion(data);
    } catch (error) {
      console.error('Failed to load ingestion:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRowResults = async () => {
    try {
      const offset = (page - 1) * pageSize;
      const data = await apiClient.get<{ items: RowResult[]; total: number }>(
        `/ingestions/${id}/results?limit=${pageSize}&offset=${offset}`
      );
      setRowResults(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to load row results:', error);
    }
  };

  const handleDownloadRawFile = async () => {
    try {
      const data = await apiClient.get<{ download_url: string }>(`/ingestions/${id}/raw-file`);
      window.open(data.download_url, '_blank');
    } catch (error) {
      console.error('Failed to download raw file:', error);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const data = await apiClient.get<{ download_url: string }>(`/ingestions/${id}/report`);
      window.open(data.download_url, '_blank');
    } catch (error) {
      console.error('Failed to download report:', error);
    }
  };

  const getOutcomeTag = (outcome: string) => {
    switch (outcome) {
      case 'accepted':
        return <Tag type="green" renderIcon={Checkmark}>Accepted</Tag>;
      case 'accepted_with_warning':
        return <Tag type="warm-gray" renderIcon={WarningAlt}>Accepted with warning</Tag>;
      case 'rejected':
        return <Tag type="red" renderIcon={Error}>Rejected</Tag>;
      default:
        return <Tag>{outcome}</Tag>;
    }
  };

  const getStatusTag = (status: string) => {
    switch (status) {
      case 'completed':
        return <Tag type="green" renderIcon={Checkmark}>Completed</Tag>;
      case 'validating':
        return <Tag type="cyan" renderIcon={Information}>Validating</Tag>;
      case 'failed':
        return <Tag type="red" renderIcon={Error}>Failed</Tag>;
      default:
        return <Tag type="gray">{status}</Tag>;
    }
  };

  if (loading || !ingestion) {
    return <div>Loading...</div>;
  }

  const headers = [
    { key: 'row_number', header: 'Row' },
    { key: 'outcome', header: 'Outcome' },
    { key: 'target_record_key', header: 'Target Record Key' },
    { key: 'issues', header: 'Issues' },
  ];

  const rows = rowResults.map((result) => ({
    id: result.row_number.toString(),
    row_number: result.row_number,
    outcome: result.outcome,
    target_record_key: result.target_record_key || '—',
    issues: result.issues.length > 0 
      ? result.issues.map(i => i.message).join('; ')
      : 'All checks passed.',
  }));

  return (
    <Grid>
      <Column lg={16} md={8} sm={4}>
        <Breadcrumb noTrailingSlash>
          <BreadcrumbItem href="/">Home</BreadcrumbItem>
          <BreadcrumbItem href="/ingestions">Excel ingestion</BreadcrumbItem>
          <BreadcrumbItem isCurrentPage>
            SYN-ING-{id?.toString().padStart(4, '0')}
          </BreadcrumbItem>
        </Breadcrumb>
      </Column>

      <Column lg={16} md={8} sm={4} className={styles.pageHeader}>
        <div className={styles.headerRow}>
          <div className={styles.headerLeft}>
            <h1 className={styles.heading}>Ingestion SYN-ING-{id?.toString().padStart(4, '0')}</h1>
            {getStatusTag(ingestion.status)}
            <Tag type="blue">Mapping SYN Site Inventory v2</Tag>
          </div>
          <div className={styles.downloadSection}>
            <div className={styles.downloadButtons}>
              <Button
                kind="secondary"
                renderIcon={Download}
                onClick={handleDownloadRawFile}
              >
                Download raw file
              </Button>
              <Button
                kind="primary"
                renderIcon={Download}
                onClick={handleDownloadReport}
                disabled={ingestion.status !== 'completed'}
              >
                Download result report
              </Button>
            </div>
            <p className="cds--label-01">
              Format: CSV. This action is recorded in the audit trail.
            </p>
          </div>
        </div>
      </Column>

      <Column lg={16} md={8} sm={4}>
        <InlineNotification
          kind="info"
          title=""
          subtitle="This report download is recorded in the audit trail. Validation outcomes are produced by deterministic rules. No AI is used in this release; people remain accountable for decisions."
          lowContrast
          hideCloseButton
        />
      </Column>

      <Column lg={16} md={8} sm={4} className={styles.summarySection}>
        <h2 className={styles.sectionHeading}>Summary</h2>
        <Grid narrow>
          <Column lg={4} md={2} sm={4}>
            <Tile className={styles.tile}>
              <Stack gap={3}>
                <div className={styles.tileHeader}>
                  <Information size={16} />
                  <span className="cds--label-01">Rows processed</span>
                </div>
                <div className={styles.tileValue}>
                  {ingestion.accepted_count + ingestion.warning_count + ingestion.rejected_count}
                </div>
              </Stack>
            </Tile>
          </Column>
          <Column lg={4} md={2} sm={4}>
            <Tile className={styles.tile}>
              <Stack gap={3}>
                <div className={styles.tileHeader}>
                  <Checkmark size={16} className={styles.tileIconSuccess} />
                  <span className="cds--label-01">Accepted</span>
                </div>
                <div className={styles.tileValue}>
                  {ingestion.accepted_count}
                </div>
              </Stack>
            </Tile>
          </Column>
          <Column lg={4} md={2} sm={4}>
            <Tile className={styles.tile}>
              <Stack gap={3}>
                <div className={styles.tileHeader}>
                  <WarningAlt size={16} className={styles.tileIconWarning} />
                  <span className="cds--label-01">Accepted with warning</span>
                </div>
                <div className={styles.tileValue}>
                  {ingestion.warning_count}
                </div>
              </Stack>
            </Tile>
          </Column>
          <Column lg={4} md={2} sm={4}>
            <Tile className={styles.tile}>
              <Stack gap={3}>
                <div className={styles.tileHeader}>
                  <Error size={16} className={styles.tileIconError} />
                  <span className="cds--label-01">Rejected</span>
                </div>
                <div className={styles.tileValue}>
                  {ingestion.rejected_count}
                </div>
              </Stack>
            </Tile>
          </Column>
        </Grid>
      </Column>

      <Column lg={16} md={8} sm={4} className={styles.rowResultsSection}>
        <h2 className={styles.sectionHeading}>Row-level results</h2>
        <DataTable rows={rows} headers={headers}>
          {({
            rows,
            headers,
            getTableProps,
            getHeaderProps,
            getRowProps,
            getTableContainerProps,
          }) => (
            <TableContainer {...getTableContainerProps()}>
              <TableToolbar>
                <TableToolbarContent>
                  <Select
                    id="outcome-filter"
                    labelText="Outcome"
                    size="sm"
                    value={outcomeFilter}
                    onChange={(e) => setOutcomeFilter(e.target.value)}
                  >
                    <SelectItem text="All" value="" />
                    <SelectItem text="Accepted" value="accepted" />
                    <SelectItem text="Accepted with warning" value="accepted_with_warning" />
                    <SelectItem text="Rejected" value="rejected" />
                  </Select>
                </TableToolbarContent>
              </TableToolbar>
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    {headers.map((header) => {
                      const headerProps = getHeaderProps({ header });
                      return (
                        <TableHeader {...headerProps}>
                          {header.header}
                        </TableHeader>
                      );
                    })}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row) => {
                    const originalResult = rowResults.find(r => r.row_number.toString() === row.id);
                    const rowData = row as unknown as { 
                      row_number: number; 
                      target_record_key: string; 
                      issues: string;
                    };
                    const rowProps = getRowProps({ row });
                    return (
                      <TableRow {...rowProps}>
                        <TableCell>{rowData.row_number}</TableCell>
                        <TableCell>{originalResult && getOutcomeTag(originalResult.outcome)}</TableCell>
                        <TableCell>{rowData.target_record_key}</TableCell>
                        <TableCell>{rowData.issues}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              <Pagination
                page={page}
                pageSize={pageSize}
                pageSizes={[10, 25, 50, 100]}
                totalItems={total}
                onChange={({ page, pageSize }) => {
                  setPage(page);
                  setPageSize(pageSize);
                }}
              />
            </TableContainer>
          )}
        </DataTable>
      </Column>
    </Grid>
  );
}
