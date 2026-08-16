import { expect, test } from '@playwright/test'

test('shows the Phase 3 dashboard and transaction filters', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Your financial overview' })).toBeVisible()
  await expect(page.getByText('15', { exact: true }).first()).toBeVisible()

  await page.getByRole('link', { name: 'Transactions' }).click()
  await expect(page.getByRole('heading', { name: 'Transactions' })).toBeVisible()
  await expect(page.getByLabel('Filter by bank')).toBeVisible()
  await expect(page.getByLabel('Filter by category')).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Account', exact: true })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Type', exact: true })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Sort by', exact: true })).toBeVisible()

  await expect(page.getByRole('columnheader', { name: 'Type' })).toHaveCount(0)
  await expect(page.getByRole('columnheader', { name: 'Actions' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'View' })).toHaveCount(0)
})
