# AGENTS.md

## Project

This repository contains a Personal Finance Analytics & Insights application.

Architecture:

* React + TypeScript + Vite frontend
* FastAPI backend
* SQLAlchemy
* Alembic
* PostgreSQL production target
* SQLite permitted for early local development
* Modular monolith
* Australian Open Banking/CDR integration later

## Core Principles

The product pipeline is:

Bank Data
→ Transaction Processing
→ Merchant Normalisation
→ Categorisation
→ Analytics
→ Insights

Do not treat this as a simple CRUD transaction tracker.

## Architecture Rules

* Do not change the core technology stack without approval.
* Do not introduce microservices.
* Do not introduce Kubernetes.
* Do not replace PostgreSQL with a NoSQL database.
* Keep business logic outside React components.
* Keep analytics logic in dedicated backend modules.
* Keep banking provider logic behind an adapter/interface.
* Inspect existing code before introducing new abstractions.
* Reuse existing components and services before creating duplicates.

## Banking Security

Never:

* collect bank usernames
* collect bank passwords
* collect bank PINs
* collect MFA codes
* scrape online banking websites
* expose banking provider secrets to the frontend
* log banking access tokens

Use Open Banking/CDR provider consent flows only.

## Financial Data Privacy

Treat transaction and account information as sensitive.

Use data minimisation.

Do not send full raw transaction datasets to external LLMs.

LLMs may receive small aggregated analytical objects only when explicitly implemented.

## Analytics Rules

Prefer deterministic calculations.

Important capabilities include:

* period-over-period comparisons
* rolling averages
* category trends
* merchant trends
* recurring payment detection
* anomaly detection
* spending concentration
* income trends
* cash-flow trends
* insight ranking

Do not generate noisy or trivial insights.

Use both percentage and monetary thresholds.

## Coding Standards

Frontend:

* TypeScript strict mode
* functional React components
* hooks
* reusable components
* TanStack Query for API state

Backend:

* Python type hints
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* pytest

## Dependency Rules

* Do not install global dependencies unless required.
* Add dependencies to the appropriate project dependency file.
* Prefer established libraries over custom infrastructure.
* Do not introduce a new dependency when the existing stack already provides the capability.

## Testing

After meaningful changes:

1. Run relevant backend tests.
2. Run frontend tests.
3. Run lint/type checks.
4. Fix regressions before proceeding.

Analytics calculations should have deterministic unit tests.

## Database Changes

All schema changes must use Alembic migrations.

Never manually modify production schema outside migrations.

Avoid destructive migrations unless explicitly required.

## Development Behaviour

For substantial features:

1. Inspect current implementation.
2. State the affected modules.
3. Implement the smallest coherent change.
4. Run relevant tests.
5. Summarise what changed.

Do not rewrite large working areas unnecessarily.

