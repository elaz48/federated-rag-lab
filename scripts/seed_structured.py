"""Create and populate data/structured.sqlite with Meridian Analytics sample data.

Run from the repo root:
    uv run python scripts/seed_structured.py

Re-running is safe: tables are dropped and recreated.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Repo root = parent of scripts/
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "structured.sqlite"

# Plans align with data/docs/pricing-faq.md so multi-source questions work.
CUSTOMERS: list[tuple[int, str, str, float, str]] = [
    (1, "Acme Logistics", "Starter", 49.0, "2024-03-12"),
    (2, "Northwind Trading", "Professional", 199.0, "2023-11-02"),
    (3, "Brightside Clinics", "Enterprise", 899.0, "2023-06-18"),
    (4, "Harbor Freight Co", "Starter", 49.0, "2025-01-09"),
    (5, "Summit Retail Group", "Professional", 199.0, "2024-08-21"),
    (6, "Cedar Health Network", "Enterprise", 899.0, "2022-12-01"),
    (7, "Pinnacle Media", "Starter", 49.0, "2025-04-03"),
    (8, "Orbit Fintech", "Professional", 199.0, "2024-02-14"),
    (9, "Lumen Education", "Professional", 199.0, "2023-09-30"),
    (10, "Cascade Energy", "Enterprise", 899.0, "2024-05-07"),
    (11, "Bluebird Insurance", "Starter", 49.0, "2025-06-11"),
    (12, "Vertex Robotics", "Professional", 199.0, "2024-10-19"),
    (13, "Atlas Manufacturing", "Enterprise", 899.0, "2023-01-25"),
    (14, "Meadowlane Farms", "Starter", 49.0, "2025-02-28"),
    (15, "Quorum Legal", "Professional", 199.0, "2024-07-16"),
    (16, "Skyline Hotels", "Enterprise", 899.0, "2023-04-08"),
    (17, "Nova Software", "Starter", 49.0, "2025-03-22"),
    (18, "Riverstone Bank", "Enterprise", 899.0, "2022-08-15"),
]

# Flags align with product/security docs (SSO, exports, dashboards, API, etc.).
#
# Pilot override (intentional): customer 8 (Orbit Fintech, Professional) has
# sso=1 even though SSO is an Enterprise-only plan feature. Pricing FAQ notes
# that account teams can enable individual flags during pilots. Stage 04 eval
# uses this row as a multi-source / override case.
FEATURE_FLAGS: list[tuple[int, str, int]] = [
    (1, "api_access", 0),
    (1, "advanced_export", 0),
    (1, "sso", 0),
    (2, "api_access", 1),
    (2, "advanced_export", 1),
    (2, "custom_dashboards", 1),
    (2, "sso", 0),
    (3, "api_access", 1),
    (3, "advanced_export", 1),
    (3, "custom_dashboards", 1),
    (3, "sso", 1),
    (3, "dedicated_support", 1),
    (5, "api_access", 1),
    (5, "advanced_export", 0),
    (5, "custom_dashboards", 1),
    (6, "api_access", 1),
    (6, "sso", 1),
    (6, "dedicated_support", 1),
    (8, "api_access", 1),
    (8, "advanced_export", 1),
    (8, "sso", 1),  # pilot override: Professional + SSO
    (10, "api_access", 1),
    (10, "sso", 1),
    (10, "custom_dashboards", 1),
    (12, "api_access", 1),
    (12, "custom_dashboards", 0),
    (13, "api_access", 1),
    (13, "sso", 1),
    (13, "dedicated_support", 1),
    (15, "api_access", 1),
    (15, "advanced_export", 1),
    (16, "api_access", 1),
    (16, "sso", 1),
    (18, "api_access", 1),
    (18, "sso", 1),
    (18, "dedicated_support", 1),
    (18, "custom_dashboards", 1),
]


def seed(db_path: Path = DB_PATH) -> None:
    """Drop, recreate, and fill the structured knowledge base."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove stale file so a partial schema never lingers.
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                plan TEXT NOT NULL,
                mrr REAL NOT NULL,
                signup_date TEXT NOT NULL
            );

            CREATE TABLE feature_flags (
                customer_id INTEGER NOT NULL,
                flag TEXT NOT NULL,
                enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
                PRIMARY KEY (customer_id, flag),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );
            """
        )
        conn.executemany(
            "INSERT INTO customers (id, name, plan, mrr, signup_date) VALUES (?, ?, ?, ?, ?)",
            CUSTOMERS,
        )
        conn.executemany(
            "INSERT INTO feature_flags (customer_id, flag, enabled) VALUES (?, ?, ?)",
            FEATURE_FLAGS,
        )
        conn.commit()
    finally:
        conn.close()

    n_customers = len(CUSTOMERS)
    n_flags = len(FEATURE_FLAGS)
    print(f"Wrote {db_path}")
    print(f"  customers: {n_customers} rows")
    print(f"  feature_flags: {n_flags} rows")


if __name__ == "__main__":
    seed()
