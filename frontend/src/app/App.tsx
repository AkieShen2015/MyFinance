import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { financeApi, type Account, type Transaction } from '../api/finance'

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

function AccountCard({ account }: { account: Account }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-emerald-700">{account.institution_name}</p>
          <h3 className="mt-1 font-semibold text-slate-950">{account.account_name}</h3>
          <p className="mt-1 text-sm text-slate-500">
            {account.masked_account_number ?? 'Masked number unavailable'}
          </p>
        </div>
        <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium capitalize text-emerald-700">
          {account.connection_status}
        </span>
      </div>
      <p className="mt-6 text-2xl font-semibold text-slate-950">
        {money(account.current_balance, account.currency)}
      </p>
      <p className="mt-1 text-xs capitalize text-slate-500">
        {account.account_type.replace('_', ' ')}
      </p>
    </article>
  )
}

function TransactionRow({ transaction }: { transaction: Transaction }) {
  const expense = Number(transaction.amount) < 0
  return (
    <tr className="border-t border-slate-100">
      <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
        {transaction.transaction_date}
      </td>
      <td className="px-5 py-4">
        <p className="font-medium text-slate-900">
          {transaction.merchant_name ?? transaction.description}
        </p>
        <p className="mt-0.5 text-xs text-slate-500">
          {transaction.institution_name} · {transaction.account_name}
        </p>
      </td>
      <td className="px-5 py-4 text-sm text-slate-600">
        {transaction.category_name ?? 'Other'}
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
  const overview = useQuery({ queryKey: ['overview'], queryFn: financeApi.overview })
  const accounts = useQuery({ queryKey: ['accounts'], queryFn: financeApi.accounts })
  const transactions = useQuery({
    queryKey: ['transactions', 15],
    queryFn: financeApi.transactions,
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
            <p className="mt-2 text-slate-600">Phase 2 · deterministic mock banking data</p>
          </div>
          <span className="w-fit rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-800">
            Mock data — no bank connected
          </span>
        </header>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Summary">
          <SummaryCard
            label="Total balance"
            value={money(overview.data.total_balance)}
            detail="Across all mock accounts"
          />
          <SummaryCard
            label="Accounts"
            value={String(overview.data.account_count)}
            detail="Across two institutions"
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
          <p className="text-sm font-medium text-slate-500">Connected institutions</p>
          <h2 className="mb-4 text-2xl font-semibold text-slate-950">Accounts</h2>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {accounts.data.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        </section>

        <section className="mt-10 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-end justify-between px-5 py-5">
            <div>
              <p className="text-sm font-medium text-slate-500">Latest activity</p>
              <h2 className="text-2xl font-semibold text-slate-950">Recent transactions</h2>
            </div>
            <p className="text-sm text-slate-500">
              Showing {transactions.data.items.length} of {transactions.data.total}
            </p>
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

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
