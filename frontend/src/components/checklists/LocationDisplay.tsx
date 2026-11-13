import { Button, Stack } from '@carbon/react'
import styles from './LocationDisplay.module.scss'

interface Location {
  id: number
  latitude: number
  longitude: number
  accuracy_meters: number
  captured_at_utc: string
}

interface LocationDisplayProps {
  location: Location | null
  onCapture: () => Promise<void>
  readOnly?: boolean
}

export function LocationDisplay({ location, onCapture, readOnly = false }: LocationDisplayProps) {
  return (
    <Stack gap={4}>
      {!readOnly && (
        <Button kind="tertiary" size="sm" onClick={onCapture}>
          {location ? 'Capture location' : 'Capture location'}
        </Button>
      )}
      
      {location && (
        <dl className={styles.locationList}>
          <dt className="cds--label">Latitude</dt>
          <dd className={`${styles.locationLabel} cds--type-mono`}>
            {location.latitude.toFixed(4)}
          </dd>
          
          <dt className="cds--label">Longitude</dt>
          <dd className={`${styles.locationLabel} cds--type-mono`}>
            {location.longitude.toFixed(4)}
          </dd>
          
          <dt className="cds--label">Accuracy</dt>
          <dd className={styles.locationLabel}>
            ±{location.accuracy_meters} m
          </dd>
          
          <dt className="cds--label">Captured</dt>
          <dd className={styles.locationLabel}>
            {new Date(location.captured_at_utc).toLocaleString()}
          </dd>
        </dl>
      )}
      
      {!location && !readOnly && (
        <p className="cds--label cds--label-01">
          No location captured yet.
        </p>
      )}
      
      {location && !readOnly && (
        <p className="cds--label cds--label-01">
          Location is recorded with the checklist and visible only to authorised roles.
        </p>
      )}
    </Stack>
  )
}
