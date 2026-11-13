import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 07: Ingestion Results', () => {
  test('should open completed ingestion and see results page structure', async ({ page }) => {
    // Log in as ASP user (syn.asp)
    await page.goto('/login')
    await page.getByLabel(/username/i).fill('asp@example.com')
    await page.locator('#password').fill('asp123')
    await page.getByRole('button', { name: /sign in/i }).click()
    
    await expect(page).toHaveURL(/\/(home)?$/)
    
    // Navigate to ingestion results page for seed ingestion ID 1  
    // (ID 1 in DB renders as SYN-ING-0001 on the page)
    await page.goto('/ingestions/1')
    
    // Verify page has ingestion heading with code (ID 1 = SYN-ING-0001)
    await expect(page.getByRole('heading', { name: /syn-ing-0001/i })).toBeVisible()
    
    // Verify download buttons exist
    await expect(page.getByRole('button', { name: /download raw file/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /download.*report/i })).toBeVisible()
    
    // Verify summary heading
    await expect(page.getByRole('heading', { name: /summary/i })).toBeVisible()
    
    // Verify summary data is present (tiles with counts)
    await expect(page.getByText(/1248/)).toBeVisible() // total rows
    await expect(page.getByText(/1190/)).toBeVisible() // accepted count
    
    // Verify row-level results heading
    await expect(page.getByRole('heading', { name: /row.*level.*results/i })).toBeVisible()
    
    // Verify table has data (table element exists)
    const table = page.locator('table')
    await expect(table).toBeVisible()
  })
})
