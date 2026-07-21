# Meridian Analytics — Integrations Guide

Meridian connects to systems of record; it does not replace them. This guide lists supported connectors, auth patterns, and plan gates.

## First-class connectors

| Source | Auth | Sync modes | Notes |
|---|---|---|---|
| Snowflake | Key-pair or OAuth | Full + incremental | Prefer a read-only role on a warehouse dedicated to analytics. |
| BigQuery | Service account JSON | Full + incremental | Grant `bigquery.dataViewer` on selected datasets only. |
| Postgres | User/password or IAM | Full + incremental | Point at a replica when possible. |
| HubSpot | OAuth app | Incremental | Contacts, companies, deals. |
| Salesforce | OAuth connected app | Incremental | Accounts, opportunities, cases. |
| Stripe | Restricted API key | Incremental | Balance transactions and subscriptions. |

## Custom and HTTP sources

Enterprise workspaces can define **custom HTTP connectors** that poll a customer endpoint on a schedule. Payloads must be JSON arrays of objects with a stable primary key and an updated-at timestamp. Custom connectors are reviewed by Meridian solutions engineering on first enablement.

## Plan requirements

- All plans include the six first-class connectors above.
- **REST API access** requires Professional or Enterprise (or an explicit `api_access` flag).
- **Custom HTTP connectors** require Enterprise.
- **Advanced export** to customer object storage requires Professional or Enterprise.

## Operational guidance

- Rotate connector credentials at least every 90 days.
- Prefer network allowlisting of Meridian egress IPs for warehouse sources.
- After schema changes in the source, open **Data → Connectors → Refresh schema** so metric definitions stay valid.
- Failed syncs surface in **Data → Sync health**; three consecutive failures auto-pause the connector to protect warehouse load.

If a source you need is missing, contact support (Starter/Professional) or your CSM (Enterprise) to request a connector roadmap slot.
