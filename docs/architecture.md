# Architecture and implementation plan

## Repository assessment

The initial repository contained only empty `work/` and `outputs/` directories,
was not a Git repository, and had no application code. The local machine exposes
Node 24 and npm 11. The Codex workspace runtime provides Python 3.12.13. Docker is
not currently installed, so SQLite is the local fallback while PostgreSQL remains
the production target.

## System design

The product is a modular monolith: a React browser application, a FastAPI API,
one relational database, and a background worker boundary. Routes authenticate
and validate; services enforce business rules; repositories own persistence;
analytics modules contain deterministic calculations; banking adapters translate
provider models into canonical internal models.

Provider tokens and provider API calls stay server-side. The browser only receives
a short-lived hosted-consent URL/session reference. Financial aggregation happens
server-side so raw history is not sent to the browser merely to draw a chart.

The transaction pipeline is composed of independently testable stages:

1. validate provider input;
2. deduplicate and reconcile updates;
3. normalise descriptions and signed amounts;
4. resolve a canonical merchant;
5. apply deterministic categorisation precedence;
6. persist atomically;
7. refresh affected analytics and recurring series;
8. evaluate, rank, and store structured insights.

## Final folder boundaries

- `frontend/src/app`: composition, router, providers
- `frontend/src/features`: domain UI and feature-specific API hooks
- `frontend/src/components`: reusable presentation primitives
- `backend/app/api`: HTTP routes and request dependencies
- `backend/app/core`: configuration, security, logging, database
- `backend/app/models` and `schemas`: persistence and API contracts
- `backend/app/repositories`: user-scoped persistence operations
- `backend/app/services`: application workflows and pipeline stages
- `backend/app/analytics`: pure aggregation, comparison, recurring, anomaly,
  concentration, and insight-rule functions
- `backend/app/integrations/banking`: provider protocol, canonical DTOs, mock and
  eventual real adapters
- `backend/app/workers`: durable sync and analytics job entry points

## Key decisions

- Use UUID identifiers, timezone-aware UTC timestamps, ISO currency codes, and
  decimal money values; never binary floating point.
- Use opaque server-side sessions in Secure, HttpOnly, SameSite cookies plus CSRF
  protection for mutations. The current phase exposes an authentication protocol,
  not a fake production authentication implementation.
- Keep SQLAlchemy portable. PostgreSQL-only optimisations must be isolated and
  justified with measured query plans.
- Preserve original transaction descriptions but expose provider raw data only
  through explicitly sanitised response schemas.
- Store insight facts as structured data. Rendered text is replaceable output,
  never the analytical source of truth.
- Run real CDR integration only after the mock provider and analytics pipeline are
  stable and the provider/legal participation model is confirmed.

## Architectural risks

- SQLite/PostgreSQL differences in concurrency, decimals, JSON, constraints, and
  date handling: CI must run migrations and integration tests against PostgreSQL.
- Merchant aliases can merge unrelated merchants: retain match provenance and add
  user override support rather than destructive rewriting.
- Transfers/refunds can distort income and expense totals: define canonical types
  and exclude internal transfers from cash-flow analytics by policy.
- Pending-to-posted records may change provider IDs: use provider links first and
  conservative reconciliation second; do not fuzzy-delete records.
- Analytics boundary ambiguity can create misleading comparisons: define timezone,
  calendar-month, partial-period, and zero-baseline semantics centrally.
- Insight fatigue: use monetary floors, confidence, deduplication, cooldowns, and a
  strict 3-8 item dashboard budget.
- Background jobs can race or replay: use idempotency keys, connection-level locks,
  database transactions, and observable job states.

## Delivery phases and gates

1. **Foundation:** scaffolds, configuration, database/Alembic, authentication
   abstraction, lint/type/test tooling. Gate: all checks and migration round-trip.
2. **Core finance model:** entities, constraints, mock provider and 12-month fixture.
   Gate: fresh migration plus ownership/deduplication tests.
3. **Transaction intelligence:** normalisation, merchant resolution, categorisation,
   overrides, tags, search/filter API. Gate: deterministic pipeline/API tests.
4. **Analytics:** income, expenses, cash flow, category/merchant aggregation,
   rolling and period comparisons. Gate: golden numerical test cases.
5. **Recurring:** cadence/tolerance detection and cost equivalents. Gate: noisy,
   missed, variable-amount, and inactive-series fixtures.
6. **Insights:** trend/anomaly/concentration rules and prioritisation. Gate: relevance
   thresholds and structured-output snapshots.
7. **Dashboard:** charts, drilldowns, transactions and accounts UX. Gate: component,
   accessibility, and Playwright flows.
8. **Open Banking:** contracted CDR adapter, consent, webhooks, incremental sync,
   revocation and deletion. Gate: sandbox contract/security tests.
9. **Production hardening:** production identity, secrets, rate limits, audit,
   monitoring, backup/restore, performance and deployment review.

No later phase should begin while the prior phase gate is failing.

