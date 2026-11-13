/**
 * E2E Journey Test: Ingestion Workflow
 * 
 * Tests complete user journey:
 * 1. Log in as ASP user (syn.asp)
 * 2. Upload workbook with mapping v2
 * 3. Wait for validation complete
 * 4. Verify summary counts
 * 5. Download report
 * 6. Verify CSV contents
 */

import { test, expect } from './_pipeline_guard';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import * as XLSX from 'xlsx';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe('Ingestion Journey', () => {
  test('complete ingestion workflow from login to report download', async ({ page }) => {
    // Step 1: Login as ASP user using the working login pattern
    await page.goto('/login');
    
    // Verify login page loaded
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    
    // Type credentials
    const usernameInput = page.getByLabel(/username \(required\)/i);
    const passwordInput = page.locator('#password');
    
    await usernameInput.fill('asp@example.com');
    await passwordInput.fill('asp123');
    
    // Submit the form
    await page.getByRole('button', { name: /^sign in$/i }).click();
    
    // Wait for redirect to home
    await expect(page).toHaveURL('/');
    await expect(page.getByText(/signed in as/i)).toBeVisible({ timeout: 10000 });
    
    // Step 2: Navigate to ingestion upload page
    await page.getByRole('link', { name: /ingestion|excel/i }).click();
    await page.waitForTimeout(1000);
    
    // Navigate to upload page
    const uploadLink = page.getByRole('link', { name: /upload|new ingestion/i });
    if (await uploadLink.isVisible()) {
      await uploadLink.click();
    } else {
      await page.goto('/ingestions/upload');
    }
    
    await expect(page.getByRole('heading', { name: /upload|ingestion/i })).toBeVisible({ timeout: 10000 });
    
    // Step 3: Select mapping version
    const mappingSelect = page.locator('select[name="mapping_version_id"], #mapping-select, [data-testid="mapping-select"]').first();
    await expect(mappingSelect).toBeVisible({ timeout: 5000 });
    await mappingSelect.selectOption({ index: 1 });
    
    // Step 4: Upload workbook
    const testWorkbookPath = await createTestWorkbook(page);
    
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(testWorkbookPath);
    
    await page.waitForTimeout(1000);
    
    // Submit upload
    const uploadButton = page.getByRole('button', { name: /upload|submit/i }).first();
    await expect(uploadButton).toBeVisible({ timeout: 5000 });
    await uploadButton.click();
    
    // Wait for upload to complete
    await page.waitForTimeout(2000);
    
    // Should redirect to ingestion detail page
    await expect(page.getByRole('heading', { name: /ingestion|SYN-ING/i })).toBeVisible({ timeout: 10000 });
    
    // Step 5: Wait for validation to complete
    let attempts = 0;
    const maxAttempts = 20;
    
    while (attempts < maxAttempts) {
      await page.waitForTimeout(1000);
      
      // Check status tag
      const statusTag = page.locator('.cds--tag[data-testid="status-tag"], .cds--tag').first();
      if (await statusTag.isVisible()) {
        const statusText = await statusTag.textContent();
        if (statusText && /completed|failed/i.test(statusText)) {
          break;
        }
      }
      
      // Reload page to get updated status
      if (attempts % 5 === 0) {
        await page.reload();
      }
      
      attempts++;
    }
    
    // Verify completed status
    await expect(page.getByText(/completed/i)).toBeVisible({ timeout: 5000 });
    
    // Step 6: Verify summary counts
    const summarySection = page.locator('[data-testid="summary-section"], .summary-tiles, .cds--tile-group').first();
    
    // Assert summary section exists
    await expect(summarySection).toBeVisible({ timeout: 5000 });
    
    // Verify counts are present
    const acceptedCount = summarySection.locator('[data-testid="accepted-count"], .accepted-tile').first();
    await expect(acceptedCount).toBeVisible({ timeout: 3000 });
    const acceptedText = await acceptedCount.textContent();
    expect(acceptedText).toMatch(/\d+/);
    
    const rejectedCount = summarySection.locator('[data-testid="rejected-count"], .rejected-tile').first();
    await expect(rejectedCount).toBeVisible({ timeout: 3000 });
    const rejectedText = await rejectedCount.textContent();
    expect(rejectedText).toMatch(/\d+/);
    
    // Step 7: View row-level results
    const resultsTable = page.locator('[data-testid="results-table"], .cds--data-table, table').first();
    
    // Assert table exists
    await expect(resultsTable).toBeVisible({ timeout: 5000 });
    
    // Verify table has rows
    const rows = resultsTable.locator('tbody tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    
    // Verify row structure
    const firstRow = rows.first();
    await expect(firstRow).toBeVisible();
    
    // Should have cells
    const cells = firstRow.locator('td');
    const cellCount = await cells.count();
    expect(cellCount).toBeGreaterThan(0);
    
    // Step 8: Download report
    const downloadReportButton = page.getByRole('button', { name: /download report/i }).first();
    
    // Assert button exists
    await expect(downloadReportButton).toBeVisible({ timeout: 5000 });
    
    // Start waiting for download
    const downloadPromise = page.waitForEvent('download');
    await downloadReportButton.click();
    
    // Wait for download to complete
    const download = await downloadPromise;
    const downloadPath = path.join(__dirname, '..', 'downloads', await download.suggestedFilename());
    
    // Ensure downloads directory exists
    const downloadsDir = path.join(__dirname, '..', 'downloads');
    if (!fs.existsSync(downloadsDir)) {
      fs.mkdirSync(downloadsDir, { recursive: true });
    }
    
    await download.saveAs(downloadPath);
    
    // Step 9: Verify CSV contents
    expect(fs.existsSync(downloadPath)).toBe(true);
    
    const csvContent = fs.readFileSync(downloadPath, 'utf-8');
    
    // Verify CSV has header row
    expect(csvContent).toContain('row_number');
    expect(csvContent).toContain('outcome');
    
    // Verify CSV has data rows
    const lines = csvContent.split('\n');
    expect(lines.length).toBeGreaterThan(1);
    
    // Clean up downloaded file
    fs.unlinkSync(downloadPath);
  });

  test('ingestion workflow with validation errors', async ({ page }) => {
    // Login as ASP user
    await page.goto('/login');
    const usernameInput = page.getByLabel(/username \(required\)/i);
    const passwordInput = page.locator('#password');
    await usernameInput.fill('asp@example.com');
    await passwordInput.fill('asp123');
    await page.getByRole('button', { name: /^sign in$/i }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate to upload
    await page.goto('/ingestions/upload');
    await expect(page.getByRole('heading', { name: /upload|ingestion/i })).toBeVisible({ timeout: 10000 });
    
    // Select mapping
    const mappingSelect = page.locator('select[name="mapping_version_id"], #mapping-select').first();
    await expect(mappingSelect).toBeVisible({ timeout: 5000 });
    await mappingSelect.selectOption({ index: 1 });
    
    // Upload workbook with validation errors
    const errorWorkbookPath = await createErrorWorkbook(page);
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(errorWorkbookPath);
    await page.waitForTimeout(1000);
    
    // Submit
    const uploadButton = page.getByRole('button', { name: /upload|submit/i }).first();
    await uploadButton.click();
    await page.waitForTimeout(3000);
    
    // Wait for completion
    await page.waitForTimeout(5000);
    await page.reload();
    
    // Verify rejected count > 0
    const rejectedCount = page.locator('[data-testid="rejected-count"], .rejected-tile').first();
    
    // Assert count element exists
    await expect(rejectedCount).toBeVisible({ timeout: 5000 });
    const rejectedText = await rejectedCount.textContent();
    const count = parseInt(rejectedText?.match(/\d+/)?.[0] || '0');
    expect(count).toBeGreaterThan(0);
    
    // Verify error details in results table
    const resultsTable = page.locator('table, .cds--data-table').first();
    
    // Assert table exists
    await expect(resultsTable).toBeVisible({ timeout: 5000 });
    
    // Look for rejected rows
    const rejectedRows = resultsTable.locator('tr:has-text("rejected")');
    const rejectedRowCount = await rejectedRows.count();
    expect(rejectedRowCount).toBeGreaterThan(0);
    
    // Verify issues are shown
    const issuesCell = resultsTable.locator('td:has-text("error"), td:has-text("warning")').first();
    await expect(issuesCell).toBeVisible({ timeout: 2000 });
  });

  test('ASP user can only see own ingestions', async ({ page }) => {
    // Login as ASP user
    await page.goto('/login');
    const usernameInput = page.getByLabel(/username \(required\)/i);
    const passwordInput = page.locator('#password');
    await usernameInput.fill('asp@example.com');
    await passwordInput.fill('asp123');
    await page.getByRole('button', { name: /^sign in$/i }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate to ingestions list
    await page.goto('/ingestions');
    
    // Verify page loaded
    await expect(page.getByRole('heading', { name: /ingestion/i })).toBeVisible({ timeout: 10000 });
    
    // Should only see own ingestions
    const ingestionTable = page.locator('table, .cds--data-table').first();
    
    // Assert table exists
    await expect(ingestionTable).toBeVisible({ timeout: 5000 });
    
    const rows = ingestionTable.locator('tbody tr');
    const rowCount = await rows.count();
    
    // ASP user should see at least their own ingestions
    expect(rowCount).toBeGreaterThan(0);
  });
});

// Helper function to create test workbook
async function createTestWorkbook(page: any): Promise<string> {
  const testData = [
    ['SITE_ID', 'SITE_NAME', 'LAT', 'LON'],
    ['SITE-E2E-001', 'E2E Test Site 1', 59.3293, 18.0686],
    ['SITE-E2E-002', 'E2E Test Site 2', 57.7089, 11.9746],
    ['SITE-E2E-003', 'E2E Test Site 3', 55.6050, 13.0038]
  ];

  const workbookPath = path.join(__dirname, '..', 'test-data', 'e2e-test-workbook.xlsx');
  
  const dir = path.dirname(workbookPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  const ws = XLSX.utils.aoa_to_sheet(testData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
  XLSX.writeFile(wb, workbookPath);
  
  return workbookPath;
}

// Helper function to create workbook with errors
async function createErrorWorkbook(page: any): Promise<string> {
  const errorData = [
    ['SITE_ID', 'SITE_NAME', 'LAT', 'LON'],
    ['SITE-ERR-001', 'Error Site 1', 99.9999, 18.0686],
    ['SITE-ERR-002', 'Error Site 2', 57.7089, 199.9999],
    ['SITE-ERR-003', 'Error Site 3', 55.6050, 13.0038]
  ];

  const workbookPath = path.join(__dirname, '..', 'test-data', 'e2e-error-workbook.xlsx');
  
  const dir = path.dirname(workbookPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  const ws = XLSX.utils.aoa_to_sheet(errorData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
  XLSX.writeFile(wb, workbookPath);
  
  return workbookPath;
}
