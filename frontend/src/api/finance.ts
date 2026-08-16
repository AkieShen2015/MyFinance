export interface Overview {
  account_count: number
  transaction_count: number
  category_count: number
  total_balance: string
  currency: string
}

export interface Account {
  id: string
  institution_name: string
  account_name: string
  account_type: string
  masked_account_number: string | null
  currency: string
  current_balance: string
  available_balance: string | null
  connection_status: string
  last_sync_at: string | null
}

export interface Transaction {
  id: string
  transaction_date: string
  institution_name: string
  account_name: string
  merchant_name: string | null
  description: string
  category_name: string | null
  tags: string[]
  transaction_type: string
  amount: string
  currency: string
  pending: boolean
}

export interface TransactionPage {
  items: Transaction[]
  total: number
  limit: number
  offset: number
}

export interface Category {
  id: string
  name: string
  parent_id: string | null
  type: string
  icon: string | null
  is_system: boolean
}

async function getJson<T>(path: string): Promise<T> {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  const response = await fetch(`${apiBaseUrl}${path}`, { credentials: 'include' })
  if (!response.ok) {
    const message =
      response.status === 503
        ? 'Development data is not seeded.'
        : 'Unable to load finance data.'
    throw new Error(message)
  }
  return (await response.json()) as T
}

export const financeApi = {
  overview: () => getJson<Overview>('/api/overview'),
  accounts: () => getJson<Account[]>('/api/accounts'),
  categories: () => getJson<Category[]>('/api/categories'),
  transactions: (query = 'limit=15') =>
    getJson<TransactionPage>(`/api/transactions?${query}`),
}
