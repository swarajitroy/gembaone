import { useState, FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Theme,
  Grid,
  Column,
  TextInput,
  PasswordInput,
  Button,
  InlineNotification,
  Tag
} from '@carbon/react'
import { Information } from '@carbon/icons-react'
import { useAuth } from '../lib/auth-context'
import styles from './LoginPage.module.css'

export function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { login } = useAuth()
  
  // Default to demo credentials matching seed data
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState<string | null>(null)
  const [correlationId, setCorrelationId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isRateLimited, setIsRateLimited] = useState(false)
  
  // Check for session expired message
  const sessionExpired = searchParams.get('session') === 'expired'

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setCorrelationId(null)
    setIsRateLimited(false)
    setIsLoading(true)

    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      if (err instanceof Error) {
        const errorMessage = err.message
        
        // Check for rate limiting (429 status)
        if (errorMessage.includes('429') || errorMessage.toLowerCase().includes('rate limit')) {
          setIsRateLimited(true)
          setCorrelationId(`corr-${Math.random().toString(16).substring(2, 10)}`)
        } else {
          setError(errorMessage)
          setCorrelationId(`corr-${Math.random().toString(16).substring(2, 10)}`)
        }
      } else {
        setError('Sign-in failed')
        setCorrelationId(`corr-${Math.random().toString(16).substring(2, 10)}`)
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Theme theme="white">
      <header
        className={`flex items-center gap-4 min-h-12 px-4 ${styles.header}`}
        aria-label="GembaONE Platform"
      >
        <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-white">
          Skip to main content
        </a>
        <a href="/" className="text-white font-semibold no-underline">
          Ericsson <span className="font-normal">GembaONE Platform</span>
        </a>
        <div className="ml-auto">
          <Tag type="gray" size="sm">
            <Information size={12} className="mr-1" />
            Synthetic demo data
          </Tag>
        </div>
      </header>

      <main id="main-content" className="p-8">
        <Grid>
          <Column sm={4} md={6} lg={8}>
            <div className="bg-gray-100 p-8">
              <h1 className="text-2xl mb-2">Sign in</h1>
              <p className="text-gray-600 mb-6">Use the account issued for your role.</p>

              {sessionExpired && (
                <InlineNotification
                  kind="info"
                  title="Session expired"
                  subtitle="You were signed out after a period of inactivity. Sign in again."
                  className="mb-4"
                  lowContrast
                  hideCloseButton
                />
              )}

              {error && (
                <InlineNotification
                  kind="error"
                  title="Sign-in failed"
                  subtitle={`${error}${correlationId ? ` (Correlation ID: ${correlationId})` : ''}`}
                  className="mb-4"
                  lowContrast
                  hideCloseButton
                />
              )}

              {isRateLimited && (
                <InlineNotification
                  kind="warning"
                  title="Too many attempts"
                  subtitle={`Try again in 60 seconds. The Sign in button stays unavailable until then.${correlationId ? ` (Correlation ID: ${correlationId})` : ''}`}
                  className="mb-4"
                  lowContrast
                  hideCloseButton
                />
              )}

              <form onSubmit={handleSubmit}>
                <TextInput
                  id="username"
                  labelText="Username (required)"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="text"
                  required
                  className="mb-4"
                  autoComplete="username"
                  disabled={isLoading || isRateLimited}
                />
                <PasswordInput
                  id="password"
                  labelText="Password (required)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="mb-4"
                  autoComplete="current-password"
                  disabled={isLoading || isRateLimited}
                />
                <Button
                  type="submit"
                  disabled={isLoading || isRateLimited}
                  className="w-full"
                >
                  {isLoading ? 'Signing in…' : isRateLimited ? 'Sign in unavailable (60 s)' : 'Sign in'}
                </Button>
              </form>

              <p className="text-xs text-gray-600 mt-4">
                Demonstration environment — synthetic data only. Sign-in attempts are recorded in the audit trail.
              </p>
              <p className="text-xs text-gray-600 mt-2">
                <a href="#main-content">Need access? Contact your internal administrator.</a>
              </p>
            </div>

            <div className="mt-8 bg-gray-100 p-8">
              <h2 className="text-lg mb-4">Who can do what</h2>
              <p className="text-gray-600 mb-4">
                Your role decides which pages and actions appear after sign-in. Pages you cannot use are not shown.
              </p>
              <dl className="space-y-2 text-sm">
                <div className="grid grid-cols-[minmax(120px,1fr)_2fr] gap-4">
                  <dt className="font-semibold">Internal admin</dt>
                  <dd className="text-gray-600">Checklist templates, mappings, checklists and Excel ingestion.</dd>
                </div>
                <div className="grid grid-cols-[minmax(120px,1fr)_2fr] gap-4">
                  <dt className="font-semibold">Field engineer</dt>
                  <dd className="text-gray-600">Start and complete checklists, attach photos and capture location.</dd>
                </div>
                <div className="grid grid-cols-[minmax(120px,1fr)_2fr] gap-4">
                  <dt className="font-semibold">Reviewer</dt>
                  <dd className="text-gray-600">View submitted checklists. No editing.</dd>
                </div>
                <div className="grid grid-cols-[minmax(120px,1fr)_2fr] gap-4">
                  <dt className="font-semibold">ASP user</dt>
                  <dd className="text-gray-600">Upload Excel workbooks and view your own results only.</dd>
                </div>
                <div className="grid grid-cols-[minmax(120px,1fr)_2fr] gap-4">
                  <dt className="font-semibold">All roles</dt>
                  <dd className="text-gray-600">No role can delete records. Uploaded files and submitted checklists are retained.</dd>
                </div>
              </dl>
              <p className="text-xs text-gray-600 mt-4">
                Demo users: <code className="font-mono">syn.admin</code>, <code className="font-mono">syn.engineer</code>,{' '}
                <code className="font-mono">syn.reviewer</code>, <code className="font-mono">syn.asp</code>. Passwords are issued separately.
              </p>
              <p className="text-xs text-gray-600 mt-2">
                Validation outcomes are produced by deterministic rules. No AI is used in this release; people remain accountable for decisions.
              </p>
            </div>
          </Column>
        </Grid>
      </main>

      <footer className="border-t border-gray-200 p-4 text-xs text-gray-600 bg-gray-100">
        Synthetic demonstration data only · Ericsson confidential constraints apply · Build/correlation reference shown on outcomes
      </footer>
    </Theme>
  )
}
