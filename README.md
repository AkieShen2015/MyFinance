# Personal Finance Analytics & Insights

A multi-user-ready, privacy-conscious personal finance analytics application for
Australian users. Bank access will eventually use a compliant CDR provider; the
application never collects bank credentials or scrapes bank websites.

## Prerequisites

- Python 3.12
- Node.js 22 or newer
- PostgreSQL for production (SQLite is supported for early local development)

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item ..\.env.example ..\.env
alembic upgrade head
uvicorn app.main:app --reload
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`; the API runs at
`http://localhost:8000`. See `docs/` for design decisions and phase gates.

## Docker development stack

Docker starts PostgreSQL, runs Alembic, and serves both applications:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Useful endpoints:

- Docker frontend: `http://localhost:5174`
- API documentation: `http://localhost:8000/api/docs`
- Health check: `http://localhost:8000/api/health`

The frontend development image includes the Chromium build required by
Playwright. After changes to `frontend/Dockerfile` or the frontend lockfile,
rebuild that image before running end-to-end tests:

```powershell
docker compose build frontend
docker compose up -d frontend
docker compose exec frontend npm run test:e2e
```

The Compose credentials are development-only defaults. Set `APP_SECRET_KEY` and
`POSTGRES_PASSWORD` in `.env`; never reuse local values in production.

## Mock finance data

After applying migrations, populate the development database with 14 mock bank
institutions, 15 accounts, system and account-scoped categories, merchants, and
twelve months of deterministic transactions:

```powershell
docker compose exec backend python -m app.seed
```

The seed is idempotent. It uses synthetic data only and never requests bank
credentials or communicates with a real financial institution.

## Dashboard analytics

The Phase 4 dashboard uses deterministic, date-bounded calculations over posted
transactions. Transfers are excluded and refunds reduce expenses. Its APIs are:

- `GET /api/dashboard/summary`
- `GET /api/dashboard/expenses-by-category`
- `GET /api/dashboard/income-vs-expenses`

Each endpoint requires `date_from` and `date_to` ISO date query parameters.

## Advanced analytics and insights

The Analytics page uses `GET /api/analytics/report` for deterministic prior-period
comparisons, merchant concentration, recurring-payment estimates, anomaly detection,
savings rate, monthly category trends, and ranked material insights. Repeated `account_id` query parameters scope
the report to one or more accounts and are validated against the authenticated user.

Prior-period comparisons use the immediately preceding, non-overlapping range with the
same inclusive number of calendar days. The Analytics UI provides the same standard period
presets as Overview, including a rolling Last 1 year option, plus custom dates. This year uses
a year-over-year comparison against the same year-to-date dates in the previous year.
Recurring and unusual-transaction results are returned
without API truncation and displayed in pages of 10.

The response also contains an `ai_payload` object composed only of small aggregate values.
It is the approved boundary for a future optional explanation provider: raw descriptions,
transaction rows, account identifiers, and provider data must never be included.
