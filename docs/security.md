# Security, privacy and CDR risks

## Banking/CDR boundary

The application never collects bank usernames, passwords, PINs or MFA codes and
never screen-scrapes. Consent and bank authentication occur in provider/bank-hosted
flows. Provider secrets and tokens remain on the backend, encrypted with keys held
outside the database, and are redacted from logs, traces and errors.

A commercial API alone does not establish the application's legal role. Before a
real integration, confirm whether the product operates as an accredited recipient,
affiliate/sponsored participant, CDR representative or outsourced service provider;
record consent, disclosure, retention, deletion, dispute-resolution and incident
obligations in the provider contract and privacy design.

Provider selection must assess hosted consent, scopes, receipts, expiry/renewal,
revocation, data residency/subprocessors, webhook verification, replay protection,
rate limits, pagination/cursors, pending-to-posted semantics, deletion/reversal,
sandbox quality, SLA, breach notification and exit/data-portability terms.

## Application threats and controls

- Broken object-level authorisation: every repository query is user-scoped and is
  covered by cross-user negative tests.
- Session theft/CSRF: opaque rotated server sessions, HttpOnly/Secure/SameSite
  cookies, CSRF tokens for mutations, expiry and revocation.
- Sensitive logging: allowlist structured fields; exclude financial descriptions,
  raw payloads, cookies, headers, full account identifiers and tokens.
- Forged/replayed webhooks: verify provider signatures and timestamp windows, store
  unique event IDs, and process idempotently.
- Malicious provider data: strict schemas, length limits, safe URL handling,
  escaped rendering and payload-size limits.
- Excess retention: minimise raw provider data and provide distinct revoke consent,
  disconnect, delete imported data, delete connection/account and delete profile
  operations with auditable partial-failure states.
- Analytics privacy: no raw history is sent to an LLM. A future language model may
  receive only the minimum aggregated structured insight required for phrasing.
- Supply chain: committed lockfiles, dependency scanning, minimal containers and
  non-root production processes.

