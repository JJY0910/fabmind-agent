import { expect, test } from '@playwright/test';

const sidebarRoutes = [
  { label: /^Dashboard/, path: '/', heading: /Operations Center/ },
  { label: /^Equipment/, path: '/equipment', heading: /Equipment Registry/ },
  { label: /^Active Incidents/, path: '/active-incidents', heading: /Active Incidents/ },
  { label: /^Checklists/, path: '/checklists', heading: /Checklist Runs/ },
  { label: /^Approvals/, path: '/approvals', heading: /Approval Queue/ },
  { label: /^Audit Console/, path: '/audit-events', heading: /Audit Console/ },
  { label: /^Settings/, path: '/settings', heading: /System Safety Settings/ },
];

const directRoutes = [
  { path: '/', visibleText: /Operations Center/ },
  { path: '/equipment', visibleText: /Equipment Registry/ },
  { path: '/active-incidents', visibleText: /Active Incidents/ },
  { path: '/checklists', visibleText: /Checklist Runs/ },
  { path: '/approvals', visibleText: /Approval Queue/ },
  { path: '/audit-events', visibleText: /Audit Console/ },
  { path: '/settings', visibleText: /System Safety Settings/ },
  { path: '/diagnosis-sessions/LP-01-SESSION', visibleText: /LP-01-SESSION/ },
  { path: '/checklist-runs/RUN-LP-01', visibleText: /RUN-LP-01/ },
  { path: '/report-drafts/RPT-LP-01', visibleText: /RPT-LP-01/ },
];

const representativeIds = [
  { path: '/equipment', id: 'LP-01' },
  { path: '/diagnosis-sessions/LP-01-SESSION', id: 'LP-01-SESSION' },
  { path: '/checklists', id: 'RUN-LP-01' },
  { path: '/checklist-runs/RUN-LP-01', id: 'RUN-LP-01' },
  { path: '/approvals', id: 'RPT-LP-01' },
  { path: '/report-drafts/RPT-LP-01', id: 'RPT-LP-01' },
];

async function expectNoNotFound(page: import('@playwright/test').Page) {
  await expect(page.getByText('This page could not be found')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: /^404$/ })).toHaveCount(0);
}

test.describe('Sidebar navigation hardening', () => {
  for (const route of sidebarRoutes) {
    test(`sidebar link routes to ${route.path} without not-found UI`, async ({ page }) => {
      await page.goto('/');

      await page.getByRole('link', { name: route.label }).click();

      await expect.poll(() => new URL(page.url()).pathname).toBe(route.path);
      await expectNoNotFound(page);
      await expect(page.getByRole('heading', { name: route.heading })).toBeVisible();
    });
  }
});

test.describe('Required routes are not 404', () => {
  for (const route of directRoutes) {
    test(`${route.path} renders an operational page`, async ({ page }) => {
      const response = await page.goto(route.path);

      expect(response?.status(), `${route.path} should not return HTTP 404`).not.toBe(404);
      await expectNoNotFound(page);
      await expect(page.getByText(route.visibleText).first()).toBeVisible();
    });
  }
});

test.describe('Representative operational IDs remain visible', () => {
  for (const item of representativeIds) {
    test(`${item.id} is visible on ${item.path}`, async ({ page }) => {
      await page.goto(item.path);

      await expectNoNotFound(page);
      await expect(page.getByText(item.id).first()).toBeVisible();
    });
  }
});
