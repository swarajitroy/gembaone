import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 05: Checklist Review', () => {
  test('should display submitted checklist with status tags', async ({ page }) => {
    // Log in as reviewer
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
    
    const usernameInput = page.getByLabel(/username \(required\)/i)
    const passwordInput = page.locator('#password')
    await usernameInput.fill('reviewer@example.com')
    await passwordInput.fill('reviewer123')
    await page.getByRole('button', { name: /^sign in$/i }).click()
    
    await expect(page).toHaveURL('/')
    
    // Navigate to submitted checklist SYN-CL-0041 (ID 2)
    await page.goto('/checklists/2')
    
    // Verify page loaded
    const heading = page.locator('h1')
    await expect(heading).toBeVisible()
    
    // Verify checklist title (may be "Review: SYN-CL-0041" or just "SYN-CL-0041")
    await expect(heading).toContainText(/SYN-CL-0041|checklist|review/i)
    
    // Verify submitted status tag
    const submittedTag = page.locator('[class*="tag"], [class*="Tag"]').filter({ hasText: /submitted|complete/i }).first()
    await expect(submittedTag).toBeVisible()
    
    // Verify read-only tag
    const readOnlyTag = page.locator('[class*="tag"], [class*="Tag"]').filter({ hasText: /read.only|locked|view/i }).first()
    await expect(readOnlyTag).toBeVisible()
    
    // Verify template version tag
    const versionTag = page.locator('[class*="tag"], [class*="Tag"]').filter({ hasText: /template|v1\.0|version/i }).first()
    await expect(versionTag).toBeVisible()
  })

  test('should display review content with answers', async ({ page }) => {
    // Log in as reviewer
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible()
    
    const usernameInput = page.getByLabel(/username \(required\)/i)
    const passwordInput = page.locator('#password')
    await usernameInput.fill('reviewer@example.com')
    await passwordInput.fill('reviewer123')
    await page.getByRole('button', { name: /^sign in$/i }).click()
    
    await expect(page).toHaveURL('/')
    
    // Navigate to submitted checklist
    await page.goto('/checklists/2')
    await expect(page.locator('h1')).toBeVisible()
    
    // Wait for content to load
    await page.waitForTimeout(1500)
    
    // Verify answers content is visible (check for h2 heading within the content)
    const answersHeading = page.locator('h2').filter({ hasText: /answers/i })
    const headingCount = await answersHeading.count()
    
    // If h2 heading exists, verify it
    if (headingCount > 0) {
      await expect(answersHeading.first()).toBeVisible()
    } else {
      // Otherwise check for answers text anywhere on page
      const answersText = page.locator('text=/answers/i').first()
      await expect(answersText).toBeVisible()
    }
  })
})
