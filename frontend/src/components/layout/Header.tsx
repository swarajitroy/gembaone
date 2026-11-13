import { Header as CarbonHeader, HeaderName, HeaderGlobalBar, HeaderGlobalAction, SkipToContent, Tag } from '@carbon/react'
import { Information, UserAvatar, Logout } from '@carbon/icons-react'
import { useAuth } from '../../lib/auth-context'

export function Header() {
  const { user, logout } = useAuth()

  return (
    <CarbonHeader aria-label="GembaONE Platform">
      <SkipToContent />
      <HeaderName href="/" prefix="Ericsson">
        GembaONE Platform
      </HeaderName>
      <HeaderGlobalBar>
        <Tag type="gray" className="ml-4">
          <Information className="mr-1" size={16} />
          Synthetic demo data
        </Tag>
        {user && (
          <>
            <div className="flex items-center gap-2 px-4 text-sm">
              <UserAvatar size={20} />
              <span>{user.display_name}</span>
              <Tag type="purple" size="sm">
                {user?.role_codes?.[0]?.replace('_', ' ') || ''}
              </Tag>
            </div>
            <HeaderGlobalAction aria-label="Sign out" tooltipAlignment="end" onClick={logout}>
              <Logout size={20} />
            </HeaderGlobalAction>
          </>
        )}
      </HeaderGlobalBar>
    </CarbonHeader>
  )
}
