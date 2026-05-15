import { test, expect } from '@playwright/test';

test.describe('Agent Analysis UI', () => {
  test('should navigate from dashboard to diagnosis session and render agent results', async ({ page }) => {
    // 1. Visit Dashboard
    await page.goto('/');
    
    // 2. Dashboard should load
    await expect(page.locator('text=Operations Center')).toBeVisible();
    await expect(page.locator('text=Recent Diagnostic Sessions')).toBeVisible();

    // 3. Click the LP-01 Golden Path item
    await page.click('text=LP-CLAMP-014');

    // 4. Verify Navigation
    await expect(page).toHaveURL(/\/diagnosis-sessions\/LP-01-SESSION/);

    // 5. Verify Agent Analysis UI Header
    await expect(page.locator('text=Agent Analysis Results')).toBeVisible();
    await expect(page.locator('text=Analysis Complete')).toBeVisible();

    // 6. Verify Context
    await expect(page.locator('text=Situation Snapshot')).toBeVisible();
    await expect(page.locator('text=DO_CLAMP_SOL')).toBeVisible();

    // 7. Verify Agent Timeline
    await expect(page.locator('text=Agent Timeline')).toBeVisible();
    await expect(page.locator('text=Rule Scoring')).toBeVisible();

    // 8. Verify Guardrail
    await expect(page.locator('text=Safety Guardrail: Pass')).toBeVisible();

    // 9. Verify Hypotheses and Evidence
    await expect(page.locator('text=Top Hypotheses')).toBeVisible();
    await expect(page.locator('text=Clamp 완료 센서 위치 이탈 또는 감도 불량')).toBeVisible();
    await expect(page.locator('text=Linked Evidence')).toBeVisible();
    await expect(page.locator('text=DOC-LP-04')).toBeVisible();

    // 10. Verify Inspection Plan
    await expect(page.locator('text=Recommended Inspection Plan')).toBeVisible();
    await expect(page.locator('text=인터락 상태 확인')).toBeVisible();
  });
});
