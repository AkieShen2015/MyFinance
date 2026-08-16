import { render, screen } from '@testing-library/react'
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
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('renders seeded accounts and recent transactions', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = new URL(String(input), 'http://localhost')
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
    expect(screen.getByText('Showing 1 of 150')).toBeVisible()
  })
})
