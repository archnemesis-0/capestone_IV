# Customer 360 — Data Product Documentation

## 1. Purpose

`customer_360` gives ShopEasy a single, trusted, customer-grain view that unifies data
scattered across four operational systems (customer master data, orders, support
tickets, and web engagement). It answers, for any customer: who they are, how much
they've bought, how engaged they are with support and the web/app channels, what
segment they belong to, and whether they're currently active.

It exists so that teams stop pulling ad-hoc joins across raw source files and instead
consume one governed table with agreed-upon business rules already applied (dedup,
cleaning, segment/status logic).

## 2. Owner

**Data Quality / Analytics Engineering team** (this capstone team) is the product owner.
Day-to-day stewardship:

| Layer | Owner |
|---|---|
| Bronze / Silver (ingestion, cleaning, dedup) | Person 1 — Data Engineer |
| Gold / `customer_360` (metrics, segments, activity status) | Person 2 — Analytics Engineer |
| Quality validation (`tests/`, `quality_report.md`) | Person 3 — Data Quality Engineer |
| Product documentation, lineage, Streamlit consumer app | Person 4 — Data Product & Visualization Engineer |

Changes to business logic (segment thresholds, activity-status windows, dedup rules)
should go through whoever owns that layer, with quality checks in `tests/` re-run before
merging.

## 3. Consumers

- **Support / Success teams** — look up a customer's order history, ticket history, and
  activity status before a call.
- **Marketing** — target campaigns by `customer_segment` (e.g. re-engage `DORMANT`
  customers, reward `VIP`s).
- **Analytics / BI** — build dashboards and ad-hoc reports without re-deriving metrics
  from raw sources.
- **This capstone's Streamlit app** ([app/streamlit_app.py](app/streamlit_app.py)) — a
  reference consumer demonstrating search + profile lookups.

Any new consumer should read `customer_360` directly rather than joining the raw source
CSVs or Bronze tables — those are not governed and can contain the raw data issues
documented in [quality_report.md](quality_report.md).

## 4. Refresh

Currently a **manual, on-demand batch** pipeline. To refresh:

```bash
cd src
python build_bronze.py
python build_silver.py
python build_gold.py
python build_customer360.py
```

Then re-validate before treating the refresh as trustworthy:

```bash
python -m pytest tests/ -v
```

There is no scheduler wired up yet (out of scope for this capstone). If this became a
production pipeline, the natural next step would be an orchestrated daily/hourly job
that runs the four build scripts followed by the pytest quality gate, and blocks
downstream consumption if tests fail.

## 5. Business rules

These are the rules currently baked into the pipeline (see `src/build_silver.py`,
`src/build_gold.py`, `src/build_customer360.py` for implementation):

- **Customer identity**: one row per `customer_id` in the final table. Duplicate
  customer records are collapsed to the most recent `registration_date`
  (`silver_customers_dedup`).
- **Valid orders only**: orders with negative `order_amount` are dropped as invalid.
  Orders are deduplicated by `order_id`, keeping the most recent `order_date`.
- **Cancelled orders excluded from spend**: `total_orders`, `total_spend`, and
  `average_order_value` are computed from **active** orders only
  (`order_status <> 'CANCELLED'`).
- **Customer segment** (by `total_spend`):

  | Segment | Threshold |
  |---|---|
  | VIP | ≥ 100,000 |
  | HIGH_VALUE | ≥ 75,000 |
  | FREQUENT | ≥ 50,000 |
  | REGULAR | ≥ 25,000 |
  | OCCASIONAL | < 25,000 |

- **Customer activity status** (by recency of most recent activity — order, support
  ticket, or web event — relative to today):

  | Status | Rule |
  |---|---|
  | ACTIVE | last activity within 90 days |
  | DORMANT | last activity 91–365 days ago |
  | CHURNED | last activity more than 365 days ago |
  | NO_ACTIVITY | no orders, tickets, or events at all |

- **Support tickets**: `open_tickets_count`, `resolved_tickets_count`,
  `closed_tickets_count` are counted from `ticket_status` (`OPEN` / `RESOLVED` /
  `CLOSED`), standardized to uppercase.
- **Web events**: `web_events` counts distinct `event_id` per customer across all
  channels and event types.

## 6. Data dictionary — `customer_360`

| Column | Type | Description |
|---|---|---|
| `customer_id` | VARCHAR | Unique customer identifier (grain of the table). |
| `first_name` | VARCHAR | Customer first name. |
| `last_name` | VARCHAR | Customer last name. |
| `email` | VARCHAR | Normalized (lowercased, trimmed) email address. |
| `phone` | VARCHAR | Phone number; `'UNKNOWN'` if missing in source. |
| `customer_status` | VARCHAR | Account status from source system: `ACTIVE` / `INACTIVE`. Distinct from the computed `customer_activity_status` below. |
| `total_orders` | BIGINT | Count of distinct active (non-cancelled) orders. |
| `total_spend` | DOUBLE | Sum of `order_amount` across active orders. |
| `average_order_value` | DOUBLE | `total_spend / total_orders`; 0 if no orders. |
| `first_order_date` | TIMESTAMP | Date of the customer's earliest active order. |
| `last_order_date` | TIMESTAMP | Date of the customer's most recent active order. |
| `open_tickets_count` | BIGINT | Count of support tickets currently `OPEN`. |
| `resolved_tickets_count` | BIGINT | Count of support tickets `RESOLVED`. |
| `closed_tickets_count` | BIGINT | Count of support tickets `CLOSED`. |
| `web_events` | BIGINT | Total distinct web/app events (all types, all channels). |
| `customer_segment` | VARCHAR | Value-based segment: `VIP` / `HIGH_VALUE` / `FREQUENT` / `REGULAR` / `OCCASIONAL`. |
| `customer_activity_status` | VARCHAR | Recency-based status: `ACTIVE` / `DORMANT` / `CHURNED` / `NO_ACTIVITY`. |

## 7. Lineage

See [`docs/lineage.md`](docs/lineage.md) for the full source-to-field lineage mapping.

Summary:

```
customers.csv ─┐
orders.csv ─────┤
payments.csv ───┼─▶ Bronze (raw load, read_csv_auto) ─▶ Silver (clean, standardize,
support.csv ────┤                                        dedup, filter invalid)
web_events.csv ─┘                                              │
                                                                 ▼
                                              Gold (gold_customer_orders,
                                              gold_customer_support,
                                              gold_customer_engagement)
                                                                 │
                                                                 ▼
                                                          customer_360
                                                    (one row per customer)
```

## 8. Quality

See [`quality_report.md`](quality_report.md) for the full validation framework, checks,
and results (41/41 pytest checks passing as of the last pipeline run).

## 9. Catalog / discovery

See [`docs/catalog.md`](docs/catalog.md) for how a new consumer discovers and starts
using this data product.
