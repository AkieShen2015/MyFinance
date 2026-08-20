export interface Overview {
  account_count: number
  transaction_count: number
  category_count: number
  total_balance: string
  currency: string
}

export interface Account {
  id: string
  institution_id: string
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
  account_id: string
  category_id: string | null
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
  account_id: string | null
  type: string
  icon: string | null
  is_system: boolean
}

export interface DashboardSummary {
  date_from: string
  date_to: string
  total_income: string
  total_expenses: string
  net_cash_flow: string
  total_account_balance: string
  currency: string
}

export interface ExpenseCategory {
  category: string
  amount: string
  percentage: string
}

export interface IncomeExpenseMonth {
  month: string
  income: string
  expenses: string
}

export interface AnalyticsComparison {
  current: string
  previous: string
  change_amount: string
  change_percentage: string | null
}

export interface AnalyticsReport {
  date_from: string
  date_to: string
  previous_date_from: string
  previous_date_to: string
  income: AnalyticsComparison
  expenses: AnalyticsComparison
  net_cash_flow: AnalyticsComparison
  savings_rate: string | null
  category_trends: Array<{
    category: string
    current_amount: string
    previous_amount: string
    change_amount: string
    change_percentage: string | null
    monthly: Array<{ month: string; amount: string }>
  }>
  top_merchants: Array<{
    merchant: string
    amount: string
    percentage: string
    transaction_count: number
  }>
  recurring_payments: Array<{
    merchant: string
    average_amount: string
    occurrences: number
    cadence_days: number
    next_expected_date: string
    confidence: string
  }>
  anomalies: Array<{
    transaction_id: string
    date: string
    merchant: string
    category: string
    amount: string
    baseline_amount: string
    multiple: string
  }>
  insights: Array<{
    kind: string
    title: string
    message: string
    impact_amount: string
    confidence: string
  }>
  ai_payload: {
    period_start: string
    period_end: string
    expense_change_amount: string
    expense_change_percentage: string | null
    top_category_changes: Array<Record<string, string>>
    recurring_total: string
    anomaly_count: number
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

async function getJson<T>(path: string): Promise<T> {
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

async function patchJson(path: string, body: unknown): Promise<void> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    body: JSON.stringify(body),
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    method: 'PATCH',
  })
  if (!response.ok) throw new Error('Unable to update the transaction category.')
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    body: JSON.stringify(body),
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  })
  if (!response.ok) throw new Error('Unable to create the category.')
  return (await response.json()) as T
}

export const financeApi = {
  overview: () => getJson<Overview>('/api/overview'),
  accounts: () => getJson<Account[]>('/api/accounts'),
  categories: () => getJson<Category[]>('/api/categories'),
  dashboardSummary: (query: string) =>
    getJson<DashboardSummary>(`/api/dashboard/summary?${query}`),
  expensesByCategory: (query: string) =>
    getJson<ExpenseCategory[]>(`/api/dashboard/expenses-by-category?${query}`),
  incomeVsExpenses: (query: string) =>
    getJson<IncomeExpenseMonth[]>(`/api/dashboard/income-vs-expenses?${query}`),
  analyticsReport: (query: string) =>
    getJson<AnalyticsReport>(`/api/analytics/report?${query}`),
  createCategory: (accountId: string, name: string, type: string) =>
    postJson<Category>('/api/categories', {
      account_id: accountId,
      name,
      type,
    }),
  transactions: (query = 'limit=15') =>
    getJson<TransactionPage>(`/api/transactions?${query}`),
  updateTransactionCategory: (
    transactionId: string,
    categoryId: string,
    applyToSimilar: boolean,
  ) =>
    patchJson(`/api/transactions/${transactionId}/category`, {
      apply_to_similar: applyToSimilar,
      category_id: categoryId,
    }),
}
