"""Read-only SQLite helpers + schema text for the text-to-SQL writer.

Shared by stages 02 and 03 so both get the same safety guards and the same
value vocabulary (flag names / plan labels are case-sensitive in this DB).
"""

from __future__ import annotations

import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

from common.loaders import repo_root

DB_PATH = repo_root() / "data" / "structured.sqlite"

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|"
    r"REPLACE|TRUNCATE|GRANT|REVOKE|PRAGMA|VACUUM|REINDEX)\b",
    re.I,
)


def assert_readonly_select(sql: str) -> str:
    """Teaching-grade guard: single SELECT only (not a production firewall)."""
    cleaned = sql.strip().rstrip(";")
    if not cleaned.upper().startswith("SELECT"):
        raise ValueError(f"Only SELECT allowed; got: {sql!r}")
    if ";" in cleaned or _FORBIDDEN.search(cleaned):
        raise ValueError(f"Forbidden SQL: {sql!r}")
    return cleaned


def run_select(sql: str, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Missing {db_path}. Run: uv run python scripts/seed_structured.py"
        )
    safe = assert_readonly_select(sql)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(safe).fetchall()]
    finally:
        conn.close()


@lru_cache(maxsize=1)
def value_vocabulary(db_path: str | None = None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Distinct plan labels and flag names currently in the DB (runtime query)."""
    path = Path(db_path) if db_path else DB_PATH
    plans = tuple(
        r["plan"] for r in run_select("SELECT DISTINCT plan FROM customers ORDER BY plan", path)
    )
    flags = tuple(
        r["flag"]
        for r in run_select(
            "SELECT DISTINCT flag FROM feature_flags ORDER BY flag", path
        )
    )
    return plans, flags


@lru_cache(maxsize=1)
def customer_names(db_path: str | None = None) -> tuple[str, ...]:
    """Customer names present in the DB — used by the federated router catalog."""
    path = Path(db_path) if db_path else DB_PATH
    return tuple(
        r["name"]
        for r in run_select("SELECT name FROM customers ORDER BY name", path)
    )


def router_source_catalog(db_path: Path | None = None) -> str:
    """One-line-per-source inventory for the multi-source router.

    Topic labels alone are not enough: the router must know *what records*
    sql holds (named customers) vs what *rules* docs hold.
    """
    path = db_path or DB_PATH
    names = ", ".join(customer_names(str(path)))
    return f"""
Source inventory:
- sql: per-customer records — plan, MRR, signup_date, and feature_flag rows
  (enabled 0/1). Customers currently in the database: {names}.
- docs: product rules, pricing matrix, plan contents, security/SSO policy,
  onboarding, integrations, release notes, and support SLAs. No per-customer data.

Routing rules (decide by what data the answer needs, not by topic alone):
- If the question names a specific customer, sql is required.
- If the question asks about rules, policies, plan contents, or product
  behavior, docs is required.
- Many questions need BOTH (customer fact + policy/plan explanation), e.g.
  "Is customer X allowed to use SSO, and why?" or "What plan is X on and what
  does that plan include?".
""".strip()


def schema_for_sql_writer(db_path: Path | None = None) -> str:
    """Table shapes PLUS exact value vocabulary for WHERE clauses.

    Schemas alone are not enough: models often write flag = 'SSO' when the
    stored value is 'sso'. Listing live distinct values fixes that class of miss.
    """
    path = db_path or DB_PATH
    plans, flags = value_vocabulary(str(path))
    plan_list = ", ".join(repr(p) for p in plans)
    flag_list = ", ".join(repr(f) for f in flags)
    return f"""
SQLite schema (read-only):
  customers(id INT, name TEXT, plan TEXT, mrr REAL, signup_date TEXT)
  feature_flags(customer_id INT, flag TEXT, enabled INT)  -- enabled is 0 or 1
  Join: feature_flags.customer_id = customers.id

Exact value vocabulary (case-sensitive — use these literals only):
  customers.plan: {plan_list}
  feature_flags.flag: {flag_list}

Rules:
  - Write one SELECT. No writes, PRAGMA, or multiple statements.
  - Prefer explicit column lists.
  - Match string literals exactly (e.g. flag = 'sso', not 'SSO').
""".strip()
