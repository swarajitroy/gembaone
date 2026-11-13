import { TextInput, Stack } from '@carbon/react'
import styles from './MappingDetailsForm.module.scss'

interface MappingDetailsFormProps {
  mappingCode: string
  sourceEntity: string
  targetEntity: string
  onSourceEntityChange: (value: string) => void
  onTargetEntityChange: (value: string) => void
}

export default function MappingDetailsForm({
  mappingCode,
  sourceEntity,
  targetEntity,
  onSourceEntityChange,
  onTargetEntityChange,
}: MappingDetailsFormProps) {
  return (
    <Stack gap={5} className={styles.formGrid}>
      <TextInput
        id="mapping-code"
        labelText="Mapping code"
        value={mappingCode}
        readOnly
        className={styles.monoInput}
      />
      <TextInput
        id="source-entity"
        labelText="Source entity (required)"
        value={sourceEntity}
        onChange={(e) => onSourceEntityChange(e.target.value)}
        helperText="Sheet name in the workbook."
      />
      <TextInput
        id="target-entity"
        labelText="Target entity (required)"
        value={targetEntity}
        onChange={(e) => onTargetEntityChange(e.target.value)}
        helperText="Platform record type."
      />
    </Stack>
  )
}
