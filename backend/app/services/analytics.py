from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TransactionStatus, TransactionType
from app.models.finance import Account, Category, Merchant, Transaction
from app.schemas.finance import (
    AiInsightPayloadRead,
    AnalyticsComparisonRead,
    AnalyticsReportRead,
    CategoryTrendPointRead,
    CategoryTrendRead,
    DashboardSummaryRead,
    ExpenseCategoryRead,
    FinancialInsightRead,
    IncomeExpenseMonthRead,
    MerchantSpendRead,
    RecurringPaymentRead,
    SpendingAnomalyRead,
)

ZERO = Decimal("0")
PERCENT = Decimal("0.01")


class InvalidAccountScopeError(ValueError):
    pass


def validate_account_scope(
    db: Session,
    user_id: UUID,
    account_ids: list[UUID] | None,
) -> tuple[UUID, ...]:
    requested = set(account_ids or [])
    if not requested:
        return ()
    owned = set(
        db.scalars(
            select(Account.id).where(Account.user_id == user_id, Account.id.in_(requested))
        ).all()
    )
    if owned != requested:
        raise InvalidAccountScopeError
    return tuple(sorted(owned, key=str))


def _posted_transactions(
    db: Session,
    user_id: UUID,
    date_from: date,
    date_to: date,
    account_ids: tuple[UUID, ...] = (),
) -> list[tuple[Transaction, Category | None]]:
    filters = [
        Account.user_id == user_id,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
        Transaction.pending.is_(False),
        Transaction.status == TransactionStatus.POSTED,
    ]
    if account_ids:
        filters.append(Account.id.in_(account_ids))
    return list(
        db.execute(
            select(Transaction, Category)
            .join(Account, Account.id == Transaction.account_id)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(*filters)
            .order_by(Transaction.transaction_date, Transaction.id)
        )
        .tuples()
        .all()
    )


def _income_amount(transaction: Transaction) -> Decimal:
    if transaction.transaction_type != TransactionType.INCOME:
        return ZERO
    return max(transaction.amount, ZERO)


def _expense_amount(transaction: Transaction) -> Decimal:
    if transaction.transaction_type == TransactionType.EXPENSE:
        return abs(min(transaction.amount, ZERO))
    if transaction.transaction_type == TransactionType.REFUND:
        return -abs(transaction.amount)
    return ZERO


def dashboard_summary(
    db: Session,
    user_id: UUID,
    date_from: date,
    date_to: date,
    account_ids: tuple[UUID, ...] = (),
) -> DashboardSummaryRead:
    rows = _posted_transactions(db, user_id, date_from, date_to, account_ids)
    income = sum((_income_amount(transaction) for transaction, _ in rows), ZERO)
    expenses = max(
        sum((_expense_amount(transaction) for transaction, _ in rows), ZERO),
        ZERO,
    )
    balance_query = select(Account.current_balance).where(Account.user_id == user_id)
    if account_ids:
        balance_query = balance_query.where(Account.id.in_(account_ids))
    account_balance = sum(db.scalars(balance_query), ZERO)
    return DashboardSummaryRead(
        date_from=date_from,
        date_to=date_to,
        total_income=income,
        total_expenses=expenses,
        net_cash_flow=income - expenses,
        total_account_balance=account_balance,
    )


def expenses_by_category(
    db: Session,
    user_id: UUID,
    date_from: date,
    date_to: date,
    account_ids: tuple[UUID, ...] = (),
) -> list[ExpenseCategoryRead]:
    totals: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    for transaction, category in _posted_transactions(
        db, user_id, date_from, date_to, account_ids
    ):
        expense = _expense_amount(transaction)
        if expense:
            totals[category.name if category else "Other"] += expense
    positive_totals = {name: max(amount, ZERO) for name, amount in totals.items() if amount > 0}
    overall = sum(positive_totals.values(), ZERO)
    return [
        ExpenseCategoryRead(
            category=name,
            amount=amount,
            percentage=(amount / overall * Decimal("100")).quantize(PERCENT)
            if overall
            else ZERO,
        )
        for name, amount in sorted(
            positive_totals.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        )
    ]


