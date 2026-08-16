import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'

const responses: Record<string, unknown> = {
  '/api/overview': {
    account_count: 3,
    transaction_count: 150,
    category_count: 20,
    total_balance: '21770.11',
    currency: 'AUD',
  },
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
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url =
          typeof input === 'string'
            ? new URL(input, 'http://localhost')
            : input instanceof URL
              ? input
              : new URL(input.url)
        const path = `${url.pathname}${url.search}`
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(responses[path]),
        } as Response)
      }),
    )

    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Your financial overview' })).toBeVisible()
    expect(screen.getAllByText('Everyday Account')[0]).toBeVisible()
    expect(screen.getByText('Woolworths')).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Recent 1 transactions' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Go to transactions' })).toHaveAttribute(
      'href',
      '/transactions',
    )

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Filter recent transactions by Everyday Account',
      }),
    )

    expect(await screen.findByText('Account-filtered purchase')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Show all accounts' })).toBeVisible()
  })
})
