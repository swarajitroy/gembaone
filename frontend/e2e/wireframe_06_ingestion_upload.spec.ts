import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 06: Ingestion Upload', () => {
  test('should navigate to ingestion upload and see upload interface', async ({ page }) => {
    // Log in as ASP user (syn.asp)
    await page.goto('/login')
    await page.getByLabel(/username/i).fill('asp@example.com')
    await page.locator('#password').fill('asp123')
    await page.getByRole('button', { name: /sign in/i }).click()
    
    await expect(page).toHaveURL(/\/(home)?$/)
    
    // Navigate to ingestion upload page
    await page.goto('/ingestions/upload')
    
    // Verify page heading
    await expect(page.getByRole('heading', { name: /upload.*excel.*workbook/i })).toBeVisible()
    
    // Verify ASP restriction tag
    await expect(page.getByText(/asp.*restricted access/i)).toBeVisible()
    
    // Verify info notification about immutability exists
    await expect(page.getByText(/uploads are permanent/i)).toBeVisible()
    
    // Verify file chooser section exists
    await expect(page.getByRole('heading', { name: /choose.*workbook/i })).toBeVisible()
    
    // Verify mapping version selector exists
    await expect(page.getByText(/mapping version.*required/i)).toBeVisible()
    
    // Verify upload button exists
    await expect(page.getByRole('button', { name: /upload and validate/i })).toBeVisible()
  })
})
