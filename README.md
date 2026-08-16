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

The Compose credentials are development-only defaults. Set `APP_SECRET_KEY` and
`POSTGRES_PASSWORD` in `.env`; never reuse local values in production.

## Mock finance data

After applying migrations, populate the development database with two mock banks,
three accounts, system categories, merchants, and twelve months of deterministic
transactions:

```powershell
docker compose exec backend python -m app.seed
```

The seed is idempotent. It uses synthetic data only and never requests bank
credentials or communicates with a real financial institution.
