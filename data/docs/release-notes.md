# Meridian Analytics — Release Notes

## 2025.06 — Narrative briefings v2

- Briefings now cite the top three contributing dimensions for each metric move.
- Slack delivery supports threaded replies under a single daily summary message.
- Fixed a bug where weekly briefings double-counted partial weeks at month boundaries.

## 2025.04 — Custom dashboard embeds

- Professional and Enterprise can embed boards in internal portals with a signed URL.
- Embed tokens expire after 24 hours unless refreshed by the host application.
- Viewers in embeds inherit the workspace role of the token owner (no anonymous public boards).

## 2025.02 — Anomaly monitors at scale

- Professional monitor limit raised from 25 to 50; Enterprise remains unlimited.
- New composite monitors: alert when *two* related metrics drift within the same window.
- Monitor mute windows for planned maintenance (up to 72 hours).

## 2024.11 — API and advanced export GA

- REST API graduated from beta to GA for Professional and Enterprise.
- Advanced export adds scheduled Parquet drops to customer-owned S3 or GCS buckets.
- Starter remains limited to on-demand CSV from individual charts.

## 2024.09 — SSO and SCIM (Enterprise)

- SAML 2.0 and OIDC login paths generally available on Enterprise.
- SCIM 2.0 provisioning for Okta and Entra ID.
- Workspace admins can require SSO for all human users (service accounts exempt).

## 2024.06 — Connector pack

- First-class Stripe and HubSpot connectors shipped.
- Postgres connector gained support for read replicas via separate host configuration.
- Deprecated the legacy CSV upload path; use connectors or the API instead.

Upgrade notes: API clients on the 2024 beta base path should migrate to `/v1` before 2025.12. Embed customers must rotate signing secrets at least every 90 days.
