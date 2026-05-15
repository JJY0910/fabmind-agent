import { test, expect } from '@playwright/test';

test('home page shows FabMind Agent golden path', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('FABMIND AGENT')).toBeVisible();
  await expect(page.getByText('Golden Path')).toBeVisible();
});
