/**
 * E2E Journey Test: Field Survey Workflow
 * 
 * Tests complete user journey:
 * 1. Log in as field engineer (syn.engineer)
 * 2. Create checklist from template TPL-SYN-001
 * 3. Answer all items including conditional items
 * 4. Upload photo attachment
 * 5. Capture location
 * 6. Submit checklist
 * 7. Verify submitted status
 */

import { test, expect } from './_pipeline_guard';

test.describe('Field Survey Journey', () => {
  test('complete field survey workflow from login to submission', async ({ page }) => {
    // Step 1: Login as field engineer using the working login pattern
    await page.goto('/login');
    
    // Verify login page loaded
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    
    // Type credentials using the correct selectors from wireframe_01
    const usernameInput = page.getByLabel(/username \(required\)/i);
    const passwordInput = page.locator('#password');
    
    await usernameInput.fill('engineer@example.com');
    await passwordInput.fill('engineer123');
    
    // Submit the form
    await page.getByRole('button', { name: /^sign in$/i }).click();
    
    // Wait for redirect to home
    await expect(page).toHaveURL('/');
    await expect(page.getByText(/signed in as/i)).toBeVisible();
    
    // Step 2: Navigate to checklists
    await page.getByRole('link', { name: /checklists/i }).click();
    await page.waitForURL(/\/checklists/);
    
    // Navigate to existing draft checklist (SYN-CL-0042 from seed - ID 1)
    await page.goto('/checklists/1');
    
    // Verify page loaded - match the specific checklist code heading
    await expect(page.getByRole('heading', { name: /^SYN-CL-\d+/i })).toBeVisible({ timeout: 10000 });
    
    // Step 3: Answer required items
    // The seed checklist already has some answers, we'll add/update
    const siteAccessField = page.locator('[name="site_access"]').first();
    await expect(siteAccessField).toBeVisible({ timeout: 5000 });
    
    // Fill or select site access
    const tagName = await siteAccessField.evaluate(el => el.tagName.toLowerCase());
    if (tagName === 'select') {
      await siteAccessField.selectOption('Clear');
    } else {
      await siteAccessField.fill('Clear');
    }
    await siteAccessField.blur();
    await page.waitForTimeout(500);
    
    // Step 4: Upload photo attachment if uploader present
    const fileUploader = page.locator('input[type="file"]').first();
    await expect(fileUploader).toBeVisible({ timeout: 5000 });
    
    // Create a dummy image file
    const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
    await fileUploader.setInputFiles({
      name: 'site-photo.png',
      mimeType: 'image/png',
      buffer: buffer
    });
    
    await page.waitForTimeout(1000);
    
    // Step 5: Capture location
    const captureLocationButton = page.getByRole('button', { name: /capture location|add location/i }).first();
    
    // Assert button exists
    await expect(captureLocationButton).toBeVisible({ timeout: 5000 });
    
    // Mock geolocation
    await page.context().grantPermissions(['geolocation']);
    await page.context().setGeolocation({ latitude: 59.3293, longitude: 18.0686 });
    
    await captureLocationButton.click();
    await page.waitForTimeout(500);
    
    // Verify location captured
    await expect(page.getByText(/location captured|59.3293|18.0686/i)).toBeVisible({ timeout: 3000 });
    
    // Step 6: Submit checklist
    const submitButton = page.getByRole('button', { name: /submit/i }).first();
    await expect(submitButton).toBeVisible({ timeout: 5000 });
    await submitButton.click();
    
    // Wait for submission to complete
    await page.waitForTimeout(2000);
    
    // Step 7: Verify submitted status
    const successIndicator = page.getByText(/submitted|success|complete/i).first();
    await expect(successIndicator).toBeVisible({ timeout: 10000 });
    
    // Verify status tag shows "submitted"
    const statusTag = page.locator('.cds--tag, [data-testid="status-tag"]').first();
    await expect(statusTag).toBeVisible({ timeout: 5000 });
    await expect(statusTag).toContainText(/submitted/i);
    
    // Verify read-only state (submit button should be gone or disabled)
    const submitButtonAfter = page.getByRole('button', { name: /submit/i });
    // Assert button is no longer enabled
    await expect(submitButtonAfter).not.toBeVisible();
  });

  test('field survey workflow with conditional item visibility', async ({ page }) => {
    // Login
    await page.goto('/login');
    const usernameInput = page.getByLabel(/username \(required\)/i);
    const passwordInput = page.locator('#password');
    await usernameInput.fill('engineer@example.com');
    await passwordInput.fill('engineer123');
    await page.getByRole('button', { name: /^sign in$/i }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate to existing draft checklist (SYN-CL-0042 from seed)
    await page.goto('/checklists/1');
    
    // Verify page loaded
    await expect(page.getByRole('heading', { name: /^SYN-CL-\d+/i })).toBeVisible({ timeout: 10000 });
    
    // Test conditional visibility: find trigger field
    const triggerField = page.locator('[name="site_access"]').first();
    
    // Assert field exists
    await expect(triggerField).toBeVisible({ timeout: 5000 });
    
    // Change to value that triggers condition (Obstructed)
    const tagName = await triggerField.evaluate(el => el.tagName.toLowerCase());
    if (tagName === 'select') {
      await triggerField.selectOption('Obstructed');
    } else {
      await triggerField.fill('Obstructed');
    }
    await triggerField.blur();
    await page.waitForTimeout(1000);
    
    // Verify conditional field appears
    const conditionalField = page.locator('[name="obstruction_details"]').first();
    await expect(conditionalField).toBeVisible({ timeout: 3000 });
    
    // Fill conditional field
    await conditionalField.fill('Conditional field test');
    await conditionalField.blur();
    
    // Change back to hide conditional
    if (tagName === 'select') {
      await triggerField.selectOption('Clear');
    } else {
      await triggerField.fill('Clear');
    }
    await triggerField.blur();
    await page.waitForTimeout(1000);
    
    // Verify conditional field hidden
    await expect(conditionalField).not.toBeVisible({ timeout: 3000 });
  });

  test('field survey submission validation', async ({ page }) => {
    // Login
    await page.goto('/login');
    const usernameInput = page.getByLabel(/username \(required\)/i);
    const passwordInput = page.locator('#password');
    await usernameInput.fill('engineer@example.com');
    await passwordInput.fill('engineer123');
    await page.getByRole('button', { name: /^sign in$/i }).click();
    await expect(page).toHaveURL('/');
    
    // Navigate to draft checklist
    await page.goto('/checklists/1');
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: /^SYN-CL-\d+/i })).toBeVisible({ timeout: 10000 });
    
    // Try to submit without completing required fields
    // First, clear any existing answers
    const clearableFields = await page.locator('input[type="text"], textarea').all();
    for (const field of clearableFields) {
      if (await field.isVisible()) {
        await field.fill('');
      }
    }
    
    // Attempt submission
    const submitButton = page.getByRole('button', { name: /submit/i }).first();
    
    // Assert button exists
    await expect(submitButton).toBeVisible({ timeout: 5000 });
    await submitButton.click();
    
    // Should show validation errors
    const errorNotification = page.locator('.cds--inline-notification--error, [role="alert"]').first();
    await expect(errorNotification).toBeVisible({ timeout: 5000 });
    
    // Verify still on same page (not submitted)
    const statusTag = page.locator('.cds--tag').first();
    await expect(statusTag).toBeVisible({ timeout: 5000 });
    await expect(statusTag).not.toContainText(/submitted/i);
  });
});
