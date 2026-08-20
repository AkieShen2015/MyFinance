import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'

const recurringPayments = Array.from({ length: 12 }, (_, index) => ({
  average_amount: `${String(index + 10)}.00`,
  cadence_days: 30,
  confidence: '0.90',
  merchant: `Recurring merchant ${String(index + 1)}`,
  next_expected_date: '2026-09-17',
  occurrences: 4,
}))

const unusualTransactions = Array.from({ length: 12 }, (_, index) => ({
  amount: `${String(index + 100)}.00`,
  baseline_amount: '40.00',
  category: 'Other',
  date: '2026-08-10',
  merchant: `Unusual merchant ${String(index + 1)}`,
  multiple: '2.50',
  transaction_id: `unusual-${String(index + 1)}`,
}))

const responses: Record<string, unknown> = {
  '/api/dashboard/summary': {
    date_from: '2026-08-01',
    date_to: '2026-08-20',
    total_income: '8000.00',
    total_expenses: '5200.00',
    net_cash_flow: '2800.00',
    total_account_balance: '21770.11',
    currency: 'AUD',
  },
  '/api/dashboard/expenses-by-category': [
    { category: 'Groceries', amount: '142.30', percentage: '100.00' },
  ],
  '/api/dashboard/income-vs-expenses': [
    { month: '2026-08-01', income: '8000.00', expenses: '5200.00' },
  ],
  '/api/accounts': [
    {
      id: 'account-1',
      institution_id: 'institution-1',
      institution_name: 'ANZ',
      account_name: 'Everyday Account',
      account_type: 'transaction',
      masked_account_number: '•••• 1842',
      currency: 'AUD',
      current_balance: '4280.42',
      available_balance: '4280.42',
      connection_status: 'active',
      last_sync_at: '2026-08-15T00:00:00Z',
    },
  ],
  '/api/analytics/report': {
    date_from: '2026-01-01',
    date_to: '2026-08-20',
    previous_date_from: '2025-05-13',
    previous_date_to: '2025-12-31',
    income: { current: '8000.00', previous: '7600.00', change_amount: '400.00', change_percentage: '5.26' },
    expenses: { current: '5200.00', previous: '4800.00', change_amount: '400.00', change_percentage: '8.33' },
    net_cash_flow: { current: '2800.00', previous: '2800.00', change_amount: '0.00', change_percentage: '0.00' },
    savings_rate: '35.00',
    category_trends: [{ category: 'Groceries', current_amount: '620.00', previous_amount: '500.00', change_amount: '120.00', change_percentage: '24.00', monthly: [{ month: '2026-08-01', amount: '620.00' }] }],
    top_merchants: [{ merchant: 'Woolworths', amount: '620.00', percentage: '11.92', transaction_count: 4 }],
    recurring_payments: recurringPayments,
    anomalies: unusualTransactions,
    insights: [{ kind: 'expense_change', title: 'Spending increased', message: 'Expenses increased by $400.00 against the previous equivalent period.', impact_amount: '400.00', confidence: '0.99' }],
    ai_payload: { period_start: '2026-01-01', period_end: '2026-08-20', expense_change_amount: '400.00', expense_change_percentage: '8.33', top_category_changes: [], recurring_total: '13.99', anomaly_count: 0 },
  },
  '/api/transactions?limit=15': {
    items: [
      {
        id: 'transaction-1',
        account_id: 'account-1',
        category_id: 'category-groceries',
        transaction_date: '2026-08-15',
        institution_name: 'ANZ',
        account_name: 'Everyday Account',
        merchant_name: 'Woolworths',
        description: 'WOOLWORTHS 1234 SYDNEY',
        category_name: 'Groceries',
        tags: [],
        transaction_type: 'expense',
        amount: '-142.30',
        currency: 'AUD',
        pending: false,
      },
    ],
    total: 150,
    limit: 15,
    offset: 0,
  },
  '/api/transactions?limit=15&account_id=account-1': {
    items: [
      {
        id: 'transaction-2',
        account_id: 'account-1',
        category_id: 'category-other',
        transaction_date: '2026-08-14',
        institution_name: 'ANZ',
        account_name: 'Everyday Account',
        merchant_name: 'Account-filtered purchase',
        description: 'ACCOUNT FILTERED PURCHASE',
        category_name: 'Other',
        tags: [],
        transaction_type: 'expense',
        amount: '-10.00',
        currency: 'AUD',
        pending: false,
      },
    ],
    total: 1,
    limit: 15,
    offset: 0,
  },
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('renders seeded accounts and recent transactions', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url =
        typeof input === 'string'
          ? new URL(input, 'http://localhost')
          : input instanceof URL
            ? input
            : new URL(input.url)
      const path = `${url.pathname}${url.search}`
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(responses[url.pathname] ?? responses[path]),
      } as Response)
    })
    vi.stubGlobal(
      'fetch',
      fetchMock,
    )

    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Your financial overview' })).toBeVisible()
    expect(screen.getByText('Total income')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Expenses by category' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Income vs expenses' })).toBeVisible()
    const accountCard = screen.getByRole('button', {
      name: 'Toggle Everyday Account in dashboard filters',
    })
    expect(accountCard).toBeVisible()
    expect(screen.getByText('Woolworths')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Recent 1 transactions' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Go to transactions' })).toHaveAttribute(
      'href',
      '/transactions',
    )

    fireEvent.click(accountCard)

    expect(await screen.findByText('Account-filtered purchase')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Show all accounts' })).toBeVisible()
    expect(screen.getByText('1 of 1 accounts selected')).toBeVisible()
    await waitFor(() => {
      const requestedUrls = fetchMock.mock.calls.map(([input]) =>
        typeof input === 'string' ? input : input instanceof URL ? input.href : input.url,
      )
      expect(
        requestedUrls.some(
          (url) =>
            url.includes('/api/dashboard/summary?') && url.includes('account_id=account-1'),
        ),
      ).toBe(true)
      expect(
        requestedUrls.some(
          (url) =>
            url.includes('/api/dashboard/expenses-by-category?') &&
            url.includes('account_id=account-1'),
        ),
      ).toBe(true)
      expect(
        requestedUrls.some(
          (url) =>
            url.includes('/api/dashboard/income-vs-expenses?') &&
            url.includes('account_id=account-1'),
        ),
      ).toBe(true)
    })

    fireEvent.click(screen.getByRole('link', { name: 'Analytics' }))
    expect(await screen.findByRole('heading', { name: 'Analytics & insights' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Top merchants' })).toBeVisible()
    expect(screen.getByText('Spending increased')).toBeVisible()
    expect(screen.getByText('AI-ready, privacy-first')).toBeVisible()
    expect(screen.getByText(/compared year-over-year/)).toBeVisible()
    expect(screen.getByLabelText('From')).toBeDisabled()
    fireEvent.change(screen.getByRole('combobox', { name: 'Period' }), {
      target: { value: 'custom' },
    })
    expect(screen.getByLabelText('From')).toBeEnabled()
    fireEvent.change(screen.getByRole('combobox', { name: 'Period' }), {
      target: { value: 'last_month' },
    })
    await waitFor(() => {
      expect(screen.getByLabelText('From')).toHaveValue('2026-07-01')
      expect(screen.getByLabelText('To')).toHaveValue('2026-07-31')
    })
    expect(screen.getByText(/immediately preceding, non-overlapping period/)).toBeVisible()
    fireEvent.change(screen.getByRole('combobox', { name: 'Period' }), {
      target: { value: 'last_1_year' },
    })
    await waitFor(() => {
      expect(screen.getByLabelText('From')).toHaveValue('2025-08-20')
      expect(screen.getByLabelText('To')).toHaveValue('2026-08-20')
    })
    expect(screen.getByLabelText('From')).toBeDisabled()
    expect(screen.getAllByText('Showing 1–10 of 12')).toHaveLength(2)
    fireEvent.click(screen.getByRole('button', { name: 'Next recurring payments' }))
    expect(screen.getByText('Showing 11–12 of 12')).toBeVisible()
    expect(screen.getByText('Recurring merchant 12')).toBeVisible()
    expect(screen.getByText('Showing 1–10 of 12')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Next unusual transactions' }))
    expect(screen.getAllByText('Showing 11–12 of 12')).toHaveLength(2)
    expect(screen.getByText('Unusual merchant 12')).toBeVisible()
  })
})
