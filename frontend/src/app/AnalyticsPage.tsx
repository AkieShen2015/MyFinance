import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { financeApi, type AnalyticsComparison } from '../api/finance'
import { isoDate, presetPeriod, type PeriodPreset } from './datePeriods'

const categoryColours = ['#047857', '#2563eb', '#7c3aed', '#c2410c', '#0891b2', '#be123c']
const recurringPageSize = 10
const anomalyPageSize = 10

function displayDate(value: string) {
  return new Intl.DateTimeFormat('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${value}T00:00:00`))
}

function money(value: string) {
  return new Intl.NumberFormat('en-AU', {
    currency: 'AUD',
    maximumFractionDigits: 2,
    style: 'currency',
  }).format(Number(value))
}

function compactMoney(value: number) {
  const absolute = Math.abs(value)
  if (absolute >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}m`
  if (absolute >= 1_000) return `$${(value / 1_000).toFixed(1)}k`
  return `$${Math.round(value).toString()}`
}

function ComparisonCard({ label, comparison, priorPeriod }: { label: string; comparison: AnalyticsComparison; priorPeriod: string }) {
  const change = Number(comparison.change_amount)
  const percentage = comparison.change_percentage
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-slate-950">{money(comparison.current)}</p>
      <p className={`mt-2 text-sm font-medium ${change <= 0 ? 'text-emerald-700' : 'text-amber-700'}`}>
        {change > 0 ? '+' : ''}{money(comparison.change_amount)}
        {percentage === null ? '' : ` (${percentage}%)`}
      </p>
      <p className="mt-1 text-xs text-slate-500">vs {priorPeriod}</p>
    </article>
  )
}

export function AnalyticsPage() {
  const today = new Date()
  const [periodPreset, setPeriodPreset] = useState<PeriodPreset>('this_year')
  const [dateFrom, setDateFrom] = useState(() => isoDate(new Date(today.getFullYear(), 0, 1)))
  const [dateTo, setDateTo] = useState(() => isoDate(today))
  const [selectedAccountIds, setSelectedAccountIds] = useState<string[]>([])
  const [recurringPage, setRecurringPage] = useState(0)
  const [anomalyPage, setAnomalyPage] = useState(0)
  const accounts = useQuery({ queryKey: ['accounts'], queryFn: financeApi.accounts })
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo })
  params.set('comparison', periodPreset === 'this_year' ? 'previous_year' : 'previous_period')
  selectedAccountIds.forEach((accountId) => {
    params.append('account_id', accountId)
  })
  const report = useQuery({
    placeholderData: (previousData) => previousData,
    queryFn: () => financeApi.analyticsReport(params.toString()),
    queryKey: ['analytics-report', dateFrom, dateTo, selectedAccountIds.join(',')],
  })
  useEffect(() => {
    if (periodPreset === 'custom') return
    const nextPeriod = presetPeriod(periodPreset)
    setDateFrom(nextPeriod.dateFrom)
    setDateTo(nextPeriod.dateTo)
  }, [periodPreset])
  useEffect(() => {
    setRecurringPage(0)
    setAnomalyPage(0)
  }, [dateFrom, dateTo, selectedAccountIds])

  if (accounts.isPending || report.isPending) {
    return <main className="grid min-h-screen place-items-center text-slate-600">Loading analytics…</main>
  }
  if (accounts.isError || report.isError) {
    return <main className="grid min-h-screen place-items-center text-rose-700">Unable to load analytics.</main>
  }

  const merchantChart = report.data.top_merchants.map((item) => ({
    amount: Number(item.amount),
    merchant: item.merchant,
  }))
  const recurringTotal = report.data.recurring_payments.length
  const recurringPageCount = Math.max(1, Math.ceil(recurringTotal / recurringPageSize))
  const recurringStart = recurringPage * recurringPageSize
  const recurringItems = report.data.recurring_payments.slice(
    recurringStart,
    recurringStart + recurringPageSize,
  )
  const anomalyTotal = report.data.anomalies.length
  const anomalyPageCount = Math.max(1, Math.ceil(anomalyTotal / anomalyPageSize))
  const anomalyStart = anomalyPage * anomalyPageSize
  const anomalyItems = report.data.anomalies.slice(
    anomalyStart,
    anomalyStart + anomalyPageSize,
  )
  const priorPeriod = `${displayDate(report.data.previous_date_from)}–${displayDate(report.data.previous_date_to)}`
  const categoryMonths = Array.from(
    new Set(report.data.category_trends.flatMap((trend) => trend.monthly.map((point) => point.month))),
  ).sort()
  const categoryChart: Array<Record<string, number | string>> = categoryMonths.map((month) => {
    const point: Record<string, number | string> = {
      month: new Intl.DateTimeFormat('en-AU', { month: 'short', year: '2-digit' }).format(
        new Date(`${month}T00:00:00`),
      ),
    }
    report.data.category_trends.forEach((trend) => {
      point[trend.category] = Number(
        trend.monthly.find((item) => item.month === month)?.amount ?? '0',
      )
    })
    return point
  })

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 sm:px-8">
      <div className="mx-auto max-w-7xl">
        <header>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-emerald-700">
            Personal Finance
          </p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight text-slate-950">
            Analytics & insights
          </h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Deterministic analysis of spending changes, merchant concentration, recurring
            payments and unusual activity.
          </p>
        </header>
        <nav className="mt-5 flex gap-4 text-sm font-medium">
          <Link className="text-slate-600 hover:text-emerald-700" to="/">Overview</Link>
          <Link className="text-slate-600 hover:text-emerald-700" to="/transactions">Transactions</Link>
          <span className="text-emerald-700">Analytics</span>
        </nav>

        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Analytics filters">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <label className="text-sm font-medium text-slate-700">
              Period
              <select
                className="mt-1 block w-full cursor-pointer rounded-xl border border-slate-300 bg-white px-3 py-2.5"
                onChange={(event) => {
                  const nextPreset = event.target.value as PeriodPreset
                  setPeriodPreset(nextPreset)
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
              <input className="mt-1 block w-full rounded-xl border border-slate-300 px-3 py-2 disabled:bg-slate-100" disabled={periodPreset !== 'custom'} max={dateTo} onChange={(event) => { setDateFrom(event.target.value) }} type="date" value={dateFrom} />
            </label>
            <label className="text-sm font-medium text-slate-700">
              To
              <input className="mt-1 block w-full rounded-xl border border-slate-300 px-3 py-2 disabled:bg-slate-100" disabled={periodPreset !== 'custom'} min={dateFrom} onChange={(event) => { setDateTo(event.target.value) }} type="date" value={dateTo} />
            </label>
            <details className="relative self-end">
              <summary className="cursor-pointer rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700">
                {selectedAccountIds.length === 0
                  ? `All ${String(accounts.data.length)} accounts`
                  : `${String(selectedAccountIds.length)} ${selectedAccountIds.length === 1 ? 'account' : 'accounts'} selected`}
              </summary>
              <div className="absolute right-0 z-20 mt-2 max-h-80 w-full min-w-80 overflow-y-auto rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
                <button className="mb-2 cursor-pointer text-xs font-semibold text-emerald-700" onClick={() => { setSelectedAccountIds([]) }} type="button">Use all accounts</button>
                {accounts.data.map((account) => (
                  <label className="flex cursor-pointer gap-2 rounded-lg px-2 py-2 text-sm hover:bg-slate-50" key={account.id}>
                    <input checked={selectedAccountIds.includes(account.id)} className="accent-emerald-700" onChange={() => { setSelectedAccountIds((current) => current.includes(account.id) ? current.filter((id) => id !== account.id) : [...current, account.id]) }} type="checkbox" />
                    <span><span className="block font-medium">{account.account_name}</span><span className="text-xs text-slate-500">{account.institution_name}</span></span>
                  </label>
                ))}
              </div>
            </details>
          </div>
          <p className="mt-4 border-t border-slate-100 pt-4 text-sm text-slate-600">
            {periodPreset === 'this_year'
              ? `This year is compared year-over-year with the same dates last year: ${priorPeriod}.`
              : `Comparisons use the immediately preceding, non-overlapping period of the same number of calendar days: ${priorPeriod}.`}
          </p>
        </section>

        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4" aria-label="Analytics summary">
          <ComparisonCard comparison={report.data.income} label="Income" priorPeriod={priorPeriod} />
          <ComparisonCard comparison={report.data.expenses} label="Expenses" priorPeriod={priorPeriod} />
          <ComparisonCard comparison={report.data.net_cash_flow} label="Net cash flow" priorPeriod={priorPeriod} />
          <article className="rounded-2xl border border-emerald-200 bg-emerald-950 p-5 text-white shadow-sm">
            <p className="text-sm font-medium text-emerald-200">Savings rate</p>
            <p className="mt-2 text-3xl font-semibold">{report.data.savings_rate === null ? 'N/A' : `${report.data.savings_rate}%`}</p>
            <p className="mt-2 text-xs text-emerald-200">Net cash flow as a percentage of income</p>
          </article>
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
            <p className="text-sm font-medium text-slate-500">Category movement</p>
            <h2 className="text-2xl font-semibold text-slate-950">Spending trends by category</h2>
            <p className="mt-1 text-sm text-slate-500">Top categories ranked by spending and material change.</p>
            <div className="mt-5 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
              <div className="overflow-x-auto">
                <div className="h-80 min-w-[760px]" aria-label="Category spending trend chart">
                  <ResponsiveContainer height="100%" width="100%">
                  <LineChart data={categoryChart} margin={{ left: 8, right: 16, top: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      angle={-35}
                      dataKey="month"
                      height={58}
                      interval={0}
                      textAnchor="end"
                    />
                    <YAxis tickFormatter={(value: number) => compactMoney(value)} width={72} />
                    <Tooltip formatter={(value) => money(String(value))} />
                    <Legend />
                    {report.data.category_trends.map((trend, index) => (
                      <Line
                        dataKey={trend.category}
                        dot={false}
                        key={trend.category}
                        stroke={categoryColours[index % categoryColours.length]}
                        strokeWidth={2.5}
                        type="monotone"
                      />
                    ))}
                  </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="space-y-2">
                {report.data.category_trends.map((trend) => {
                  const change = Number(trend.change_amount)
                  return (
                    <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-4 py-3" key={trend.category}>
                      <div><p className="font-medium text-slate-900">{trend.category}</p><p className="text-xs text-slate-500">Prior {money(trend.previous_amount)}</p></div>
                      <div className="text-right"><p className="font-semibold">{money(trend.current_amount)}</p><p className={`text-xs ${change <= 0 ? 'text-emerald-700' : 'text-amber-700'}`}>{change > 0 ? '+' : ''}{money(trend.change_amount)}{trend.change_percentage === null ? '' : ` · ${trend.change_percentage}%`}</p></div>
                    </div>
                  )
                })}
              </div>
            </div>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Concentration</p>
            <h2 className="text-2xl font-semibold text-slate-950">Top merchants</h2>
            <div className="mt-4 h-80" aria-label="Top merchant spending chart">
              <ResponsiveContainer height="100%" width="100%">
                <BarChart data={merchantChart} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid horizontal={false} strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="merchant" type="category" width={120} />
                  <Tooltip formatter={(value) => money(String(value))} />
                  <Bar dataKey="amount" fill="#047857" name="Spending" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">Ranked by financial impact</p>
            <h2 className="text-2xl font-semibold text-slate-950">What deserves attention</h2>
            <div className="mt-4 space-y-3">
              {report.data.insights.length === 0 ? <p className="text-sm text-slate-500">No material changes crossed the insight thresholds.</p> : report.data.insights.map((insight) => (
                <section className="rounded-xl border border-slate-200 p-4" key={`${insight.kind}-${insight.title}`}>
                  <div className="flex items-start justify-between gap-3"><h3 className="font-semibold text-slate-900">{insight.title}</h3><span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">{Math.round(Number(insight.confidence) * 100)}% confidence</span></div>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{insight.message}</p>
                </section>
              ))}
            </div>
          </article>
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-2">
          <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-end sm:justify-between">
              <div><p className="text-sm font-medium text-slate-500">Forecast</p><h2 className="text-2xl font-semibold">Recurring payments</h2></div>
              <p className="text-sm text-slate-500">
                Showing {recurringTotal === 0 ? 0 : recurringStart + 1}–{Math.min(recurringStart + recurringItems.length, recurringTotal)} of {recurringTotal}
              </p>
            </div>
            {recurringTotal === 0 ? (
              <p className="border-t border-slate-100 p-5 text-sm text-slate-500">No recurring payment patterns detected.</p>
            ) : (
              <>
                <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-5 py-3">Merchant</th><th className="px-5 py-3">Average</th><th className="px-5 py-3">Cadence</th><th className="px-5 py-3">Next expected</th></tr></thead><tbody>{recurringItems.map((item) => <tr className="border-t border-slate-100" key={item.merchant}><td className="px-5 py-3 font-medium">{item.merchant}</td><td className="px-5 py-3">{money(item.average_amount)}</td><td className="px-5 py-3">Every ~{item.cadence_days} days</td><td className="px-5 py-3">{item.next_expected_date}</td></tr>)}</tbody></table></div>
                <div className="flex items-center justify-between border-t border-slate-100 px-5 py-4 text-sm">
                  <button className="cursor-pointer rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40" disabled={recurringPage === 0} onClick={() => { setRecurringPage((page) => Math.max(0, page - 1)) }} type="button">Previous recurring payments</button>
                  <span>Page {recurringPage + 1} of {recurringPageCount}</span>
                  <button className="cursor-pointer rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40" disabled={recurringPage + 1 >= recurringPageCount} onClick={() => { setRecurringPage((page) => Math.min(recurringPageCount - 1, page + 1)) }} type="button">Next recurring payments</button>
                </div>
              </>
            )}
          </article>
          <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-end sm:justify-between">
              <div><p className="text-sm font-medium text-slate-500">Review queue</p><h2 className="text-2xl font-semibold">Unusual transactions</h2></div>
              <p className="text-sm text-slate-500">
                Showing {anomalyTotal === 0 ? 0 : anomalyStart + 1}–{Math.min(anomalyStart + anomalyItems.length, anomalyTotal)} of {anomalyTotal}
              </p>
            </div>
            {anomalyTotal === 0 ? (
              <p className="border-t border-slate-100 p-5 text-sm text-slate-500">No transactions exceeded both anomaly thresholds.</p>
            ) : (
              <>
                <div className="divide-y divide-slate-100">{anomalyItems.map((item) => <div className="flex items-center justify-between gap-4 px-5 py-4" key={item.transaction_id}><div><p className="font-medium text-slate-900">{item.merchant}</p><p className="text-xs text-slate-500">{item.category} · baseline {money(item.baseline_amount)}</p></div><div className="text-right"><p className="font-semibold">{money(item.amount)}</p><p className="text-xs text-amber-700">{item.multiple}× usual</p></div></div>)}</div>
                <div className="flex items-center justify-between border-t border-slate-100 px-5 py-4 text-sm">
                  <button className="cursor-pointer rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40" disabled={anomalyPage === 0} onClick={() => { setAnomalyPage((page) => Math.max(0, page - 1)) }} type="button">Previous unusual transactions</button>
                  <span>Page {anomalyPage + 1} of {anomalyPageCount}</span>
                  <button className="cursor-pointer rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-40" disabled={anomalyPage + 1 >= anomalyPageCount} onClick={() => { setAnomalyPage((page) => Math.min(anomalyPageCount - 1, page + 1)) }} type="button">Next unusual transactions</button>
                </div>
              </>
            )}
          </article>
        </section>

        <aside className="mt-6 rounded-2xl border border-indigo-200 bg-indigo-50 p-5">
          <p className="text-sm font-semibold text-indigo-900">AI-ready, privacy-first</p>
          <p className="mt-1 text-sm leading-6 text-indigo-800">The backend now prepares a small aggregate-only explanation payload. No raw descriptions, account identifiers or transaction rows are sent externally, and no AI provider is connected yet.</p>
        </aside>
      </div>
    </main>
  )
}
