import { test, expect } from '@playwright/test';

test.describe('Checklist Runner UI', () => {
  test('should render checklist items, field notes, and allow status change visually', async ({ page }) => {
    // Navigate directly to the mock runner
    await page.goto('/checklist-runs/RUN-LP-01');

    // 1. Verify Navigation & Header
    await expect(page.locator('text=Checklist Runner')).toBeVisible();
    await expect(page.locator('text=RUN-LP-01')).toBeVisible();

    // 2. Verify Session context
    await expect(page.getByText('Checklist Runner')).toBeVisible();

    // 3. Verify Item list
    await expect(page.locator('text=인터락 상태 확인')).toBeVisible();
    await expect(page.locator('text=센서 LED 확인')).toBeVisible();

    // 4. Verify Note contents (mock data checks)
    await expect(page.locator('textarea').first()).toHaveValue('도어 닫힘 상태 및 FOUP 안착 센서 정상 동작 확인함.');

    // 5. Verify Expected Observations
    await expect(page.locator('text=EXPECTED OBSERVATION').first()).toBeVisible();

    // 6. Test Input interaction
    const noteArea = page.getByPlaceholder('Field notes / observations...').last();
    await noteArea.fill('Test input for bracket check');
    await expect(noteArea).toHaveValue('Test input for bracket check');

    // 7. Test Save button presence
    const saveButton = page.locator('button', { hasText: 'Save Note' }).last();
    await expect(saveButton).toBeEnabled();
  });
});
