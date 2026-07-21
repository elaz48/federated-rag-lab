uv run python 02-router/ask.py "What plan is Orbit Fintech on, and is SSO enabled for them?"


=== Route ===
source: sql
reason: The question specifically asks for a named customer's plan and feature flags.

=== Retrieved context ===

--- snippet 1 | structured.sqlite ---
SQL:
SELECT c.plan, f.enabled 
FROM customers c 
LEFT JOIN feature_flags f ON c.id = f.customer_id 
WHERE c.name = 'Orbit Fintech' AND f.flag = 'SSO';

Rows (0):
[]

=== Answer ===
I do not know.




uv run python 02-router/ask.py "What does the Professional plan include?"


=== Route ===
source: docs
reason: The Professional plan details are part of the product documentation.

=== Retrieved context ===

--- snippet 1 | integrations.md ---
## Plan requirements

- All plans include the six first-class connectors above.
- **REST API access** requires Professional or Enterprise (or an explicit `api_access` flag).
- **Custom HTTP connectors** require Enterprise.
- **Advanced export** to customer object storage requires Professional or Enterprise.

## Operational guidance

--- snippet 2 | pricing-faq.md ---
## Which plan should we pick?

- Choose **Starter** if you need a few shared boards and CSV exports.
- Choose **Professional** if you need the API, advanced export, or more seats and monitors.
- Choose **Enterprise** if you require SSO, custom connectors, or a dedicated customer success manager.

--- snippet 3 | pricing-faq.md ---
**Do feature flags override the plan matrix?** Account teams can enable individual flags (for example early API access) for specific customers during pilots. Unless a flag is enabled in the customer record, plan limits apply as written above.

**What payment methods are accepted?** Credit card for Starter and Professional. Enterprise invoices via ACH or wire on Net-30 terms.

## Which plan should we pick?

--- snippet 4 | support-sla.md ---
Enterprise customers with the `dedicated_support` flag also receive a quarterly business review and a shared success plan. Uptime SLA for the core app is 99.9% monthly for Professional and Enterprise; Starter is best effort. SLA credits, when applicable, are described in the master subscription agreement—not in this public summary.

=== Answer ===
The Professional plan includes API access, advanced export, more seats, and monitors.




uv run python 02-router/ask.py "Which plan is customer Orbit Fintech on, and what does that plan include?"


=== Route ===
source: sql
reason: The question specifically asks for a named customer's plan.

=== Retrieved context ===

--- snippet 1 | structured.sqlite ---
SQL:
SELECT plan FROM customers WHERE name = 'Orbit Fintech';

Rows (1):
[{'plan': 'Professional'}]

=== Answer ===
Customer Orbit Fintech is on the 'Professional' plan. I do not know what that plan includes.

