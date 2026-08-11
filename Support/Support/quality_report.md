# Customer 360 — Data Quality Report

**Author:** Person 3 — Data Quality Engineer
**Pipeline:** Bronze → Silver → Gold → Customer 360 (`customer360.duckdb`)
**Test framework:** `pytest` (`tests/`)
**Result:** 41 / 41 checks passed

## 1. Scope

This report documents the data quality validation framework built for the Customer 360
pipeline. It covers:

- Source profiling findings carried over from Person 1's work (for traceability)
- The automated pytest suite that validates Bronze, Silver, Gold, and Customer 360
- Test execution results
- Known findings and their disposition

## 2. Source data profiling (recap)

| File | Rows | Nulls | Duplicate rows |
|---|---|---|---|
| customers.csv | 121 | `phone`: 1 | 1 |
| orders.csv | 421 | none | 1 |
| payments.csv | 440 | none | 0 |
| customer_support.csv | 180 | none | 0 |
| web_events.csv | 600 | none | 0 |

Additional source-level issues identified:
- `bronze_orders` contains **1 negative `order_amount`** (invalid).
- `bronze_orders` contains **1 duplicate `order_id`**.
- `bronze_customers` contains **1 duplicate `customer_id`**.

All of the above are handled by the Silver layer (dedup by latest `registration_date` /
`order_date`, and a `order_amount >= 0` filter), and are re-verified by the pytest suite
below rather than trusted at face value.

## 3. Validation framework

Tests live under [`tests/`](tests/) and connect **read-only** to the existing
`customer360.duckdb` (the suite validates pipeline output; it does not rebuild the
pipeline). Run with:

```bash
python -m pytest tests/ -v
```

Structure — one file per pipeline layer, so a failure immediately indicates where in the
pipeline the issue originates:

| File | Layer | Checks |
|---|---|---|
| [`tests/test_bronze.py`](tests/test_bronze.py) | Bronze | 11 |
| [`tests/test_silver.py`](tests/test_silver.py) | Silver | 13 |
| [`tests/test_gold.py`](tests/test_gold.py) | Gold | 7 |
| [`tests/test_customer360.py`](tests/test_customer360.py) | Customer 360 | 10 |

### 3.1 Bronze checks
- Every Bronze table exists and is non-empty.
- Every Bronze table's row count matches its source CSV exactly (raw load fidelity — no
  rows silently dropped or duplicated on ingest).
- `bronze_customers` has the expected column set.

### 3.2 Silver checks
- `silver_customers_dedup` has no duplicate or null `customer_id`.
- `silver_customers_dedup` row count never exceeds `bronze_customers` (dedup only removes).
- `email` is normalized to lowercase.
- `phone` is never null (nulls coalesced to `'UNKNOWN'`).
- `customer_status` is standardized to `{ACTIVE, INACTIVE}`.
- `silver_orders` has no negative `order_amount` and no duplicate `order_id`.
- `silver_orders_active` never contains `CANCELLED` orders.
- Referential integrity: every `customer_id` in `silver_orders`, `silver_customer_support`,
  and `silver_web_events` exists in `silver_customers_dedup`.
- `ticket_status` is standardized to `{OPEN, RESOLVED, CLOSED}`.

### 3.3 Gold checks
- `gold_customer_orders` / `gold_customer_engagement` have one row per `customer_id`.
- No negative `total_spend`.
- `average_order_value` reconciles with `total_spend / total_orders`.
- `gold_customer_support.ticket_counts` reconciles with
  `open + resolved + closed` ticket counts (no double counting / dropped tickets).
- No negative ticket counts.
- `gold_customer_engagement.web_events` reconciles with the sum of its per-event-type
  breakdown columns.

### 3.4 Customer 360 checks
- All fields required by the project spec are present: `customer_id`, `total_orders`,
  `total_spend`, `average_order_value`, `first_order_date`, `last_order_date`,
  `open_tickets_count`, `resolved_tickets_count`, `web_events`, `customer_segment`,
  `customer_activity_status`.
- Exactly one row per `customer_id` (grain check).
- Row count matches `silver_customers_dedup` (no customers lost or duplicated in the join).
- No null `customer_id`.
- No negative `total_spend`, `total_orders`, or `average_order_value`.
- `customer_segment` values are restricted to the defined set
  `{VIP, HIGH_VALUE, FREQUENT, REGULAR, OCCASIONAL}`.
