# Data model

All user-owned access is authorised from the authenticated session; APIs never
accept `user_id` as proof of ownership. Foreign keys use restrictive deletion by
default, with explicit service-level privacy deletion workflows.

## Entities and relationships

- `users` owns connections, accounts, tags, custom categories/rules, recurring
  series, insights, sessions and audit events.
- `institutions` is provider-scoped reference data, unique on
  `(provider, external_id)`.
- `bank_connections` belongs to a user and institution, and records consent state,
  expiry and last successful sync.
- `accounts` belongs to a user, connection and institution, unique on
  `(bank_connection_id, external_account_id)`.
- `merchants` stores canonical merchants. `merchant_aliases` stores normalised
  match values, resolution method and confidence without overwriting raw text.
- `categories` is hierarchical. System rows have no owner; custom rows have a
  `user_id`. Parent/child ownership and compatible category type are validated.
- `transactions` belongs to an account and optionally a merchant/category, unique
  on `(account_id, external_transaction_id)`. It stores transaction and posted
  dates, original and normalised descriptions, decimal amount/currency, canonical
  type/status, provider category, and protected raw data.
- `transaction_tags` belongs to a user and is unique on `(user_id, name)`.
  `transaction_tag_links` has a composite primary key `(transaction_id, tag_id)`.
- `categorisation_rules` belongs to a user, has typed matching criteria, optional
  merchant, category, priority and enabled state.
- `transaction_category_changes` records old/new category, actor and whether a
  similar-transaction rule was requested.
- `recurring_series` stores merchant/category, cadence, expected amount, tolerance,
  confidence, observed range and next expected date. `recurring_occurrences` links
  supporting transactions and prevents one transaction supporting duplicate
  membership in the same series.
- `insights` stores type/entity/period/severity, stable deduplication key, title,
  summary, structured facts, score, creation/expiry and dismissal.
- `sync_jobs` stores trigger/status/cursor/page token/range/counters/errors and job
  timestamps. `provider_webhook_events` enforces event idempotency.
- `user_sessions` stores only hashed session identifiers. `audit_events` stores an
  allowlisted metadata document without descriptions, account numbers or tokens.

## Indexes

- unique `transactions(account_id, external_transaction_id)`
- `transactions(account_id, transaction_date desc)`
- `transactions(category_id, transaction_date desc)`
- `transactions(merchant_id, transaction_date desc)`
- `accounts(user_id, institution_id)`
- `bank_connections(user_id, status)`
- `categorisation_rules(user_id, enabled, priority)`
- `recurring_series(user_id, active, next_expected_date)`
- `insights(user_id, dismissed_at, score desc, created_at desc)`
- `sync_jobs(bank_connection_id, created_at desc)`

Indexes will be adjusted only after real query patterns are measured.

