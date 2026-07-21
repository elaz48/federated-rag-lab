# Meridian Analytics — Security Whitepaper Summary

This summary is intended for security and compliance reviewers evaluating Meridian Analytics. It is not a substitute for the full whitepaper or a signed DPA.

## Architecture and data flow

Meridian is a multi-tenant SaaS application hosted on AWS (us-east-1 primary, us-west-2 DR). Customer source data is **not** permanently stored in Meridian's application database. Connectors pull into an encrypted staging area for transform, then retain only aggregates, metric definitions, and cached board payloads needed to serve the product. Staging objects expire after 30 days by default; Enterprise customers can configure shorter retention.

## Encryption and access

- Data in transit: TLS 1.2+.
- Data at rest: AES-256 (S3, RDS, and backup volumes).
- Secrets: stored in a managed KMS-backed secrets manager; application pods receive short-lived credentials.
- Employee access to production is via SSO with MFA, time-bound roles, and full session logging.

## Identity and SSO

Starter and Professional workspaces use email/password or Google OAuth. **Enterprise plans include SAML 2.0 and OIDC SSO**, with optional SCIM user provisioning. SSO is gated by the `sso` feature flag on the customer record and is only enabled for Enterprise (or explicitly flagged pilot accounts).

## Network and isolation

Each workspace's metric catalog and board cache are logically isolated by tenant ID. Enterprise customers may request private networking options (PrivateLink) under a custom agreement. Outbound connector traffic originates from a published IP allowlist.

## Compliance posture

Meridian maintains SOC 2 Type II and is GDPR-ready with EU data processing addenda. Annual penetration tests are performed by an independent firm; executive summaries are available under NDA. Customers remain the controller of source warehouse data; Meridian acts as processor for product telemetry and cached analytics artifacts.

## Customer responsibilities

- Provision least-privilege, read-only connector credentials.
- Manage seat assignment and role hygiene.
- Configure SSO and SCIM when on Enterprise.
- Review export and API token policies for Professional and Enterprise workspaces.
