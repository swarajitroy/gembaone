import { SideNav, SideNavItems, SideNavLink } from '@carbon/react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { useAuth } from '../../lib/auth-context'

export function Sidebar() {
  const { user } = useAuth()
  const location = useLocation()

  const isAdmin = user?.role_codes?.includes('internal_admin')
  const isFieldEngineer = user?.role_codes?.includes('field_engineer')
  const isReviewer = user?.role_codes?.includes('reviewer')
  const isAsp = user?.is_asp

  return (
    <SideNav aria-label="Side navigation" isFixedNav expanded>
      <SideNavItems>
        <SideNavLink
          renderIcon={() => null}
          as={RouterLink}
          to="/"
          isActive={location.pathname === '/'}
        >
          Home
        </SideNavLink>
        {(isAdmin || isFieldEngineer) && (
          <SideNavLink
            renderIcon={() => null}
            as={RouterLink}
            to="/templates"
            isActive={location.pathname.startsWith('/templates')}
          >
            Checklist templates
          </SideNavLink>
        )}
        {(isAdmin || isFieldEngineer || isReviewer) && (
          <SideNavLink
            renderIcon={() => null}
            as={RouterLink}
            to="/checklists"
            isActive={location.pathname.startsWith('/checklists')}
          >
            Checklists
          </SideNavLink>
        )}
        {(isAdmin || isAsp) && (
          <SideNavLink
            renderIcon={() => null}
            as={RouterLink}
            to="/ingestions"
            isActive={location.pathname.startsWith('/ingestions')}
          >
            Excel ingestion
          </SideNavLink>
        )}
        {isAdmin && (
          <SideNavLink
            renderIcon={() => null}
            as={RouterLink}
            to="/mappings"
            isActive={location.pathname.startsWith('/mappings')}
          >
            Mappings
          </SideNavLink>
        )}
      </SideNavItems>
    </SideNav>
  )
}
