import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  financeApi,
  type Account,
  type Category,
  type Transaction,
  type TransactionPage,
} from '../api/finance'
import { AnalyticsPage } from './AnalyticsPage'
import { presetPeriod, type PeriodPreset } from './datePeriods'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

const chartColours = ['#047857', '#0f766e', '#0891b2', '#2563eb', '#7c3aed', '#c2410c']

function money(value: string, currency = 'AUD') {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value))
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-2 text-xs text-slate-500">{detail}</p>
    </article>
  )
}

const institutionThemes = [
  { match: ['anz'], background: 'from-[#004165] via-[#0072ac] to-[#00a6ca]', text: 'text-white' },
  {
    match: ['commonwealth', 'commbank', 'cba'],
    background: 'from-[#ffcc00] via-[#ffd633] to-[#f6b800]',
    text: 'text-slate-950',
  },
  { match: ['westpac'], background: 'from-[#9d001b] via-[#d5002b] to-[#f43f5e]', text: 'text-white' },
  { match: ['nab', 'national australia'], background: 'from-[#7a0019] via-[#b00020] to-[#e31837]', text: 'text-white' },
  { match: ['ing'], background: 'from-[#e65300] via-[#ff6200] to-[#ff8a00]', text: 'text-white' },
  { match: ['hsbc'], background: 'from-[#7f0019] via-[#db0011] to-[#ff3344]', text: 'text-white' },
  { match: ['bankwest'], background: 'from-[#4a136b] via-[#6d2077] to-[#a855f7]', text: 'text-white' },
  { match: ['st.george', 'st george'], background: 'from-[#006a4d] via-[#009b77] to-[#35b98f]', text: 'text-white' },
  { match: ['latitude'], background: 'from-[#102a72] via-[#3155a6] to-[#5878d8]', text: 'text-white' },
  { match: ['macquarie'], background: 'from-slate-950 via-slate-800 to-slate-600', text: 'text-white' },
  { match: ['suncorp'], background: 'from-[#006b54] via-[#008c72] to-[#38a169]', text: 'text-white' },
  { match: ['bendigo', 'adelaide bank'], background: 'from-[#005596] via-[#0072bc] to-[#29a3dc]', text: 'text-white' },
  { match: ['boq', 'bank of queensland'], background: 'from-[#003b70] via-[#005daa] to-[#e31b23]', text: 'text-white' },
  { match: ['ubank'], background: 'from-[#27104e] via-[#5a2a83] to-[#8d4dc4]', text: 'text-white' },
] as const

function institutionTheme(institutionName: string) {
  const normalisedName = institutionName.toLowerCase()
  return (
    institutionThemes.find(({ match }) =>
      match.some((name) => normalisedName.includes(name)),
    ) ?? {
      background: 'from-emerald-900 via-emerald-700 to-teal-500',
      text: 'text-white',
    }
  )
}

function leafCategories(categories: Category[]) {
  const parentIds = new Set(
    categories
      .map((category) => category.parent_id)
      .filter((parentId): parentId is string => parentId !== null),
  )
  return categories
    .filter(
      (category) =>
        !parentIds.has(category.id) &&
        category.name.toLowerCase() !== 'needs review',
    )
    .sort((first, second) => {
      const firstIsOther = first.name.localeCompare('Other', 'en-AU', {
        sensitivity: 'base',
      }) === 0
      const secondIsOther = second.name.localeCompare('Other', 'en-AU', {
        sensitivity: 'base',
      }) === 0
      if (firstIsOther && secondIsOther) return 0
      if (firstIsOther) return 1
      if (secondIsOther) return -1
      return first.name.localeCompare(second.name, 'en-AU', { sensitivity: 'base' })
    })
}

function AccountCard({
  account,
  selected,
  onSelect,
}: {
  account: Account
  selected: boolean
  onSelect: () => void
}) {
  const theme = institutionTheme(account.institution_name)
  const initials = account.institution_name
    .split(/\s+/)
    .map((word) => word[0])
    .join('')
    .slice(0, 3)
    .toUpperCase()

  return (
    <button
      aria-label={`Toggle ${account.account_name} in dashboard filters`}
      aria-pressed={selected}
      className={`relative min-h-56 w-full cursor-pointer overflow-hidden rounded-3xl bg-gradient-to-br ${theme.background} ${theme.text} p-6 text-left shadow-lg outline-none transition hover:-translate-y-1 hover:shadow-xl focus-visible:ring-4 focus-visible:ring-emerald-300 ${selected ? 'ring-4 ring-emerald-400 ring-offset-2' : ''}`}
      onClick={onSelect}
      type="button"
    >
      <div className="absolute -right-12 -top-16 h-44 w-44 rounded-full bg-white/15" />
      <div className="absolute -bottom-20 right-10 h-40 w-40 rounded-full bg-black/10" />
      <div className="relative flex h-full flex-col justify-between gap-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-lg font-bold tracking-tight">{account.institution_name}</p>
            <p className="mt-1 text-sm opacity-75">{account.account_name}</p>
          </div>
          <span className="grid h-10 min-w-10 place-items-center rounded-xl bg-white/20 px-2 text-xs font-black tracking-wider backdrop-blur-sm">
            {initials}
          </span>
        </div>
        <div>
          <div className="mb-4 h-7 w-10 rounded-md bg-gradient-to-br from-amber-100 to-amber-400 shadow-inner" />
          <p className="font-mono text-sm tracking-[0.16em] opacity-85">
            {account.masked_account_number ?? 'Masked number unavailable'}
          </p>
          <div className="mt-4 flex items-end justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wider opacity-65">Current balance</p>
              <p className="mt-1 text-2xl font-semibold">
                {money(account.current_balance, account.currency)}
              </p>
            </div>
            <div className="text-right text-xs font-medium capitalize opacity-80">
              <p>{account.account_type.replace('_', ' ')}</p>
              <p>{account.connection_status}</p>
            </div>
          </div>
        </div>
      </div>
    </button>
  )
}

