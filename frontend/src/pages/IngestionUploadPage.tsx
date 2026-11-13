import React, { useState } from 'react';
import {
  Grid,
  Column,
  Breadcrumb,
  BreadcrumbItem,
  Tag,
  InlineNotification,
  FileUploader,
  Select,
  SelectItem,
  Button,
  Stack,
} from '@carbon/react';
import { Upload } from '@carbon/icons-react';
import { useNavigate } from 'react-router-dom';
import styles from './IngestionUploadPage.module.scss';

interface MappingVersion {
  id: number;
  version_number: number;
  version_label: string;
  status: string;
}

export default function IngestionUploadPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [mappingVersionId, setMappingVersionId] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // In real app, fetch mapping versions from API
  const mappingVersions: MappingVersion[] = [
    { id: 1, version_number: 2, version_label: 'v2.0', status: 'active' },
    { id: 2, version_number: 1, version_label: 'v1.0', status: 'superseded' },
  ];

  const handleFileChange = (event: React.SyntheticEvent<HTMLElement>) => {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
      const file = files[0];
      
      // Validate file type
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.csv')) {
        setError('Only .xlsx and .csv files are supported.');
        setSelectedFile(null);
        return;
      }
      
      // Validate file size (25MB)
      const maxSize = 25 * 1024 * 1024;
      if (file.size > maxSize) {
        setError('The file is larger than 25 MB. Split the workbook and upload each part.');
        setSelectedFile(null);
        return;
      }
      
      setError(null);
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Choose a file before uploading.');
      return;
    }
    
    if (!mappingVersionId) {
      setError('Choose a mapping version before uploading.');
      return;
    }
    
    setIsUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('mapping_version_id', mappingVersionId);
      
      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch('/api/v1/ingestions', {
        method: 'POST',
        headers,
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      
      const result = await response.json();
      // Navigate to results page
      navigate(`/ingestions/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setMappingVersionId('');
    setError(null);
  };

  return (
    <Grid>
      <Column lg={16} md={8} sm={4}>
        <Breadcrumb noTrailingSlash>
          <BreadcrumbItem href="/">Home</BreadcrumbItem>
          <BreadcrumbItem href="/ingestions" isCurrentPage>
            Excel ingestion
          </BreadcrumbItem>
        </Breadcrumb>
      </Column>

      <Column lg={16} md={8} sm={4} className={styles.pageHeader}>
        <Stack gap={3}>
          <div className={styles.headerLeft}>
            <h1 className={styles.heading}>Upload Excel workbook</h1>
            <Tag type="purple">ASP · restricted access</Tag>
          </div>
          <p className="cds--label-01">
            Your uploads and results only.
          </p>
        </Stack>
      </Column>

      <Column lg={16} md={8} sm={4}>
        <InlineNotification
          kind="info"
          title="Uploads are permanent."
          subtitle="Uploaded files are stored unchanged and cannot be replaced or deleted. This upload is recorded in the audit trail. If you need a correction, contact your internal Ericsson contact. Use only synthetic or approved workbook data."
          lowContrast
          hideCloseButton
        />
      </Column>

      <Column lg={8} md={4} sm={4} className={styles.uploadSection}>
        <Stack gap={5}>
          <h2 className={styles.sectionHeading}>Choose a workbook</h2>
          
          <FileUploader
            labelTitle=""
            labelDescription=".xlsx or .csv · up to 25 MB · one file at a time"
            buttonLabel="Choose file"
            buttonKind="tertiary"
            size="md"
            filenameStatus="edit"
            accept={['.xlsx', '.csv']}
            multiple={false}
            disabled={isUploading}
            iconDescription="Delete file"
            onChange={handleFileChange}
          />

          {selectedFile && (
            <Grid narrow>
              <Column lg={12} md={6} sm={3}>
                <Stack gap={2}>
                  <div className="cds--label-01">
                    {selectedFile.name}
                  </div>
                  <div className="cds--label-01">
                    {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
                  </div>
                </Stack>
              </Column>
              <Column lg={4} md={2} sm={1}>
                <Tag type="cyan">Ready to upload</Tag>
              </Column>
            </Grid>
          )}

          <div className={styles.mappingSelector}>
            <Select
              id="mapping-version-select"
              name="mapping_version_id"
              labelText="Mapping version (required)"
              helperText="Defines how workbook columns map to platform fields."
              value={mappingVersionId}
              onChange={(e) => setMappingVersionId(e.target.value)}
              disabled={isUploading}
            >
              <SelectItem text="Choose a mapping version" value="" />
              {mappingVersions.map((version) => (
                <SelectItem
                  key={version.id}
                  text={`SYN Site Inventory · ${version.version_label} (${version.status})`}
                  value={version.id.toString()}
                />
              ))}
            </Select>
          </div>

          {error && (
            <div className={styles.errorMessage}>
              <InlineNotification
                kind="error"
                title=""
                subtitle={error}
                lowContrast
                hideCloseButton
              />
            </div>
          )}

          <Stack gap={3} orientation="horizontal">
            <Button
              kind="primary"
              renderIcon={Upload}
              onClick={handleUpload}
              disabled={!selectedFile || !mappingVersionId || isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload and validate'}
            </Button>
            <Button
              kind="ghost"
              onClick={handleClear}
              disabled={isUploading}
            >
              Clear selection
            </Button>
          </Stack>

          <p className="cds--label-01">
            The structure of the workbook is checked immediately. Row-level results appear when validation completes.
          </p>
        </Stack>
      </Column>
    </Grid>
  );
}
