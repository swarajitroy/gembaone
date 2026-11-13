import { Tag, Stack } from '@carbon/react'
import styles from './EvidenceGallery.module.scss'

interface Attachment {
  id: number
  file_object_id: number
  original_filename: string
  content_type: string
  byte_size: number
  uploaded_by_user_id: number
  uploaded_at_utc: string
}

interface EvidenceGalleryProps {
  attachments: Attachment[]
}

export function EvidenceGallery({ attachments }: EvidenceGalleryProps) {
  if (!attachments || attachments.length === 0) {
    return (
      <p className="cds--label">
        No evidence attached
      </p>
    )
  }

  return (
    <div className={styles.grid}>
      {attachments.map(attachment => (
        <div key={attachment.id} className={`cds--tile ${styles.tile}`}>
          <div 
            className={styles.thumb}
            role="img"
            aria-label={`Thumbnail for ${attachment.original_filename}`}
          >
            SYN sample photo
          </div>
          <Stack gap={2}>
            <div className={styles.tags}>
              <Tag type="purple">Synthetic</Tag>
              <Tag type="red">Sensitive data</Tag>
            </div>
            <p className={`${styles.filename} cds--type-mono cds--label-01`}>
              {attachment.original_filename}
            </p>
            <p className={`${styles.meta} cds--label-01`}>
              {(attachment.byte_size / 1024).toFixed(1)} KB · {new Date(attachment.uploaded_at_utc).toLocaleString()}
            </p>
          </Stack>
        </div>
      ))}
    </div>
  )
}
