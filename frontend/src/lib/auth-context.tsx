import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient } from './api-client'
import sharedConfig from '../../../shared_config.json'

interface User {
  id: number
  subject_id: string
  display_name: string
  email: string
  role_codes: string[]
  is_asp: boolean
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem(sharedConfig.auth.storage_key)
    if (token) {
      // Verify token and load current user
      apiClient
        .get<User>('/auth/me')
        .then((userData) => {
          setUser(userData)
          setIsAuthenticated(true)
        })
        .catch(() => {
          // Token invalid, clear it
          localStorage.removeItem(sharedConfig.auth.storage_key)
          setIsAuthenticated(false)
        })
        .finally(() => {
          setIsLoading(false)
        })
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    const response = await apiClient.post<{ access_token: string; user: User }>(
      '/auth/login',
      { email, password }
    )
    
    const token = response[sharedConfig.auth.login_response.token_field as keyof typeof response] as string
    const userData = response[sharedConfig.auth.login_response.user_field as keyof typeof response] as User
    
    localStorage.setItem(sharedConfig.auth.storage_key, token)
    setUser(userData)
    setIsAuthenticated(true)
  }

  const logout = () => {
    localStorage.removeItem(sharedConfig.auth.storage_key)
    setUser(null)
    setIsAuthenticated(false)
    window.location.href = '/login'
  }

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