- `customer_activity_status` values are restricted to the defined set
  `{ACTIVE, DORMANT, CHURNED, NO_ACTIVITY}` and is never null.
- `first_order_date` is never after `last_order_date`.
- Customers with zero orders have zero spend (no orphaned monetary values).

## 4. Test execution results

```
$ python -m pytest tests/ -v
collected 41 items

tests/test_bronze.py::test_bronze_table_exists_and_not_empty[bronze_customers] PASSED
tests/test_bronze.py::test_bronze_table_exists_and_not_empty[bronze_orders] PASSED
tests/test_bronze.py::test_bronze_table_exists_and_not_empty[bronze_payments] PASSED
tests/test_bronze.py::test_bronze_table_exists_and_not_empty[bronze_customer_support] PASSED
tests/test_bronze.py::test_bronze_table_exists_and_not_empty[bronze_web_events] PASSED
tests/test_bronze.py::test_bronze_row_count_matches_source_csv[...] PASSED (x5)
tests/test_bronze.py::test_bronze_customers_has_expected_columns PASSED
tests/test_customer360.py (10 tests) PASSED
tests/test_gold.py (7 tests) PASSED
tests/test_silver.py (13 tests) PASSED

============================== 41 passed in 0.78s ==============================
```

Full log: [`tests/pytest_results.txt`](tests/pytest_results.txt).

**41 / 41 checks passed.** No data quality failures detected in the current build of
`customer360.duckdb`.

## 5. Findings

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | `customer_360` was missing the required `customer_activity_status` field (STUDENT_TASK.md Task 5 / `sql/customer360_tasks.sql` item 8). | High — required deliverable field absent | **Fixed** — added to `src/build_customer360.py`. Derived from recency of the most recent activity (order, ticket, or web event) vs. today: `ACTIVE` ≤ 90 days, `DORMANT` 91–365 days, `CHURNED` > 365 days, `NO_ACTIVITY` if the customer has no activity at all. |
| 2 | Source `customers.csv` contains 1 duplicate row and 1 null `phone`. | Low — handled downstream | Resolved by Silver dedup and `COALESCE(phone, 'UNKNOWN')`; covered by `test_silver_customers_dedup_has_no_duplicate_customer_ids` and `test_silver_customers_phone_is_never_null`. |
| 3 | Source `orders.csv` contains 1 negative `order_amount` and 1 duplicate `order_id`. | Medium — invalid financial data if unfiltered | Resolved by Silver's `order_amount >= 0` filter and `ROW_NUMBER()` dedup; covered by `test_silver_orders_has_no_negative_amounts` and `test_silver_orders_has_no_duplicate_order_ids`. |
| 4 | `src/validation.py` (pre-existing) performs similar checks via print statements, not asserted/automated. | Low — informational only, no CI signal | Superseded by the pytest suite in `tests/`, which is automatable and gives pass/fail signal. `src/validation.py` can be retired once the team confirms the pytest suite covers its checks (it does). |

## 6. Current customer_360 distribution (for sanity, not a formal test)

**customer_segment**

| Segment | Customers |
|---|---|
| OCCASIONAL | 37 |
| REGULAR | 36 |
| FREQUENT | 22 |
| HIGH_VALUE | 16 |
| VIP | 9 |

**customer_activity_status**

| Status | Customers |
|---|---|
| ACTIVE | 114 |
| DORMANT | 6 |
| CHURNED | 0 |
| NO_ACTIVITY | 0 |

(Total: 120 customers, matching `silver_customers_dedup` row count.)

## 7. Recommendations for the team

- Re-run `python -m pytest tests/ -v` after any change to `src/build_*.py` before
  committing — treat it as the gate for pipeline changes.
- If `generate_data.py` is re-run to produce a new random dataset, re-run the full
  pipeline (`build_bronze.py` → `build_silver.py` → `build_gold.py` →
  `build_customer360.py`) and then the test suite, since row counts and distributions
  will change.
- Consider retiring `src/validation.py` in favor of `tests/`, since it duplicates checks
  without giving a pass/fail signal.
