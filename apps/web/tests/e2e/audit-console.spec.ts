import { test, expect } from '@playwright/test';

test.describe('Audit Console UI', () => {
  test('should navigate to audit console and render filters and table', async ({ page }) => {
    // 1. Visit Dashboard
    await page.goto('/');
    
    // 2. Click the Audit Console link in Sidebar
    await page.click('text=Audit Console');

    // 3. Verify Navigation
    await expect(page).toHaveURL(/\/audit-events/);

    // 4. Verify Header
    await expect(page.locator('text=Immutable security and system action ledger')).toBeVisible();

    // 5. Verify Filters and Limit Controls
    await expect(page.getByPlaceholder('Search payload or actor...')).toBeVisible();
    await expect(page.locator('text=Event Type')).toBeVisible();
    await expect(page.locator('text=Severity')).toBeVisible();
    await expect(page.locator('text=Showing top')).toBeVisible();

    // 6. Verify Table Headers
    await expect(page.locator('text=Event ID / Time')).toBeVisible();
    await expect(page.locator('text=Payload Preview')).toBeVisible();

    // 7. Verify Mock Data Rendered
    await expect(page.locator('text=POLICY_BLOCKED')).toBeVisible();
    await expect(page.locator('text=AE-9001')).toBeVisible();
  });
});
