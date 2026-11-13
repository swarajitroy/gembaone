import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { LoginPage } from '../pages/LoginPage'

const mockNavigate = vi.fn()
const mockLogin = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams()],
  }
})

vi.mock('../lib/auth-context', async () => {
  const actual = await vi.importActual('../lib/auth-context')
  return {
    ...actual,
    useAuth: () => ({
      login: mockLogin,
      user: null,
      isAuthenticated: false,
      logout: vi.fn(),
    }),
  }
})

describe('LoginPage', () => {
  it('renders login form with default credentials', () => {
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/username/i)).toHaveValue('admin@example.com')
    const passwordInput = container.querySelector('#password') as HTMLInputElement
    expect(passwordInput).toHaveValue('admin123')
    expect(screen.getByRole('button', { name: /^sign in$/i })).toBeInTheDocument()
  })

  it('displays role descriptions', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Internal admin')).toBeInTheDocument()
    expect(screen.getByText('Field engineer')).toBeInTheDocument()
    expect(screen.getByText('Reviewer')).toBeInTheDocument()
    expect(screen.getByText('ASP user')).toBeInTheDocument()
  })

  it('allows changing username and password', async () => {
    const user = userEvent.setup()
    const { container } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = container.querySelector('#password') as HTMLInputElement

    await user.clear(usernameInput)
    await user.type(usernameInput, 'engineer@example.com')
    await user.clear(passwordInput)
    await user.type(passwordInput, 'engineer123')

    expect(usernameInput).toHaveValue('engineer@example.com')
    expect(passwordInput).toHaveValue('engineer123')
  })

  it('calls login on form submit', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValue(undefined)

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const submitButton = screen.getByRole('button', { name: /^sign in$/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('admin@example.com', 'admin123')
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('displays error message on login failure', async () => {
    const user = userEvent.setup()
    mockLogin.mockRejectedValue(new Error('Invalid credentials'))

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const submitButton = screen.getByRole('button', { name: /^sign in$/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/sign-in failed/i)).toBeInTheDocument()
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during sign-in', async () => {
    const user = userEvent.setup()
    mockLogin.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)))

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const submitButton = screen.getByRole('button', { name: /^sign in$/i })
    await user.click(submitButton)

    expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument()

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled()
    })
  })
})
