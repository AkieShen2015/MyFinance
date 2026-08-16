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
  financeApi,
  type Account,
  type Category,
  type Transaction,
  type TransactionPage,
} from '../api/finance'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

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
      aria-label={`Filter recent transactions by ${account.account_name}`}
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
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null)
  const overview = useQuery({ queryKey: ['overview'], queryFn: financeApi.overview })
  const accounts = useQuery({ queryKey: ['accounts'], queryFn: financeApi.accounts })
  const recentTransactionsQuery = new URLSearchParams({ limit: '15' })
  if (selectedAccountId) recentTransactionsQuery.set('account_id', selectedAccountId)
  const transactions = useQuery({
    queryKey: ['transactions', 15, selectedAccountId],
    queryFn: () => financeApi.transactions(recentTransactionsQuery.toString()),
    placeholderData: (previousData) => previousData,
  })

  if (overview.isPending || accounts.isPending || transactions.isPending) {
    return (
      <main className="grid min-h-screen place-items-center text-slate-600">
        Loading mock finance data…
      </main>
    )
  }

  if (overview.isError || accounts.isError || transactions.isError) {
    const error = overview.error ?? accounts.error ?? transactions.error
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

  const selectedAccount = accounts.data.find((account) => account.id === selectedAccountId)
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
            <p className="mt-2 text-slate-600">Phase 3 · transaction review and filtering</p>
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
        </nav>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Summary">
          <SummaryCard
            label="Total balance"
            value={money(overview.data.total_balance)}
            detail="Across all mock accounts"
          />
          <SummaryCard
            label="Accounts"
            value={String(overview.data.account_count)}
            detail={`Across ${String(new Set(accounts.data.map((account) => account.institution_id)).size)} institutions`}
          />
          <SummaryCard
            label="Transactions"
            value={String(overview.data.transaction_count)}
            detail="Twelve months of history"
          />
          <SummaryCard
            label="Categories"
            value={String(overview.data.category_count)}
            detail="Hierarchical system categories"
          />
        </section>

        <section className="mt-10">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Connected institutions</p>
              <h2 className="text-2xl font-semibold text-slate-950">Accounts</h2>
              <p className="mt-1 text-sm text-slate-500">
                Select an account to filter recent activity.
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
                      setSelectedAccountId((currentId) =>
                        currentId === account.id ? null : account.id,
                      )
                    }}
                    selected={selectedAccountId === account.id}
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
                {selectedAccount
                  ? `${selectedAccount.institution_name} · ${selectedAccount.account_name}`
                  : 'Across all accounts'}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedAccount ? (
                <button
                  className="cursor-pointer rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  onClick={() => {
                    setSelectedAccountId(null)
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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
