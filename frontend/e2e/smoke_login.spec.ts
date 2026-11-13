import { test, expect } from './_pipeline_guard'

test('smoke login flow', async ({ page }) => {
  // Navigate to login page
  await page.goto('/login')

  // Verify login page loaded
  await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()

  // Fill in seed admin credentials
  await page.getByLabel(/username \(required\)/i).fill('admin@example.com')
  await page.locator('#password').fill('admin123')

  // Submit login form
  await page.getByRole('button', { name: /sign in/i }).click()

  // Wait for navigation to home page
  await page.waitForURL('/')

  // Verify home page loaded with user data
  await expect(page.getByRole('heading', { name: /home/i })).toBeVisible()
  await expect(page.getByText(/signed in as/i)).toBeVisible()
})
