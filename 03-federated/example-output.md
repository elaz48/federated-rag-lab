uv run python 03-federated/ask.py "Is Orbit Fintech allowed to use SSO, and why?"


=== Route ===
sources: ['sql', 'docs']
reason: The question requires customer-specific data and policy information regarding SSO usage.

=== Snippets (pre-fusion bag) ===

--- snippet 1 | origin=sql | structured.sqlite ---
SQL:
SELECT customers.name, feature_flags.flag, feature_flags.enabled 
FROM customers 
JOIN feature_flags ON feature_flags.customer_id = customers.id 
WHERE customers.name = 'Orbit Fintech' AND feature_flags.flag = 'sso';

Rows (1):
[{'name': 'Orbit Fintech', 'flag': 'sso', 'enabled': 1}]

--- snippet 2 | origin=docs | security-summary.md ---
## Identity and SSO

Starter and Professional workspaces use email/password or Google OAuth. **Enterprise plans include SAML 2.0 and OIDC SSO**, with optional SCIM user provisioning. SSO is gated by the `sso` feature flag on the customer record and is only enabled for Enterprise (or explicitly flagged pilot accounts).

## Network and isolation

--- snippet 3 | origin=docs | pricing-faq.md ---
| SSO (SAML / OIDC) | No | No | Yes |
| Dedicated support + CSM | No | No | Yes |
| Custom connectors | No | No | Yes |

--- snippet 4 | origin=docs | security-summary.md ---
## Encryption and access

- Data in transit: TLS 1.2+.
- Data at rest: AES-256 (S3, RDS, and backup volumes).
- Secrets: stored in a managed KMS-backed secrets manager; application pods receive short-lived credentials.
- Employee access to production is via SSO with MFA, time-bound roles, and full session logging.

## Identity and SSO

--- snippet 5 | origin=docs | release-notes.md ---
## 2024.11 — API and advanced export GA

- REST API graduated from beta to GA for Professional and Enterprise.
- Advanced export adds scheduled Parquet drops to customer-owned S3 or GCS buckets.
- Starter remains limited to on-demand CSV from individual charts.

## 2024.09 — SSO and SCIM (Enterprise)

- SAML 2.0 and OIDC login paths generally available on Enterprise.
- SCIM 2.0 provisioning for Okta and Entra ID.
- Workspace admins can require SSO for all human users (service accounts exempt).

=== Fused context ===
[sql | structured.sqlite]
SQL:
SELECT customers.name, feature_flags.flag, feature_flags.enabled 
FROM customers 
JOIN feature_flags ON feature_flags.customer_id = customers.id 
WHERE customers.name = 'Orbit Fintech' AND feature_flags.flag = 'sso';

Rows (1):
[{'name': 'Orbit Fintech', 'flag': 'sso', 'enabled': 1}]

[docs | security-summary.md]
## Identity and SSO

Starter and Professional workspaces use email/password or Google OAuth. **Enterprise plans include SAML 2.0 and OIDC SSO**, with optional SCIM user provisioning. SSO is gated by the `sso` feature flag on the customer record and is only enabled for Enterprise (or explicitly flagged pilot accounts).

## Network and isolation

[docs | pricing-faq.md]
| SSO (SAML / OIDC) | No | No | Yes |
| Dedicated support + CSM | No | No | Yes |
| Custom connectors | No | No | Yes |

[docs | security-summary.md]
## Encryption and access

- Data in transit: TLS 1.2+.
- Data at rest: AES-256 (S3, RDS, and backup volumes).
- Secrets: stored in a managed KMS-backed secrets manager; application pods receive short-lived credentials.
- Employee access to production is via SSO with MFA, time-bound roles, and full session logging.

## Identity and SSO

[docs | release-notes.md]
## 2024.11 — API and advanced export GA

- REST API graduated from beta to GA for Professional and Enterprise.
- Advanced export adds scheduled Parquet drops to customer-owned S3 or GCS buckets.
- Starter remains limited to on-demand CSV from individual charts.

## 2024.09 — SSO and SCIM (Enterprise)

- SAML 2.0 and OIDC login paths generally available on Enterprise.
- SCIM 2.0 provisioning for Okta and Entra ID.
- Workspace admins can require SSO for all human users (service accounts exempt).

=== Answer ===
Yes, Orbit Fintech is allowed to use SSO because the feature flag for SSO is enabled for their account. Although SSO is generally gated for Enterprise plans, the enabled flag indicates that Orbit Fintech is either on an Enterprise plan or is part of a pilot program that allows SSO access.
