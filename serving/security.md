# Serving Layer Security (Task 13)

Aligned with [architecture/09-security-architecture.md](../../architecture/09-security-architecture.md).
The serving layer is the platform's external-facing surface, so defence-in-depth
focuses here.

## Authentication

- **Users**: OIDC via Keycloak (open-source IdP). Superset and the API delegate
  login to Keycloak; no local passwords in serving components.
- **Services**: ML/RAG/service accounts use client-credential tokens with narrow
  scopes.
- **External**: public API access uses an anonymous read scope limited to
  public-classified datasets.

## Authorization

- Role-based (RBAC) per [access-strategy.md](access-strategy.md): scope → role →
  dataset permission.
- Enforced at every surface: Superset roles + row-level security, API middleware
  scope checks, RAG classification filter, warehouse read-only grants.
- **Deny by default** — a dataset with no explicit grant is inaccessible.

## Dataset Permissions

| Class | Grant model |
| --- | --- |
| Public | read to anonymous scope |
| Internal | read to authenticated staff roles |
| Sensitive | read to named role only (`ops_maritime`) |
| Demo (sim) | read to `demo` scope, responses labelled synthetic |

## API Security

| Control | Detail |
| --- | --- |
| Transport | TLS enforced (HTTPS only) |
| Tokens | short-lived bearer tokens; rotation supported |
| Input validation | Pydantic models; whitelist filters (no arbitrary SQL) |
| Rate limiting | per-token quota; `429` on breach |
| Injection defence | parameterized queries only; no string-built SQL |
| CORS | allow-list of known origins |

## Audit Logging

- Every serving access logged: `who` (subject), `what` (dataset/endpoint),
  `when`, `result` (allow/deny), `filters`.
- Logs shipped to the observability stack; retained for compliance review.
- Denied accesses are alerted on (see incident I-07).

## Consumer Isolation

- Read-only credentials for all consumers; the refresh service account is the
  only writer and is network-isolated from consumer roles.
- Sensitive (maritime) data is served from a dataset only `ops_maritime` and
  `exec`/`ai` service accounts can reach; it is never embedded into the public
  RAG index.
- Tenant/role scoping prevents one consumer group from reading another's
  restricted datasets.

## OWASP Alignment

| Risk | Mitigation |
| --- | --- |
| Broken access control | deny-by-default RBAC, row-level security, audit |
| Injection | parameterized queries, filter whitelisting |
| Sensitive data exposure | classification + retrieval boundaries + TLS |
| Security misconfiguration | secrets from env only, read-only grants |
| Auth failures | OIDC, short-lived tokens, rate limiting |
