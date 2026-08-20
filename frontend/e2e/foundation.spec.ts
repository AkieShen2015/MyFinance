import { expect, test } from '@playwright/test'

test('shows the Phase 4 dashboard analytics and transaction filters', async ({ page }) => {
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'Your financial overview', exact: true }),
  ).toBeVisible()
  await expect(page.getByText('Total income', { exact: true })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Expenses by category', exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Income vs expenses', exact: true }),
  ).toBeVisible()
  await page.getByRole('combobox', { name: 'Period', exact: true }).selectOption('last_3_months')
  await expect(page.getByLabel('From', { exact: true })).toBeDisabled()
  const accountCards = page.getByRole('button', { name: /^Toggle .+ in dashboard filters$/ })
  await accountCards.nth(0).scrollIntoViewIfNeeded()
  const scrollPositionBeforeSelection = await page.evaluate(() => window.scrollY)
  const firstAccountCard = await accountCards.nth(0).boundingBox()
  if (!firstAccountCard) throw new Error('First account card is not visible')
  await page.mouse.click(
    firstAccountCard.x + firstAccountCard.width / 2,
    firstAccountCard.y + firstAccountCard.height / 2,
  )
  await expect(page.getByText(/1 of \d+ accounts selected/, { exact: true })).toBeVisible()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(scrollPositionBeforeSelection)
  await accountCards.nth(1).click()
  await expect(page.getByText(/2 of \d+ accounts selected/, { exact: true })).toBeVisible()
  await expect(page.getByText('Across 2 selected accounts', { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: 'Show all accounts', exact: true }).click()
  await expect(page.getByText(/All \d+ accounts/, { exact: true })).toBeVisible()

  await page.getByRole('link', { name: 'Transactions', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Transactions', exact: true }),
  ).toBeVisible()
  await expect(page.getByLabel('Filter by bank', { exact: true })).toBeVisible()
  await expect(page.getByLabel('Filter by category', { exact: true })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Account', exact: true })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Type', exact: true })).toBeVisible()
  await expect(page.getByRole('combobox', { name: 'Sort by', exact: true })).toBeVisible()

  await expect(page.getByRole('columnheader', { name: 'Type', exact: true })).toHaveCount(0)
  await expect(page.getByRole('columnheader', { name: 'Actions', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'View', exact: true })).toHaveCount(0)

  await page.getByRole('link', { name: 'Analytics', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Analytics & insights', exact: true }),
  ).toBeVisible()
  await page.getByRole('combobox', { name: 'Period', exact: true }).selectOption('last_month')
  await expect(page.getByLabel('From', { exact: true })).toHaveValue('2026-07-01')
  await expect(page.getByLabel('To', { exact: true })).toHaveValue('2026-07-31')
  await page.getByRole('combobox', { name: 'Period', exact: true }).selectOption('this_year')
  await expect(page.getByRole('heading', { name: 'Top merchants', exact: true })).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Spending trends by category', exact: true }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'What deserves attention', exact: true }),
  ).toBeVisible()
  const recurringPayments = page
    .getByRole('heading', { name: 'Recurring payments', exact: true })
    .locator('xpath=ancestor::article')
  await expect(recurringPayments).toBeVisible()
  await expect(
    recurringPayments.getByText('Showing 1–10 of 10', { exact: true }),
  ).toBeVisible()
  await expect(page.getByText('AI-ready, privacy-first')).toBeVisible()
})
