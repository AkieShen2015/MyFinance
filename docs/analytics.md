# Deterministic analytics design

## Calculation policy

All calculations use canonical signed decimal amounts and the user's configured
timezone. Income and expense are classified explicitly; transfers are reported
separately and excluded from income/expense unless a reviewed rule says otherwise.
Pending transactions are excluded from historical comparisons by default.

Period functions return current value, baseline value, absolute delta and optional
percentage delta. A zero baseline produces `null`, not infinity. Rolling averages
use complete prior calendar periods by default, expose the number of periods with
data, and never silently treat missing months as zero. Partial current periods are
compared with equivalent elapsed portions where the insight rule requires fairness.

Category trees aggregate descendants without double counting. Merchant and category
queries share the same filter object so dashboard totals reconcile with drilldowns.
Year-over-year values are emitted only when sufficient coverage exists.

## Recurring detection

Candidates are grouped by user, canonical merchant, direction and currency. A
minimum of three posted occurrences is required. Inter-arrival intervals are scored
against weekly (7), fortnightly (14), monthly (calendar-month), quarterly and yearly
cadences with cadence-specific date tolerances. Amount similarity uses both an
absolute and relative tolerance and supports variable bills through robust median
and median absolute deviation statistics.

Confidence combines occurrence count, interval regularity, amount stability,
merchant-resolution confidence and recency. A series becomes inactive after a
cadence-dependent number of missed expected payments. Monthly equivalents use
52/12 for weekly, 26/12 for fortnightly, 1 for monthly, 1/3 for quarterly and 1/12
for yearly costs. Each series retains its supporting transaction IDs for audit and
recalculation. User overrides will be able to confirm, reject, merge or split a
series in a later phase.

## Insight rules

Rules consume aggregate facts, never arbitrary UI state. Initial rules cover:

- merchant/category spend above or below a prior period or rolling baseline;
- income deviation and consecutive negative cash-flow months;
- newly detected, increased, or disappeared recurring costs;
- unusually large transactions using historical amount distributions;
- top-three/top-five merchant spending concentration;
- meaningful 3/6/12-month category totals and fastest-growing categories.

Every candidate contains a stable rule/entity/period deduplication key, raw decimal
facts, baseline coverage, confidence and score components. Rules require both an
absolute monetary floor and a percentage/statistical threshold. Ranking combines
normalised monetary impact, percentage change (capped), confidence, recurrence and
novelty. Near-duplicates collapse, dismissed/recently-shown candidates receive a
cooldown, and only the best 3-8 eligible insights appear on the dashboard.

