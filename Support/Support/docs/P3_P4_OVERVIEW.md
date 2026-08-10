# Person 3 & Person 4 — Task Overview

## Person 3: Data Quality Engineer

**Goal:** validate that the Bronze → Silver → Gold → Customer 360 pipeline produces
trustworthy data.

| Task | Delivered as |
|---|---|
| Quality validation framework | [tests/conftest.py](tests/conftest.py) — read-only DuckDB fixture shared across all test files |
| Pytest-based tests | [tests/test_bronze.py](tests/test_bronze.py), [test_silver.py](tests/test_silver.py), [test_gold.py](tests/test_gold.py), [test_customer360.py](tests/test_customer360.py) |
| Data quality checks | 41 checks — nulls, duplicates, referential integrity, value ranges, cross-table reconciliation, required-field/enum validation (spec required ≥5) |
| Execute & document results | [tests/pytest_results.txt](tests/pytest_results.txt) — 41/41 passing |
| Quality report | [quality_report.md](quality_report.md) — methodology, results, findings (incl. the missing `customer_activity_status` fix) |
| Present findings | `quality_report.md` is presentation-ready; live walkthrough is on the presenter |

**Run it:** `python -m pytest tests/ -v`

## Person 4: Data Product & Visualization Engineer

**Goal:** package Customer 360 as a documented, discoverable, consumable data product.

| Task | Delivered as |
|---|---|
| Product documentation | [data_product.md](data_product.md) — purpose, owner, consumers, refresh, business rules, data dictionary |
| Data lineage documentation | [docs/lineage.md](docs/lineage.md) — source CSV → Bronze → Silver → Gold → `customer_360`, field-level |
| Streamlit application | [app/streamlit_app.py](app/streamlit_app.py) — connects to `customer_360` (fixed a wrong DB path and wrong table name in the starter stub) |
| Customer search & profile view | Sidebar search (name/email/ID) + segment/activity filters, results table, full profile view (identity, orders, support, engagement, segment, activity status) |
| Catalog / consumption demo | [docs/catalog.md](docs/catalog.md) — how a new consumer discovers and starts using `customer_360`; the Streamlit app is the reference consumer |

**Run it:** `cd app && streamlit run streamlit_app.py`

## How the two connect

Person 4's product documentation links directly to Person 3's `quality_report.md` as
the trust signal a consumer checks before relying on `customer_360` — the data product
isn't just described, it's backed by an automated, re-runnable quality gate.
