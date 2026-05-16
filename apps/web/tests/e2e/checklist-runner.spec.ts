import { test, expect } from '@playwright/test';

test.describe('Checklist Runner UI', () => {
  test('should render checklist items, field notes, and allow status change visually', async ({ page }) => {
    await page.goto('/checklist-runs/RUN-LP-01');

    await expect(page.getByRole('heading', { name: 'Checklist Runner' })).toBeVisible();
    await expect(page.getByText('RUN-LP-01').first()).toBeVisible();
    await expect(page.getByText('LP-01-SESSION').first()).toBeVisible();

    await expect(page.getByRole('heading', { name: '인터락 상태 확인' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '센서 LED 확인' })).toBeVisible();
    await expect(page.getByRole('heading', { name: '센서 bracket 고정 상태 확인' })).toBeVisible();
    await expect(page.getByText('EXPECTED OBSERVATION').first()).toBeVisible();

    const noteAreas = page.getByPlaceholder('Field notes / observations...');
    await expect(noteAreas).toHaveCount(3);
    await expect(noteAreas.nth(0)).toHaveValue('도어 닫힘 상태 및 FOUP 안착 센서 정상 동작 확인함.');
    await expect(noteAreas.nth(1)).toHaveValue('현장 매뉴얼 안전 점검 절차에 따라 확인 중. LED 점등 안됨.');

    const finalStatus = page.getByRole('combobox').last();
    await finalStatus.selectOption('IN_PROGRESS');
    await expect(finalStatus).toHaveValue('IN_PROGRESS');

    const finalNote = noteAreas.last();
    await finalNote.fill('Observed bracket state requires senior review before maintenance action.');
    await expect(finalNote).toHaveValue('Observed bracket state requires senior review before maintenance action.');

    const saveButton = page.locator('button', { hasText: 'Save Note' }).last();
    await expect(saveButton).toBeEnabled();
  });
});