function TransactionRow({
  transaction,
  categories,
  categoryUpdating = false,
  detailed = false,
  onCategoryChange,
  onCreateCustomCategory,
}: {
  transaction: Transaction
  categories?: Category[]
  categoryUpdating?: boolean
  detailed?: boolean
  onCategoryChange?: (categoryId: string) => void
  onCreateCustomCategory?: (name: string) => void
}) {
  const [customCategoryName, setCustomCategoryName] = useState('')
  const expense = Number(transaction.amount) < 0
  return (
    <tr className="border-t border-slate-100">
      <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
        {transaction.transaction_date}
      </td>
      {detailed ? (
        <>
          <td className="px-5 py-4 text-sm text-slate-600">
            {transaction.institution_name}
          </td>
          <td className="px-5 py-4 text-sm text-slate-600">
            {transaction.account_name}
          </td>
        </>
      ) : null}
      <td className="px-5 py-4">
        <p className="font-medium text-slate-900">
          {transaction.merchant_name ?? transaction.description}
        </p>
        {!detailed ||
        (transaction.merchant_name !== null &&
          transaction.merchant_name !== transaction.description) ? (
          <p className="mt-0.5 text-xs text-slate-500">
            {detailed
              ? transaction.description
              : `${transaction.institution_name} · ${transaction.account_name}`}
          </p>
        ) : null}
      </td>
      <td className="px-5 py-4 text-sm text-slate-600">
        {categories && onCategoryChange ? (
          <div>
            <select
              aria-label={`Category for ${transaction.merchant_name ?? transaction.description}`}
              className="max-w-44 cursor-pointer rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-emerald-600 disabled:cursor-wait disabled:opacity-60"
              disabled={categoryUpdating}
              onChange={(event) => {
                onCategoryChange(event.target.value)
              }}
              value={transaction.category_id ?? ''}
            >
              <option disabled value="">Select category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            {transaction.category_name === 'Other' ? (
              <div className="mt-2">
                <p className="text-xs font-medium text-amber-700">Needs review</p>
                {onCreateCustomCategory ? (
                  <form
                    className="mt-2 flex min-w-64 gap-2"
                    onSubmit={(event) => {
                      event.preventDefault()
                      const name = customCategoryName.trim()
                      if (name) onCreateCustomCategory(name)
                    }}
                  >
                    <input
                      aria-label={`New category for ${transaction.description}`}
                      className="min-w-0 flex-1 rounded-lg border border-slate-300 px-2 py-1.5 text-xs outline-none focus:border-emerald-600"
                      disabled={categoryUpdating}
                      maxLength={100}
                      onChange={(event) => {
                        setCustomCategoryName(event.target.value)
                      }}
                      placeholder="New account category"
                      value={customCategoryName}
                    />
                    <button
                      className="cursor-pointer rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-white disabled:cursor-wait disabled:opacity-60"
                      disabled={categoryUpdating || customCategoryName.trim().length === 0}
                      type="submit"
                    >
                      Add
                    </button>
                  </form>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : (
          transaction.category_name ?? 'Other'
        )}
      </td>
      <td
        className={`whitespace-nowrap px-5 py-4 text-right font-semibold ${
          expense ? 'text-slate-900' : 'text-emerald-700'
        }`}
      >
        {money(transaction.amount, transaction.currency)}
      </td>
    </tr>
  )
}

function OverviewPage() {
  const accountScroller = useRef<HTMLDivElement>(null)
  const [accountsExpanded, setAccountsExpanded] = useState(false)
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([])
  const [periodPreset, setPeriodPreset] = useState<PeriodPreset>('this_month')
  const [dateFrom, setDateFrom] = useState(() => presetPeriod('this_month').dateFrom)
  const [dateTo, setDateTo] = useState(() => presetPeriod('this_month').dateTo)
  const accounts = useQuery({ queryKey: ['accounts'], queryFn: financeApi.accounts })
  const analyticsParams = new URLSearchParams({ date_from: dateFrom, date_to: dateTo })
  selectedAccountIds.forEach((accountId) => {
    analyticsParams.append('account_id', accountId)
  })
  const analyticsQuery = analyticsParams.toString()
  const accountScopeKey = selectedAccountIds.join(',')
  const summary = useQuery({
    queryKey: ['dashboard-summary', dateFrom, dateTo, accountScopeKey],
    queryFn: () => financeApi.dashboardSummary(analyticsQuery),
    placeholderData: (previousData) => previousData,
  })
  const expenses = useQuery({
    queryKey: ['dashboard-expenses', dateFrom, dateTo, accountScopeKey],
    queryFn: () => financeApi.expensesByCategory(analyticsQuery),
    placeholderData: (previousData) => previousData,
  })
  const trend = useQuery({
    queryKey: ['dashboard-trend', dateFrom, dateTo, accountScopeKey],
    queryFn: () => financeApi.incomeVsExpenses(analyticsQuery),
    placeholderData: (previousData) => previousData,
  })
  const recentTransactionsQuery = new URLSearchParams({ limit: '15' })
  selectedAccountIds.forEach((accountId) => {
    recentTransactionsQuery.append('account_id', accountId)
  })
  const transactions = useQuery({
    queryKey: ['transactions', 15, accountScopeKey],
    queryFn: () => financeApi.transactions(recentTransactionsQuery.toString()),
    placeholderData: (previousData) => previousData,
  })

  if (
    accounts.isPending ||
    transactions.isPending ||
    summary.isPending ||
    expenses.isPending ||
    trend.isPending
  ) {
    return (
      <main className="grid min-h-screen place-items-center text-slate-600">
        Loading mock finance data…
      </main>
    )
  }

  if (
    accounts.isError ||
    transactions.isError ||
    summary.isError ||
    expenses.isError ||
    trend.isError
  ) {
    const error =
      accounts.error ?? transactions.error ?? summary.error ?? expenses.error ?? trend.error
    return (
      <main className="grid min-h-screen place-items-center px-6">
        <section className="max-w-lg rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-slate-950">Finance data is unavailable</h1>
          <p className="mt-3 text-slate-600">{error?.message ?? 'Unable to load finance data.'}</p>
          <p className="mt-3 text-sm text-slate-500">
            Restart the backend to apply migrations and seed the mock provider.
          </p>
        </section>
      </main>
    )
  }

  const selectedAccounts = accounts.data.filter((account) =>
    selectedAccountIds.includes(account.id),
  )
  const institutions = Array.from(
    new Map(
      accounts.data.map((account) => [
        account.institution_id,
        { id: account.institution_id, name: account.institution_name },
      ]),
    ).values(),
  ).sort((first, second) => first.name.localeCompare(second.name, 'en-AU'))
  const toggleAccount = (accountId: string) => {
    setSelectedAccountIds((currentIds) => {
      const nextIds = new Set(currentIds)
      if (nextIds.has(accountId)) nextIds.delete(accountId)
      else nextIds.add(accountId)
      return accounts.data
        .filter((account) => nextIds.has(account.id))
        .map((account) => account.id)
    })
  }
  const categoryChartData = expenses.data.map((item) => ({
    amount: Number(item.amount),
    category: item.category,
    percentage: Number(item.percentage),
  }))
  const trendChartData = trend.data.map((item) => ({
    expenses: Number(item.expenses),
    income: Number(item.income),
    month: new Intl.DateTimeFormat('en-AU', { month: 'short', year: '2-digit' }).format(
      new Date(`${item.month}T00:00:00`),
    ),
  }))
  const scrollAccounts = (direction: -1 | 1) => {
    accountScroller.current?.scrollBy({
      behavior: 'smooth',
      left: direction * accountScroller.current.clientWidth * 0.8,
    })
  }

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">
              Personal Finance
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
              Your financial overview
            </h1>
            <p className="mt-2 text-slate-600">Phase 4 · cash-flow analytics and trends</p>
          </div>
          <span className="w-fit rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-800">
            Mock data — no bank connected
          </span>
        </header>
        <nav className="mt-5 flex gap-4 text-sm font-medium">
          <span className="text-emerald-700">Overview</span>
          <Link className="text-slate-600 hover:text-emerald-700" to="/transactions">
            Transactions
          </Link>
          <Link className="text-slate-600 hover:text-emerald-700" to="/analytics">
            Analytics
          </Link>
        </nav>

        <section
          aria-label="Dashboard period"
          className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="grid gap-4 md:grid-cols-[minmax(180px,1fr)_minmax(160px,1fr)_minmax(160px,1fr)]">
            <label className="text-sm font-medium text-slate-700">
              Period
              <select
                className="mt-1 block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-600"
                onChange={(event) => {
                  const nextPreset = event.target.value as PeriodPreset
                  setPeriodPreset(nextPreset)
                  if (nextPreset !== 'custom') {
                    const nextPeriod = presetPeriod(nextPreset)
                    setDateFrom(nextPeriod.dateFrom)
                    setDateTo(nextPeriod.dateTo)
                  }
                }}
                value={periodPreset}
              >
                <option value="this_month">This month</option>
                <option value="last_month">Last month</option>
                <option value="last_3_months">Last 3 months</option>
                <option value="last_6_months">Last 6 months</option>
                <option value="last_1_year">Last 1 year</option>
                <option value="this_year">This year</option>
                <option value="custom">Custom date range</option>
              </select>
            </label>
            <label className="text-sm font-medium text-slate-700">
              From
              <input
                className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none focus:border-emerald-600 disabled:bg-slate-100"
                disabled={periodPreset !== 'custom'}
                max={dateTo}
                onChange={(event) => {
                  if (event.target.value) setDateFrom(event.target.value)
                }}
                type="date"
                value={dateFrom}
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              To
              <input
                className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 outline-none focus:border-emerald-600 disabled:bg-slate-100"
                disabled={periodPreset !== 'custom'}
                min={dateFrom}
                onChange={(event) => {
                  if (event.target.value) setDateTo(event.target.value)
                }}
                type="date"
                value={dateTo}
              />
            </label>
          </div>
          <div className="mt-4 border-t border-slate-100 pt-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
              <label className="min-w-56 text-sm font-medium text-slate-700">
                Add an institution
                <select
                  aria-label="Add institution accounts"
                  className="mt-1 block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2.5 outline-none focus:border-emerald-600"
                  onChange={(event) => {
                    const institutionId = event.target.value
                    if (!institutionId) return
                    const institutionAccountIds = accounts.data
                      .filter((account) => account.institution_id === institutionId)
                      .map((account) => account.id)
                    setSelectedAccountIds((currentIds) => {
                      const nextIds = new Set([...currentIds, ...institutionAccountIds])
                      return accounts.data
                        .filter((account) => nextIds.has(account.id))
                        .map((account) => account.id)
                    })
                  }}
                  value=""
                >
                  <option value="">Choose institution…</option>
                  {institutions.map((institution) => (
                    <option key={institution.id} value={institution.id}>
                      {institution.name}
                    </option>
                  ))}
                </select>
              </label>
              <details className="relative min-w-64">
                <summary className="cursor-pointer list-none rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  {selectedAccountIds.length === 0
                    ? `All ${String(accounts.data.length)} accounts`
                    : `${String(selectedAccountIds.length)} of ${String(accounts.data.length)} accounts selected`}
                </summary>
                <div className="absolute left-0 z-30 mt-2 w-full min-w-80 rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
                  <div className="mb-2 flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
                    <button
                      className="cursor-pointer text-xs font-semibold text-emerald-700 hover:text-emerald-900"
                      onClick={() => {
                        setSelectedAccountIds(accounts.data.map((account) => account.id))
                      }}
                      type="button"
                    >
                      Select all
                    </button>
                    <button
                      className="cursor-pointer text-xs font-semibold text-slate-600 hover:text-slate-900"
                      onClick={() => {
                        setSelectedAccountIds([])
                      }}
                      type="button"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="max-h-72 space-y-1 overflow-y-auto">
                    {accounts.data.map((account) => (
                      <label
                        className="flex cursor-pointer items-start gap-2 rounded-lg px-2 py-2 text-sm hover:bg-slate-50"
                        key={account.id}
                      >
                        <input
                          checked={selectedAccountIds.includes(account.id)}
                          className="mt-0.5 h-4 w-4 accent-emerald-700"
                          onChange={() => {
                            toggleAccount(account.id)
                          }}
                          type="checkbox"
                        />
                        <span>
                          <span className="block font-medium text-slate-800">
                            {account.account_name}
                          </span>
                          <span className="block text-xs text-slate-500">
                            {account.institution_name} · {account.masked_account_number}
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </details>
              <button
                className={`w-fit rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50 ${selectedAccountIds.length === 0 ? 'invisible' : 'cursor-pointer'}`}
                disabled={selectedAccountIds.length === 0}
                onClick={() => {
                  setSelectedAccountIds([])
                }}
                type="button"
              >
                Clear selection
              </button>
            </div>
            <div
              className="mt-3 flex min-h-8 flex-wrap items-center gap-2"
              aria-label="Selected accounts"
            >
              {selectedAccounts.length > 0 ? (
                selectedAccounts.map((account) => (
                  <button
                    aria-label={`Remove ${account.account_name} from dashboard filter`}
                    className="cursor-pointer rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-800 hover:bg-emerald-100"
                    key={account.id}
                    onClick={() => {
                      toggleAccount(account.id)
                    }}
                    type="button"
                  >
                    {account.institution_name} · {account.account_name} ×
                  </button>
                ))
              ) : (
                <p className="text-xs text-slate-500">
                  Analytics and recent activity currently include every account.
                </p>
              )}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Summary">
          <SummaryCard
            label="Total income"
            value={money(summary.data.total_income, summary.data.currency)}
            detail={`${dateFrom} to ${dateTo}`}
          />
          <SummaryCard
            label="Total expenses"
            value={money(summary.data.total_expenses, summary.data.currency)}
            detail="Posted expenses less refunds"
          />
          <SummaryCard
            label="Net cash flow"
            value={money(summary.data.net_cash_flow, summary.data.currency)}
            detail="Income minus expenses"
          />
          <SummaryCard
            label="Total account balance"
            value={money(summary.data.total_account_balance, summary.data.currency)}
            detail={
              selectedAccountIds.length === 0
                ? `Across all ${String(accounts.data.length)} mock accounts`
                : `Across ${String(selectedAccountIds.length)} selected ${selectedAccountIds.length === 1 ? 'account' : 'accounts'}`
            }
          />
        </section>

        <section className="mt-8 grid gap-6 xl:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Spending composition</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-950">Expenses by category</h2>
            {categoryChartData.length === 0 ? (
              <p className="py-16 text-center text-slate-500">No expenses in this period.</p>
            ) : (
              <div className="mt-5 grid items-center gap-4 sm:grid-cols-[minmax(0,1fr)_minmax(180px,0.8fr)]">
                <div className="h-72" aria-label="Expense category chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryChartData}
                        dataKey="amount"
                        innerRadius={62}
                        nameKey="category"
                        outerRadius={100}
                        paddingAngle={2}
                      >
                        {categoryChartData.map((item, index) => (
                          <Cell
                            fill={chartColours[index % chartColours.length]}
                            key={item.category}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <ul className="max-h-72 space-y-3 overflow-y-auto pr-2">
                  {categoryChartData.map((item, index) => (
                    <li className="flex items-center justify-between gap-3 text-sm" key={item.category}>
                      <span className="flex min-w-0 items-center gap-2 text-slate-700">
                        <span
                          className="h-3 w-3 shrink-0 rounded-full"
                          style={{ backgroundColor: chartColours[index % chartColours.length] }}
                        />
                        <span className="truncate">{item.category}</span>
                      </span>
                      <span className="whitespace-nowrap font-medium text-slate-900">
                        {money(String(item.amount))} · {item.percentage.toFixed(1)}%
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Monthly movement</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-950">Income vs expenses</h2>
            <div className="mt-5 h-72" aria-label="Income versus expenses chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendChartData} margin={{ left: 4, right: 4, top: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" />
                  <YAxis width={70} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="income" fill="#047857" name="Income" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="expenses" fill="#c2410c" name="Expenses" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>
        </section>

        <section className="mt-10">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Connected institutions</p>
              <h2 className="text-2xl font-semibold text-slate-950">Accounts</h2>
              <p className="mt-1 text-sm text-slate-500">
                Select one or more accounts to filter analytics and recent activity.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {accounts.data.length > 3 ? (
                <button
                  className="cursor-pointer rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
                  onClick={() => {
                    setAccountsExpanded((expanded) => !expanded)
                  }}
                  type="button"
                >
                  {accountsExpanded ? 'Collapse cards' : 'Show all cards'}
                </button>
              ) : null}
            </div>
          </div>
          <div className="relative">
            {!accountsExpanded && accounts.data.length > 3 ? (
              <button
                aria-label="Scroll accounts left"
                className="absolute left-2 top-1/2 z-10 grid h-11 w-11 -translate-y-1/2 cursor-pointer place-items-center rounded-full border border-slate-200 bg-white/95 text-2xl text-slate-800 shadow-lg backdrop-blur hover:bg-white sm:-left-5"
                onClick={() => {
                  scrollAccounts(-1)
                }}
                type="button"
              >
                ←
              </button>
            ) : null}
            <div
              className={
                accountsExpanded
                  ? 'grid gap-4 md:grid-cols-2 xl:grid-cols-3'
                  : 'flex snap-x snap-mandatory gap-4 overflow-x-auto pb-4'
              }
              ref={accountScroller}
            >
              {accounts.data.map((account) => (
                <div
                  className={
                    accountsExpanded
                      ? 'min-w-0'
                      : 'w-[88%] shrink-0 snap-start sm:w-[48%] xl:w-[32%]'
                  }
                  key={account.id}
                >
                  <AccountCard
                    account={account}
                    onSelect={() => {
                      toggleAccount(account.id)
                    }}
                    selected={selectedAccountIds.includes(account.id)}
                  />
                </div>
              ))}
            </div>
            {!accountsExpanded && accounts.data.length > 3 ? (
              <button
                aria-label="Scroll accounts right"
                className="absolute right-2 top-1/2 z-10 grid h-11 w-11 -translate-y-1/2 cursor-pointer place-items-center rounded-full border border-slate-200 bg-white/95 text-2xl text-slate-800 shadow-lg backdrop-blur hover:bg-white sm:-right-5"
                onClick={() => {
                  scrollAccounts(1)
                }}
                type="button"
              >
                →
              </button>
            ) : null}
          </div>
        </section>

        <section className="mt-10 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Latest activity</p>
              <h2 className="text-2xl font-semibold text-slate-950">
                Recent {transactions.data.items.length} transactions
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                {selectedAccounts.length === 0
                  ? 'Across all accounts'
                  : selectedAccounts.length === 1 && selectedAccounts[0]
                    ? `${selectedAccounts[0].institution_name} · ${selectedAccounts[0].account_name}`
                    : `Across ${String(selectedAccounts.length)} selected accounts`}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedAccountIds.length > 0 ? (
                <button
                  className="cursor-pointer rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  onClick={() => {
                    setSelectedAccountIds([])
                  }}
                  type="button"
                >
                  Show all accounts
                </button>
              ) : null}
              <Link
                className="w-fit rounded-xl bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800"
                to="/transactions"
              >
                Go to transactions
              </Link>
            </div>
          </div>
          {transactions.data.items.length === 0 ? (
            <p className="border-t border-slate-100 px-5 py-10 text-center text-slate-500">
              No transactions found.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Date</th>
                    <th className="px-5 py-3">Merchant</th>
                    <th className="px-5 py-3">Category</th>
                    <th className="px-5 py-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.data.items.map((transaction) => (
                    <TransactionRow key={transaction.id} transaction={transaction} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}

function TransactionsPage() {
  const queryClient = useQueryClient()
  const pageSize = 50
  const [draftSearch, setDraftSearch] = useState('')
  const [search, setSearch] = useState('')
  const [institutionId, setInstitutionId] = useState('')
  const [accountId, setAccountId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [transactionType, setTransactionType] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [amountMin, setAmountMin] = useState('')
  const [amountMax, setAmountMax] = useState('')
  const [sort, setSort] = useState('transaction_date:desc')
  const [rememberCategory, setRememberCategory] = useState(true)
  const [page, setPage] = useState(0)
  const accounts = useQuery({ queryKey: ['accounts'], queryFn: financeApi.accounts })
  const categories = useQuery({ queryKey: ['categories'], queryFn: financeApi.categories })
  const query = new URLSearchParams({
    limit: String(pageSize),
    offset: String(page * pageSize),
  })
  if (search) query.set('search', search)
  if (institutionId) query.set('institution_id', institutionId)
  if (accountId) query.set('account_id', accountId)
  if (categoryId) query.set('category_id', categoryId)
  if (transactionType) query.set('transaction_type', transactionType)
  if (dateFrom) query.set('date_from', dateFrom)
  if (dateTo) query.set('date_to', dateTo)
  if (amountMin) query.set('amount_min', amountMin)
  if (amountMax) query.set('amount_max', amountMax)
  const [sortBy = 'transaction_date', sortOrder = 'desc'] = sort.split(':')
  query.set('sort_by', sortBy)
  query.set('sort_order', sortOrder)
  const transactionQueryKey = [
    'transactions-page',
    search,
    institutionId,
    accountId,
    categoryId,
    transactionType,
    dateFrom,
    dateTo,
    amountMin,
    amountMax,
    sort,
    page,
  ] as const
  const transactions = useQuery({
    queryKey: transactionQueryKey,
    queryFn: () => financeApi.transactions(query.toString()),
  })
  const selectableCategories = leafCategories(categories.data ?? [])
  const categoryMutation = useMutation({
    mutationFn: ({ transactionId, categoryId }: { transactionId: string; categoryId: string }) =>
      financeApi.updateTransactionCategory(
        transactionId,
        categoryId,
        rememberCategory,
      ),
    onSuccess: async (_, variables) => {
      const selectedCategory = selectableCategories.find(
        (category) => category.id === variables.categoryId,
      )
      queryClient.setQueryData<TransactionPage>(transactionQueryKey, (currentPage) => {
        if (!currentPage) return currentPage
        if (categoryId && categoryId !== variables.categoryId) {
          return {
            ...currentPage,
            items: currentPage.items.filter(
              (transaction) => transaction.id !== variables.transactionId,
            ),
            total: Math.max(0, currentPage.total - 1),
          }
        }
        return {
          ...currentPage,
          items: currentPage.items.map((transaction) =>
            transaction.id === variables.transactionId
              ? {
                  ...transaction,
                  category_id: variables.categoryId,
                  category_name: selectedCategory?.name ?? transaction.category_name,
                }
              : transaction,
          ),
        }
      })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['transactions'] }),
        queryClient.invalidateQueries({ queryKey: ['transactions-page'] }),
      ])
    },
  })
  const customCategoryMutation = useMutation({
    mutationFn: async ({ transaction, name }: { transaction: Transaction; name: string }) => {
      const category = await financeApi.createCategory(
        transaction.account_id,
        name,
        transaction.transaction_type === 'income' ? 'income' : 'expense',
      )
      await financeApi.updateTransactionCategory(
        transaction.id,
        category.id,
        rememberCategory,
      )
      return category
    },
    onSuccess: async (category, variables) => {
      queryClient.setQueryData<Category[]>(['categories'], (currentCategories) =>
        currentCategories?.some((item) => item.id === category.id)
          ? currentCategories
          : [...(currentCategories ?? []), category],
      )
      queryClient.setQueryData<TransactionPage>(transactionQueryKey, (currentPage) => {
        if (!currentPage) return currentPage
        if (categoryId && categoryId !== category.id) {
          return {
            ...currentPage,
            items: currentPage.items.filter(
              (transaction) => transaction.id !== variables.transaction.id,
            ),
            total: Math.max(0, currentPage.total - 1),
          }
        }
        return {
          ...currentPage,
          items: currentPage.items.map((transaction) =>
            transaction.id === variables.transaction.id
              ? {
                  ...transaction,
                  category_id: category.id,
                  category_name: category.name,
                }
              : transaction,
          ),
        }
      })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['categories'] }),
        queryClient.invalidateQueries({ queryKey: ['transactions'] }),
        queryClient.invalidateQueries({ queryKey: ['transactions-page'] }),
      ])
    },
  })
  const institutions = Array.from(
    new Map(
      (accounts.data ?? []).map((account) => [
        account.institution_id,
        account.institution_name,
      ]),
    ),
  ).sort((first, second) => first[1].localeCompare(second[1]))

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-7xl">
        <nav className="mb-8 flex gap-4 text-sm font-medium">
          <Link className="text-slate-600 hover:text-emerald-700" to="/">Overview</Link>
          <span className="text-emerald-700">Transactions</span>
          <Link className="text-slate-600 hover:text-emerald-700" to="/analytics">Analytics</Link>
        </nav>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">Transactions</h1>
        <p className="mt-2 text-slate-600">Search all accounts by merchant or description.</p>
        <form
          className="mt-6 flex max-w-5xl flex-col gap-3 sm:flex-row"
          onSubmit={(event) => {
            event.preventDefault()
            setPage(0)
            setSearch(draftSearch.trim())
          }}
        >
          <input
            aria-label="Search transactions"
            className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 outline-none focus:border-emerald-600"
            onChange={(event) => {
              setDraftSearch(event.target.value)
            }}
            placeholder="Search Woolworths, rent, Netflix…"
            value={draftSearch}
          />
          <select
            aria-label="Filter by bank"
            className="cursor-pointer rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-slate-700 outline-none focus:border-emerald-600"
            disabled={accounts.isPending || accounts.isError}
            onChange={(event) => {
              setPage(0)
              setInstitutionId(event.target.value)
              setAccountId('')
            }}
            value={institutionId}
          >
            <option value="">All banks</option>
            {institutions.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
          <select
            aria-label="Filter by category"
            className="cursor-pointer rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-slate-700 outline-none focus:border-emerald-600"
            disabled={categories.isPending || categories.isError}
            onChange={(event) => {
              setPage(0)
              setCategoryId(event.target.value)
            }}
            value={categoryId}
          >
            <option value="">All categories</option>
            {selectableCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
          <button className="cursor-pointer rounded-xl bg-emerald-700 px-5 py-2.5 font-medium text-white hover:bg-emerald-800" type="submit">Search</button>
        </form>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="text-xs font-medium text-slate-600">
            Account
            <select
              className="mt-1 block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-emerald-600"
              onChange={(event) => {
                setPage(0)
                setAccountId(event.target.value)
              }}
              value={accountId}
            >
              <option value="">All accounts</option>
              {(accounts.data ?? [])
                .filter(
                  (account) =>
                    !institutionId || account.institution_id === institutionId,
                )
                .map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.institution_name} · {account.account_name}
                  </option>
                ))}
            </select>
          </label>
          <label className="text-xs font-medium text-slate-600">
            Type
            <select
              className="mt-1 block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-emerald-600"
              onChange={(event) => {
                setPage(0)
                setTransactionType(event.target.value)
              }}
              value={transactionType}
            >
              <option value="">Income and expenses</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="refund">Refund</option>
              <option value="transfer">Transfer</option>
            </select>
          </label>
          <label className="text-xs font-medium text-slate-600">
            Date from
            <input
              className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
              onChange={(event) => {
                setPage(0)
                setDateFrom(event.target.value)
              }}
              type="date"
              value={dateFrom}
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            Date to
            <input
              className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
              onChange={(event) => {
                setPage(0)
                setDateTo(event.target.value)
              }}
              type="date"
              value={dateTo}
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            Minimum amount
            <input
              className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
              onChange={(event) => {
                setPage(0)
                setAmountMin(event.target.value)
              }}
              placeholder="e.g. -500"
              step="0.01"
              type="number"
              value={amountMin}
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            Maximum amount
            <input
              className="mt-1 block w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-600"
              onChange={(event) => {
                setPage(0)
                setAmountMax(event.target.value)
              }}
              placeholder="e.g. 500"
              step="0.01"
              type="number"
              value={amountMax}
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            Sort by
            <select
              className="mt-1 block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-emerald-600"
              onChange={(event) => {
                setPage(0)
                setSort(event.target.value)
              }}
              value={sort}
            >
              <option value="transaction_date:desc">Newest first</option>
              <option value="transaction_date:asc">Oldest first</option>
              <option value="amount:asc">Amount: low to high</option>
              <option value="amount:desc">Amount: high to low</option>
              <option value="merchant:asc">Merchant: A–Z</option>
              <option value="merchant:desc">Merchant: Z–A</option>
            </select>
          </label>
          <div className="flex items-end">
            <button
              className="w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              onClick={() => {
                setDraftSearch('')
                setSearch('')
                setInstitutionId('')
                setAccountId('')
                setCategoryId('')
                setTransactionType('')
                setDateFrom('')
                setDateTo('')
                setAmountMin('')
                setAmountMax('')
                setSort('transaction_date:desc')
                setPage(0)
              }}
              type="button"
            >
              Clear filters
            </button>
          </div>
        </div>
        <label className="mt-3 flex w-fit cursor-pointer items-center gap-2 text-sm text-slate-600">
          <input
            checked={rememberCategory}
            className="h-4 w-4 accent-emerald-700"
            onChange={(event) => {
              setRememberCategory(event.target.checked)
            }}
            type="checkbox"
          />
          Remember for future matching merchant descriptions
        </label>
        {categoryMutation.isError ? (
          <p className="mt-3 text-sm font-medium text-rose-700">
            {categoryMutation.error.message}
          </p>
        ) : null}
        {customCategoryMutation.isError ? (
          <p className="mt-3 text-sm font-medium text-rose-700">
            {customCategoryMutation.error.message}
          </p>
        ) : null}
        <section className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          {transactions.isPending ? <p className="p-8 text-slate-500">Loading transactions…</p> : null}
          {transactions.isError ? <p className="p-8 text-rose-700">Unable to load transactions.</p> : null}
          {transactions.data ? (
            <>
              <div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
                <p>
                  Showing {transactions.data.total === 0 ? 0 : transactions.data.offset + 1}–
                  {Math.min(
                    transactions.data.offset + transactions.data.items.length,
                    transactions.data.total,
                  )}{' '}
                  of {transactions.data.total}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    className="cursor-pointer rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                    disabled={page === 0}
                    onClick={() => {
                      setPage((currentPage) => Math.max(0, currentPage - 1))
                    }}
                    type="button"
                  >
                    Previous
                  </button>
                  <span>
                    Page {page + 1} of{' '}
                    {Math.max(1, Math.ceil(transactions.data.total / pageSize))}
                  </span>
                  <button
                    className="cursor-pointer rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                    disabled={
                      transactions.data.offset + transactions.data.items.length >=
                      transactions.data.total
                    }
                    onClick={() => {
                      setPage((currentPage) => currentPage + 1)
                    }}
                    type="button"
                  >
                    Next
                  </button>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] text-left">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-5 py-3">Date</th>
                      <th className="px-5 py-3">Bank</th>
                      <th className="px-5 py-3">Account</th>
                      <th className="px-5 py-3">Merchant</th>
                      <th className="px-5 py-3">Category</th>
                      <th className="px-5 py-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.data.items.map((transaction) => (
                      <TransactionRow
                        categories={selectableCategories.filter(
                          (category) =>
                            category.is_system ||
                            category.account_id === transaction.account_id,
                        )}
                        categoryUpdating={
                          (categoryMutation.isPending &&
                            categoryMutation.variables.transactionId === transaction.id) ||
                          (customCategoryMutation.isPending &&
                            customCategoryMutation.variables.transaction.id === transaction.id)
                        }
                        detailed
                        key={transaction.id}
                        onCategoryChange={(categoryId) => {
                          categoryMutation.mutate({
                            categoryId,
                            transactionId: transaction.id,
                          })
                        }}
                        onCreateCustomCategory={(name) => {
                          customCategoryMutation.mutate({ name, transaction })
                        }}
                        transaction={transaction}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : null}
        </section>
      </div>
    </main>
  )
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
