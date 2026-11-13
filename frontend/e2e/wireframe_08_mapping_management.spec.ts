import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 08: Mapping Management', () => {
  test('should navigate to mapping MAP-SYN-001, add elevation entry, verify page elements', async ({
    page,
  }) => {
    // Log in as syn.admin
    await page.goto('/login')
    await page.getByLabel(/username/i).fill('admin@example.com')
    await page.locator('#password').fill('admin123')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Wait for navigation to home page
    await expect(page).toHaveURL(/\/(home)?$/)

    // Navigate to mapping MAP-SYN-001 (ID 1)
    await page.goto('/mappings/1')

    // Wait for page to load
    await page.waitForLoadState('networkidle')

    // Verify page heading - either full text or partial
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/inventory/i)

    // Verify active version tag
    await expect(page.getByText(/Active: v2/i)).toBeVisible()

    // Verify draft version tag
    await expect(page.getByText(/Draft of v3/i)).toBeVisible()

    // Verify mapping details section
    await expect(page.getByText(/Mapping details/i)).toBeVisible()
    
    // Verify immutability notification
    await expect(page.getByText(/Versions are immutable/i).first()).toBeVisible()

    // Add new entry: source_column="elevation", target_field="elevation"
    await page.locator('#new-source-column').fill('elevation')
    await page.locator('#new-target-field').fill('elevation')
    
    // Click Add mapping entry button
    await page.getByRole('button', { name: /add mapping entry/i }).click()

    // Verify entry was added (original 4 + 1 new = 5)
    await expect(page.getByText(/5 entries/i)).toBeVisible()

    // Verify publish button exists (may be disabled due to validation)
    const publishButton = page.getByRole('button', { name: /publish new version/i })
    await expect(publishButton).toBeVisible()

    // Verify version history sidebar
    await expect(page.getByText(/Version history/i)).toBeVisible()
    await expect(page.getByText(/^Draft$/i)).toBeVisible()
    await expect(page.getByText(/Not published/i)).toBeVisible()
  })
})
