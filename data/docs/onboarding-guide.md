# Meridian Analytics — Onboarding Guide

This guide walks a new workspace from empty to first live dashboard. Most teams finish the happy path in under two hours.

## Day 0 — Workspace setup

1. Accept the invite email and set a strong password (or complete SSO if your org is on Enterprise).
2. Invite teammates from **Settings → Members**. Assign the **Admin**, **Editor**, or **Viewer** role.
3. Confirm your plan under **Settings → Billing**. Trial workspaces start on Professional features for 14 days.

## Day 1 — Connect a source

1. Open **Data → Connectors** and pick a first-class source (Snowflake, BigQuery, Postgres, HubSpot, Salesforce, or Stripe).
2. Use a read-only service account. Meridian never writes back to your warehouse.
3. Select the schemas or objects to sync. Start narrow (billing + CRM) and expand later.
4. Run **Test connection**, then **Start initial sync**. Large warehouses can take 15–60 minutes for the first pull.

## Day 1 — Define metrics

1. Open **Metrics → New metric**.
2. Give the metric a stable name (for example `mrr_recognized`) and a description stakeholders will understand.
3. Point it at a certified table or view. Prefer views owned by your data team.
4. Set the default aggregation and time grain (day / week / month).
5. Publish to the catalog. Unpublished metrics cannot appear on shared boards.

## Day 2 — First board and alert

1. Create a board from a template (**Revenue pulse** or **Customer health** work well).
2. Pin three to five metrics. Add one dimension breakout (region or plan).
3. Share the board with Viewers via link or Slack.
4. Create an anomaly monitor on your most important metric with a conservative threshold for the first week.

## Common pitfalls

- Connecting a write-capable warehouse user (security review will block it).
- Publishing metrics without owners — assign an owner so definitions do not rot.
- Building ten boards before validating one trusted metric.

When onboarding is complete, schedule a 30-minute workspace review with your admin and, on Enterprise, your CSM.
