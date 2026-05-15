import { expect, test } from '@playwright/test';

test('home page shows FabMind Agent operations dashboard', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByText('FABMIND')).toBeVisible();
  await expect(page.getByText('Operations Center')).toBeVisible();
  await expect(page.getByText('Active Diagnosis')).toBeVisible();
  await expect(page.getByText('Pending Approval')).toBeVisible();
  await expect(page.getByText('Evidence Linked')).toBeVisible();
});
