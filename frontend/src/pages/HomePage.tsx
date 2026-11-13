import { useState, useEffect } from 'react'
import {
  Grid,
  Column,
  Tile,
  Tag,
  SkeletonText,
  InlineNotification
} from '@carbon/react'
import { Information } from '@carbon/icons-react'
import { useAuth } from '../lib/auth-context'
import { apiClient } from '../lib/api-client'
import { Layout } from '../components/layout/Layout'
import { ChecklistsTable } from '../components/checklists/ChecklistsTable'
import { IngestionsTable } from '../components/ingestions/IngestionsTable'
import { ChecklistListItem } from '../types/checklists'
import { IngestionRecord } from '../types/ingestions'

export function HomePage() {
  const { user } = useAuth()
  const [checklists, setChecklists] = useState<ChecklistListItem[]>([])
  const [ingestions, setIngestions] = useState<IngestionRecord[]>([])
  const [isLoadingChecklists, setIsLoadingChecklists] = useState(true)
  const [isLoadingIngestions, setIsLoadingIngestions] = useState(true)
  const [checklistsError, setChecklistsError] = useState<string | null>(null)
  const [ingestionsError, setIngestionsError] = useState<string | null>(null)

  useEffect(() => {
    const loadChecklists = async () => {
      try {
        setIsLoadingChecklists(true)
        const response = await apiClient.get<{ items: ChecklistListItem[]; total: number } | ChecklistListItem[]>(
          '/checklists'
        )
        const items = Array.isArray(response) ? response : response?.items || []
        setChecklists(items.slice(0, 3)) // Show recent 3
      } catch (error) {
        console.error('Failed to load checklists:', error)
        setChecklistsError(error instanceof Error ? error.message : 'Failed to load checklists')
      } finally {
        setIsLoadingChecklists(false)
      }
    }

    const loadIngestions = async () => {
      // Only load ingestions for roles that have ingestion_view permission
      const canViewIngestions = user?.role_codes.some(
        role => role === 'internal_admin' || role === 'asp_user'
      )
      
      if (!canViewIngestions) {
        setIsLoadingIngestions(false)
        return
      }

      try {
        setIsLoadingIngestions(true)
        const response = await apiClient.get<{ items: IngestionRecord[]; total: number } | IngestionRecord[]>(
          '/ingestions'
        )
        const items = Array.isArray(response) ? response : response?.items || []
        setIngestions(items.slice(0, 3)) // Show recent 3
      } catch (error) {
        console.error('Failed to load ingestions:', error)
        setIngestionsError(error instanceof Error ? error.message : 'Failed to load ingestions')
      } finally {
        setIsLoadingIngestions(false)
      }
    }

    loadChecklists()
    loadIngestions()
  }, [user])

  const getRoleDisplay = (roleCodes: string[]) => {
    const roleMap: Record<string, { label: string; color: 'purple' | 'blue' | 'gray' | 'cyan' }> = {
      internal_admin: { label: 'Internal admin', color: 'purple' },
      field_engineer: { label: 'Field engineer', color: 'blue' },
      reviewer: { label: 'Reviewer', color: 'gray' },
      asp_user: { label: 'ASP user', color: 'cyan' },
    }
    const role = roleCodes[0] || 'unknown'
    return roleMap[role] || { label: role.replace('_', ' '), color: 'gray' }
  }

  const roleInfo = user ? getRoleDisplay(user.role_codes) : null
  
  // Check if user can view ingestions
  const canViewIngestions = user?.role_codes.some(
    role => role === 'internal_admin' || role === 'asp_user'
  ) ?? false

  return (
    <Layout>
      <Grid>
        <Column sm={4} md={8} lg={16}>
          <h1 className="text-2xl mb-2">Home</h1>
          <p className="text-gray-600 mb-6 flex items-center gap-2">
            Signed in as {user?.display_name} ({user?.subject_id}) ·{' '}
            {roleInfo && (
              <Tag type={roleInfo.color} size="sm">
                {roleInfo.label}
              </Tag>
            )}
            . Navigation shows only what your role can use.
          </p>
        </Column>

        <Column sm={4} md={4} lg={5} className="mb-6">
          <Tile className="min-h-32">
            <div className="text-xs text-gray-600 mb-2">Checklist templates</div>
            <div className="text-lg mb-2">2 active · 1 retired</div>
            <div className="text-sm text-gray-600">Create, version and start checklists.</div>
          </Tile>
        </Column>

        <Column sm={4} md={4} lg={5} className="mb-6">
          <Tile className="min-h-32">
            <div className="text-xs text-gray-600 mb-2">My checklists</div>
            <div className="text-lg mb-2">3 in progress · 5 submitted</div>
            <div className="text-sm text-gray-600">Continue or review checklist records.</div>
          </Tile>
        </Column>

        <Column sm={4} md={4} lg={6} className="mb-6">
          <Tile className="min-h-32">
            <div className="text-xs text-gray-600 mb-2">Excel ingestion</div>
            <div className="text-lg mb-2">1 validating · 4 completed · 1 failed</div>
            <div className="text-sm text-gray-600">Upload workbooks and read results.</div>
          </Tile>
        </Column>

        <Column sm={4} md={8} lg={16} className="mt-8 mb-8">
          <h2 className="text-xl mb-4">Recent checklists</h2>
          {isLoadingChecklists ? (
            <div className="p-4 bg-gray-100" aria-busy="true">
              <SkeletonText paragraph lineCount={3} />
            </div>
          ) : checklistsError ? (
            <InlineNotification
              kind="error"
              title="Failed to load checklists"
              subtitle={checklistsError}
              lowContrast
              hideCloseButton
            />
          ) : checklists.length === 0 ? (
            <div className="p-8 bg-gray-100 text-center">
              <p className="text-gray-600">No checklist instances yet. Start your first checklist from a template.</p>
            </div>
          ) : (
            <ChecklistsTable checklists={checklists} />
          )}
        </Column>

        {canViewIngestions && (
          <Column sm={4} md={8} lg={16} className="mt-8 mb-8">
            <h2 className="text-xl mb-4">Recent ingestions</h2>
            {isLoadingIngestions ? (
              <div className="p-4 bg-gray-100" aria-busy="true">
                <SkeletonText paragraph lineCount={3} />
              </div>
            ) : ingestionsError ? (
              <InlineNotification
                kind="error"
                title="Failed to load ingestions"
                subtitle={ingestionsError}
                lowContrast
                hideCloseButton
              />
            ) : ingestions.length === 0 ? (
              <div className="p-8 bg-gray-100 text-center">
                <p className="text-gray-600">No Excel ingestions yet. Upload your first workbook.</p>
              </div>
            ) : (
              <IngestionsTable ingestions={ingestions} />
            )}
          </Column>
        )}

        <Column sm={4} md={8} lg={16} className="mt-8">
          <h2 className="text-xl mb-4">Role view</h2>
          <p className="text-xs text-gray-600 mb-4">
            <Information size={16} className="inline mr-1" />
            This page is shown for the {roleInfo?.label} role. Other roles see a reduced version of the same page; they are not separate screens.
          </p>
          <dl className="space-y-2 text-sm">
            <div className="grid grid-cols-[200px_1fr] gap-4 border-t border-gray-200 pt-3">
              <dt className="font-semibold">Field engineer</dt>
              <dd className="text-gray-600">Home and Checklists. Templates list allows Start checklist only; no builder.</dd>
            </div>
            <div className="grid grid-cols-[200px_1fr] gap-4 border-t border-gray-200 pt-3">
              <dt className="font-semibold">Reviewer</dt>
              <dd className="text-gray-600">Home and Checklists. Submitted checklists with Review only.</dd>
            </div>
            <div className="grid grid-cols-[200px_1fr] gap-4 border-t border-gray-200 pt-3">
              <dt className="font-semibold">ASP user</dt>
              <dd className="text-gray-600">Home and Excel ingestion. Only the Excel ingestion tile and own ingestions. No templates, checklists or mappings.</dd>
            </div>
            <div className="grid grid-cols-[200px_1fr] gap-4 border-t border-gray-200 pt-3">
              <dt className="font-semibold">Internal admin</dt>
              <dd className="text-gray-600">All sections shown above.</dd>
            </div>
          </dl>
          <p className="text-xs text-gray-600 mt-4">
            No role can delete records. This release uses deterministic rules only; no AI makes decisions.
          </p>
        </Column>
      </Grid>
    </Layout>
  )
}
