import { Information } from '@carbon/icons-react'
import styles from './ConditionalItemIndicator.module.scss'

interface ConditionalItemIndicatorProps {
  condition: string
}

export function ConditionalItemIndicator({ condition }: ConditionalItemIndicatorProps) {
  return (
    <div className={styles.indicator}>
      <div className={styles.content}>
        <Information size={16} className={styles.icon} />
        <span className="cds--label">
          {condition}
        </span>
      </div>
    </div>
  )
}