def _month_starts(date_from: date, date_to: date) -> list[date]:
    months: list[date] = []
    current = date(date_from.year, date_from.month, 1)
    final = date(date_to.year, date_to.month, 1)
    while current <= final:
        months.append(current)
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else date(current.year, current.month + 1, 1)
        )
    return months


def income_vs_expenses(
    db: Session,
    user_id: UUID,
    date_from: date,
    date_to: date,
    account_ids: tuple[UUID, ...] = (),
) -> list[IncomeExpenseMonthRead]:
    monthly: defaultdict[date, dict[str, Decimal]] = defaultdict(
        lambda: {"income": ZERO, "expenses": ZERO}
    )
    for transaction, _ in _posted_transactions(db, user_id, date_from, date_to, account_ids):
        month = date(transaction.transaction_date.year, transaction.transaction_date.month, 1)
        monthly[month]["income"] += _income_amount(transaction)
        monthly[month]["expenses"] += _expense_amount(transaction)
    return [
        IncomeExpenseMonthRead(
            month=month,
            income=monthly[month]["income"],
            expenses=max(monthly[month]["expenses"], ZERO),
        )
        for month in _month_starts(date_from, date_to)
    ]


def _advanced_rows(
    db: Session,
    user_id: UUID,
    date_from: date,
    date_to: date,
    account_ids: tuple[UUID, ...],
) -> list[tuple[Transaction, Category | None, Merchant | None]]:
    filters = [
        Account.user_id == user_id,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
        Transaction.pending.is_(False),
        Transaction.status == TransactionStatus.POSTED,
    ]
    if account_ids:
        filters.append(Account.id.in_(account_ids))
    return list(
        db.execute(
            select(Transaction, Category, Merchant)
            .join(Account, Account.id == Transaction.account_id)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .outerjoin(Merchant, Merchant.id == Transaction.merchant_id)
            .where(*filters)
            .order_by(Transaction.transaction_date, Transaction.id)
        )
        .tuples()
        .all()
    )


def _comparison(current: Decimal, previous: Decimal) -> AnalyticsComparisonRead:
    change = current - previous
    percentage = (
        (change / abs(previous) * Decimal("100")).quantize(PERCENT)
        if previous
        else None
    )
    return AnalyticsComparisonRead(
        current=current,
        previous=previous,
        change_amount=change,
        change_percentage=percentage,
    )


def _row_totals(
    rows: list[tuple[Transaction, Category | None, Merchant | None]],
) -> tuple[Decimal, Decimal]:
    income = sum((_income_amount(transaction) for transaction, _, _ in rows), ZERO)
    expenses = max(
        sum((_expense_amount(transaction) for transaction, _, _ in rows), ZERO),
        ZERO,
    )
    return income, expenses


