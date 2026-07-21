uv run python 01-naive-rag/ask.py "What does the Professional plan include?"


=== Retrieved chunks ===

--- chunk 1 | integrations.md ---
## Plan requirements

- All plans include the six first-class connectors above.
- **REST API access** requires Professional or Enterprise (or an explicit `api_access` flag).
- **Custom HTTP connectors** require Enterprise.
- **Advanced export** to customer object storage requires Professional or Enterprise.

## Operational guidance

--- chunk 2 | pricing-faq.md ---
## Which plan should we pick?

- Choose **Starter** if you need a few shared boards and CSV exports.
- Choose **Professional** if you need the API, advanced export, or more seats and monitors.
- Choose **Enterprise** if you require SSO, custom connectors, or a dedicated customer success manager.

--- chunk 3 | pricing-faq.md ---
**Do feature flags override the plan matrix?** Account teams can enable individual flags (for example early API access) for specific customers during pilots. Unless a flag is enabled in the customer record, plan limits apply as written above.

**What payment methods are accepted?** Credit card for Starter and Professional. Enterprise invoices via ACH or wire on Net-30 terms.

## Which plan should we pick?

--- chunk 4 | support-sla.md ---
Enterprise customers with the `dedicated_support` flag also receive a quarterly business review and a shared success plan. Uptime SLA for the core app is 99.9% monthly for Professional and Enterprise; Starter is best effort. SLA credits, when applicable, are described in the master subscription agreement—not in this public summary.

=== Answer ===
The Professional plan includes REST API access, advanced export, and more seats and monitors.




uv run python 01-naive-rag/ask.py "What plan is Orbit Fintech on, and is SSO enabled for them?"


=== Retrieved chunks ===

--- chunk 1 | security-summary.md ---
## Identity and SSO

Starter and Professional workspaces use email/password or Google OAuth. **Enterprise plans include SAML 2.0 and OIDC SSO**, with optional SCIM user provisioning. SSO is gated by the `sso` feature flag on the customer record and is only enabled for Enterprise (or explicitly flagged pilot accounts).

## Network and isolation

--- chunk 2 | pricing-faq.md ---
| SSO (SAML / OIDC) | No | No | Yes |
| Dedicated support + CSM | No | No | Yes |
| Custom connectors | No | No | Yes |

--- chunk 3 | release-notes.md ---
## 2024.11 — API and advanced export GA

- REST API graduated from beta to GA for Professional and Enterprise.
- Advanced export adds scheduled Parquet drops to customer-owned S3 or GCS buckets.
- Starter remains limited to on-demand CSV from individual charts.

## 2024.09 — SSO and SCIM (Enterprise)

- SAML 2.0 and OIDC login paths generally available on Enterprise.
- SCIM 2.0 provisioning for Okta and Entra ID.
- Workspace admins can require SSO for all human users (service accounts exempt).

--- chunk 4 | pricing-faq.md ---
**Do feature flags override the plan matrix?** Account teams can enable individual flags (for example early API access) for specific customers during pilots. Unless a flag is enabled in the customer record, plan limits apply as written above.

**What payment methods are accepted?** Credit card for Starter and Professional. Enterprise invoices via ACH or wire on Net-30 terms.

## Which plan should we pick?

=== Answer ===
I do not know.

