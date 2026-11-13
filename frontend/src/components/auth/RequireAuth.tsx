import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth-context'

interface RequireAuthProps {
  children: ReactNode
  allowedRoles?: string[]
}

export function RequireAuth({ children, allowedRoles }: RequireAuthProps) {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // If allowedRoles is specified, check if user has at least one of the required roles
  if (allowedRoles && allowedRoles.length > 0) {
    const userRoles = user?.role_codes || []
    const hasRequiredRole = allowedRoles.some(role => userRoles.includes(role))
    
    if (!hasRequiredRole) {
      // User lacks required role - redirect to home with access denied
      return <Navigate to="/" replace />
    }
  }

  return <>{children}</>
}
