import { expect, test } from '@playwright/test';

test('home page shows FabMind Agent operations dashboard', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Operations Center' })).toBeVisible();
  await expect(page.getByText('FABMIND').first()).toBeVisible();
  await expect(page.getByText('Active Diagnosis').first()).toBeVisible();
  await expect(page.getByText('Evidence Linked').first()).toBeVisible();
  await expect(page.getByText('Required Actions').first()).toBeVisible();
});
