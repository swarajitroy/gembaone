import { test, expect } from './_pipeline_guard'

test.describe('Login Flow', () => {
  test('should log in with syn.admin credentials and redirect to home', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login')

    // Verify login page loaded
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()

    // Type credentials into the form
    const usernameInput = page.getByLabel(/username \(required\)/i)
    const passwordInput = page.locator('#password')

    await usernameInput.fill('admin@example.com')
    await passwordInput.fill('admin123')

    // Submit the form
    await page.getByRole('button', { name: /^sign in$/i }).click()

    // Wait for redirect to home page
    await expect(page).toHaveURL('/')

    // Verify home page loaded
    await expect(page.getByRole('heading', { name: /^home$/i })).toBeVisible()

    // Verify user is logged in and role badge is displayed
    await expect(page.getByText(/signed in as/i)).toBeVisible()
  })

  test('should display role descriptions on login page', async ({ page }) => {
    await page.goto('/login')

    // Verify all role descriptions are present (in the role description list)
    await expect(page.getByRole('term').filter({ hasText: 'Internal admin' })).toBeVisible()
    await expect(page.getByRole('term').filter({ hasText: 'Field engineer' })).toBeVisible()
    await expect(page.getByRole('term').filter({ hasText: 'Reviewer' })).toBeVisible()
    await expect(page.getByRole('term').filter({ hasText: 'ASP user' })).toBeVisible()
  })

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/login')

    // Type invalid credentials into the form
    const usernameInput = page.getByLabel(/username \(required\)/i)
    const passwordInput = page.locator('#password')

    await usernameInput.fill('invalid@example.com')
    await passwordInput.fill('wrongpassword')

    // Submit the form
    await page.getByRole('button', { name: /^sign in$/i }).click()

    // Wait for error message - check for the notification container
    const errorNotification = page.locator('[kind="error"], .cds--inline-notification--error, [role="alert"]').first()
    await expect(errorNotification).toBeVisible({ timeout: 10000 })
  })
})
