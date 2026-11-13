import { test, expect } from './_pipeline_guard'

test.describe('Home Page', () => {
  // Login once before all tests
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    
    const usernameInput = page.getByLabel(/username \(required\)/i)
    const passwordInput = page.locator('#password')
    
    await usernameInput.fill('admin@example.com')
    await passwordInput.fill('admin123')
    
    await page.getByRole('button', { name: /^sign in$/i }).click()
    
    // Wait for home page
    await expect(page).toHaveURL('/')
    await expect(page.getByRole('heading', { name: /^home$/i })).toBeVisible()
  })

  test('should display dashboard tiles', async ({ page }) => {
    // Verify tiles by looking for their content
    await expect(page.getByText('2 active · 1 retired')).toBeVisible()
    await expect(page.getByText('3 in progress · 5 submitted')).toBeVisible()
    await expect(page.getByText('1 validating · 4 completed · 1 failed')).toBeVisible()
    
    // Also verify user is signed in (combining with role badge test)
    await expect(page.getByText(/signed in as/i)).toBeVisible()
  })

  test('should display recent checklists table', async ({ page }) => {
    // Verify recent checklists section
    await expect(page.getByRole('heading', { name: /recent checklists/i })).toBeVisible()
  })

  test('should display recent ingestions table', async ({ page }) => {
    // Verify recent ingestions section
    await expect(page.getByRole('heading', { name: /recent ingestions/i })).toBeVisible()
    
    // Also verify role information section (combining tests)
    await expect(page.getByRole('heading', { name: /role view/i })).toBeVisible()
    await expect(page.getByText(/no role can delete records/i)).toBeVisible()
  })

  test('should navigate to checklist detail when clicking open link', async ({ page }) => {
    // Wait for checklists section
    await expect(page.getByRole('heading', { name: /recent checklists/i })).toBeVisible()
    
    // Check if there are any checklist rows with Open links
    const openLinks = page.getByRole('link').filter({ hasText: /open SYN-CL-/i })
    const count = await openLinks.count()
    
    if (count > 0) {
      // Click the first Open link
      await openLinks.first().click()
      
      // Verify navigation occurred (placeholder page is OK per requirements)
      await expect(page).toHaveURL(/\/checklists\//)
    }
  })
})