def analytics_report(
    db: Session,
    user_id: UUID,
    date_from: date,
    date_to: date,
    account_ids: tuple[UUID, ...] = (),
    comparison_mode: Literal["previous_period", "previous_year"] = "previous_period",
) -> AnalyticsReportRead:
    period_days = (date_to - date_from).days + 1
    if comparison_mode == "previous_year":
        previous_from = _same_date_previous_year(date_from)
        previous_to = _same_date_previous_year(date_to)
    else:
        previous_to = date_from - timedelta(days=1)
        previous_from = previous_to - timedelta(days=period_days - 1)
    rows = _advanced_rows(db, user_id, date_from, date_to, account_ids)
    previous_rows = _advanced_rows(db, user_id, previous_from, previous_to, account_ids)
    income, expenses = _row_totals(rows)
    previous_income, previous_expenses = _row_totals(previous_rows)
    net = income - expenses
    previous_net = previous_income - previous_expenses

    merchant_groups: defaultdict[str, list[tuple[Transaction, Decimal]]] = defaultdict(list)
    category_amounts: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    category_monthly: defaultdict[str, defaultdict[date, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: ZERO)
    )
    previous_categories: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    category_transactions: defaultdict[
        str, list[tuple[Transaction, str, Decimal]]
    ] = defaultdict(list)
    for transaction, category, merchant in rows:
        expense = _expense_amount(transaction)
        if expense <= 0:
            continue
        merchant_name = merchant.display_name if merchant else "Unknown merchant"
        category_name = category.name if category else "Other"
        merchant_groups[merchant_name].append((transaction, expense))
        category_amounts[category_name] += expense
        month = date(transaction.transaction_date.year, transaction.transaction_date.month, 1)
        category_monthly[category_name][month] += expense
        category_transactions[category_name].append((transaction, merchant_name, expense))
    for transaction, category, _ in previous_rows:
        expense = _expense_amount(transaction)
        if expense > 0:
            previous_categories[category.name if category else "Other"] += expense

    top_merchants = [
        MerchantSpendRead(
            merchant=name,
            amount=total,
            percentage=(total / expenses * Decimal("100")).quantize(PERCENT)
            if expenses
            else ZERO,
            transaction_count=len(items),
        )
        for name, items in sorted(
            merchant_groups.items(),
            key=lambda item: (-sum((amount for _, amount in item[1]), ZERO), item[0]),
        )[:8]
        if (total := sum((amount for _, amount in items), ZERO)) > 0
    ]

    recurring: list[RecurringPaymentRead] = []
    for merchant_name, items in merchant_groups.items():
        ordered = sorted(items, key=lambda item: item[0].transaction_date)
        if len(ordered) < 2:
            continue
        gaps = [
            (current[0].transaction_date - previous[0].transaction_date).days
            for previous, current in zip(ordered, ordered[1:], strict=False)
        ]
        cadence = max(1, round(sum(gaps) / len(gaps)))
        if cadence > 45:
            continue
        average = sum((amount for _, amount in ordered), ZERO) / len(ordered)
        recurring.append(
            RecurringPaymentRead(
                merchant=merchant_name,
                average_amount=average.quantize(PERCENT),
                occurrences=len(ordered),
                cadence_days=cadence,
                next_expected_date=ordered[-1][0].transaction_date + timedelta(days=cadence),
                confidence=min(Decimal("0.95"), Decimal("0.55") + Decimal(len(ordered)) / 10),
            )
        )
    recurring.sort(key=lambda item: (-item.average_amount, item.merchant))

    anomalies: list[SpendingAnomalyRead] = []
    for category_name, items in category_transactions.items():
        if len(items) < 3:
            continue
        average = sum((amount for _, _, amount in items), ZERO) / len(items)
        for transaction, merchant_name, amount in items:
            multiple = amount / average if average else ZERO
            if amount - average >= Decimal("50") and multiple >= Decimal("1.8"):
                anomalies.append(
                    SpendingAnomalyRead(
                        transaction_id=transaction.id,
                        date=transaction.transaction_date,
                        merchant=merchant_name,
                        category=category_name,
                        amount=amount,
                        baseline_amount=average.quantize(PERCENT),
                        multiple=multiple.quantize(PERCENT),
                    )
                )
    anomalies.sort(key=lambda item: (-item.multiple, -item.amount))

    category_changes = sorted(
        (
            (name, amount - previous_categories[name])
            for name, amount in category_amounts.items()
        ),
        key=lambda item: (-abs(item[1]), item[0]),
    )
    trend_categories = sorted(
        category_amounts,
        key=lambda name: (
            -max(category_amounts[name], abs(category_amounts[name] - previous_categories[name])),
            name,
        ),
    )[:6]
    months = _month_starts(date_from, date_to)
    category_trends = [
        CategoryTrendRead(
            category=name,
            current_amount=category_amounts[name],
            previous_amount=previous_categories[name],
            change_amount=category_amounts[name] - previous_categories[name],
            change_percentage=(
                (
                    (category_amounts[name] - previous_categories[name])
                    / previous_categories[name]
                    * Decimal("100")
                ).quantize(PERCENT)
                if previous_categories[name]
                else None
            ),
            monthly=[
                CategoryTrendPointRead(month=month, amount=category_monthly[name][month])
                for month in months
            ],
        )
        for name in trend_categories
    ]
    expense_comparison = _comparison(expenses, previous_expenses)
    insights: list[FinancialInsightRead] = []
    if (
        abs(expense_comparison.change_amount) >= Decimal("50")
        and abs(expense_comparison.change_percentage or ZERO) >= Decimal("10")
    ):
        direction = "increased" if expense_comparison.change_amount > 0 else "decreased"
        insights.append(
            FinancialInsightRead(
                kind="expense_change",
                title=f"Spending {direction}",
                message=(
                    f"Expenses {direction} by ${abs(expense_comparison.change_amount):,.2f} "
                    "against the previous equivalent period."
                ),
                impact_amount=abs(expense_comparison.change_amount),
                confidence=Decimal("0.99"),
            )
        )
    if top_merchants and top_merchants[0].percentage >= Decimal("20"):
        leader = top_merchants[0]
        insights.append(
            FinancialInsightRead(
                kind="concentration",
                title="Spending is concentrated",
                message=(
                    f"{leader.merchant} represents {leader.percentage}% of spending "
                    "in this period."
                ),
                impact_amount=leader.amount,
                confidence=Decimal("0.98"),
            )
        )
    recurring_total = sum((item.average_amount for item in recurring), ZERO)
    if recurring:
        insights.append(
            FinancialInsightRead(
                kind="recurring",
                title="Recurring payments detected",
                message=(
                    f"{len(recurring)} recurring patterns represent about "
                    f"${recurring_total:,.2f} per cycle."
                ),
                impact_amount=recurring_total,
                confidence=max((item.confidence for item in recurring), default=ZERO),
            )
        )
    if anomalies:
        largest = anomalies[0]
        insights.append(
            FinancialInsightRead(
                kind="anomaly",
                title="Unusual spending needs review",
                message=(
                    f"{largest.merchant} was {largest.multiple}× the usual "
                    f"{largest.category} transaction in this period."
                ),
                impact_amount=largest.amount,
                confidence=Decimal("0.80"),
            )
        )
    insights.sort(key=lambda item: (-item.impact_amount, -item.confidence))
    savings_rate = (
        (net / income * Decimal("100")).quantize(PERCENT) if income > 0 else None
    )
    ai_payload = AiInsightPayloadRead(
        period_start=date_from,
        period_end=date_to,
        expense_change_amount=expense_comparison.change_amount,
        expense_change_percentage=expense_comparison.change_percentage,
        top_category_changes=[
            {"category": name, "change_amount": str(change.quantize(PERCENT))}
            for name, change in category_changes[:3]
        ],
        recurring_total=recurring_total,
        anomaly_count=len(anomalies),
    )
    return AnalyticsReportRead(
        date_from=date_from,
        date_to=date_to,
        previous_date_from=previous_from,
        previous_date_to=previous_to,
        income=_comparison(income, previous_income),
        expenses=expense_comparison,
        net_cash_flow=_comparison(net, previous_net),
        savings_rate=savings_rate,
        category_trends=category_trends,
        top_merchants=top_merchants,
        recurring_payments=recurring,
        anomalies=anomalies,
        insights=insights[:6],
        ai_payload=ai_payload,
    )


def _same_date_previous_year(value: date) -> date:
    try:
        return value.replace(year=value.year - 1)
    except ValueError:
        return value.replace(year=value.year - 1, day=28)
