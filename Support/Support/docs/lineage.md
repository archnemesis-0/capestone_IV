# Customer 360 — Data Lineage

Field-level lineage from source CSVs through Bronze → Silver → Gold → `customer_360`.

## Pipeline overview

| Stage | Script | Output |
|---|---|---|
| Bronze | [`src/build_bronze.py`](../src/build_bronze.py) | `bronze_customers`, `bronze_orders`, `bronze_payments`, `bronze_customer_support`, `bronze_web_events` |
| Silver | [`src/build_silver.py`](../src/build_silver.py) | `silver_customers`, `silver_customers_dedup`, `silver_orders`, `silver_orders_active`, `silver_payments`, `silver_customer_support`, `silver_web_events` |
| Gold | [`src/build_gold.py`](../src/build_gold.py) | `gold_customer_orders`, `gold_customer_support`, `gold_customer_engagement` |
| Product | [`src/build_customer360.py`](../src/build_customer360.py) | `customer_360` |

Every Silver, Gold, and product-layer table is derived exclusively from the layer
directly beneath it — no stage skips a layer.

## Source → Bronze

Straight, untransformed load of each CSV via DuckDB `read_csv_auto`, one table per file:

| Source file | Bronze table |
|---|---|
| `data/source/customers.csv` | `bronze_customers` |
| `data/source/orders.csv` | `bronze_orders` |
| `data/source/payments.csv` | `bronze_payments` |
| `data/source/customer_support.csv` | `bronze_customer_support` |
| `data/source/web_events.csv` | `bronze_web_events` |

## Bronze → Silver

| Silver table | Built from | Transformations |
|---|---|---|
| `silver_customers` | `bronze_customers` | Trim `customer_id`/`first_name`/`last_name`; lowercase+trim `email`; `COALESCE(phone, 'UNKNOWN')`; uppercase+trim `state`; uppercase+trim `customer_status`. |
| `silver_customers_dedup` | `silver_customers` | `ROW_NUMBER()` partitioned by `customer_id`, ordered by `registration_date DESC` — keeps most recent record per customer. |
| `silver_orders` | `bronze_orders` | Drops `order_amount < 0` (invalid); `ROW_NUMBER()` partitioned by `order_id`, ordered by `order_date DESC` — dedups. |
| `silver_orders_active` | `silver_orders` | Excludes `order_status = 'CANCELLED'`; standardizes `order_status` to uppercase. |
| `silver_payments` | `bronze_payments` | Standardizes `payment_status` to uppercase. |
| `silver_customer_support` | `bronze_customer_support` | Standardizes `category` and `ticket_status` to uppercase+trim. |
| `silver_web_events` | `bronze_web_events` | Standardizes `event_type` and `channel` to uppercase+trim. |

## Silver → Gold

| Gold table | Built from | Aggregation |
|---|---|---|
| `gold_customer_orders` | `silver_orders_active` | Group by `customer_id`: `total_orders` (nunique `order_id`), `total_spend` (sum `order_amount`), `average_order_value` (mean `order_amount`), `first_order_date`/`last_order_date` (min/max `order_date`). |
| `gold_customer_support` | `silver_customer_support` | Group by `customer_id`: `ticket_counts` (nunique `ticket_id`), `first_ticket_date`/`last_ticket_date`, plus `resolved_tickets_count` / `closed_tickets_count` / `open_tickets_count` from status-filtered sub-aggregations. |
| `gold_customer_engagement` | `silver_web_events` | Group by `customer_id`: `web_events` (nunique `event_id`), `first_event_date`/`last_event_date`, plus per-`event_type` and per-`channel` pivoted counts (`cart_events`, `login_events`, `page_view_events`, `product_view_events`, `search_events`, `email_events`, `mobile_events`, `web_channel_events`). |

`silver_payments` is loaded and cleaned but **not currently joined into Gold or
`customer_360`** — payment status/amount is not part of the current Customer 360 model.

## Gold → `customer_360`

Base: `silver_customers_dedup` (`customer_id`, `first_name`, `last_name`, `email`,
`phone`, `customer_status`), left-joined with:

| customer_360 column(s) | Source |
|---|---|
| `total_orders`, `total_spend`, `average_order_value`, `first_order_date`, `last_order_date` | `gold_customer_orders` |
| `open_tickets_count`, `resolved_tickets_count`, `closed_tickets_count` | `gold_customer_support` |
| `web_events` | `gold_customer_engagement` |
| `customer_segment` | Derived in `build_customer360.py` from `total_spend` thresholds. |
| `customer_activity_status` | Derived in `build_customer360.py` from the max of `last_order_date` (orders), `last_ticket_date` (`gold_customer_support`), and `last_event_date` (`gold_customer_engagement`), compared to today's date. |

All numeric fields (`open_tickets_count`, `resolved_tickets_count`,
`closed_tickets_count`, `web_events`, `total_orders`, `total_spend`,
`average_order_value`) are null-filled to 0 for customers with no matching activity in
that domain (e.g. a customer with no support tickets gets `0` for all ticket counts,
not `NULL`).

## Column-level lineage summary

| `customer_360` column | Ultimately traces back to |
|---|---|
| `customer_id`, `first_name`, `last_name`, `email`, `phone`, `customer_status` | `customers.csv` |
| `total_orders`, `total_spend`, `average_order_value`, `first_order_date`, `last_order_date` | `orders.csv` |
| `open_tickets_count`, `resolved_tickets_count`, `closed_tickets_count` | `customer_support.csv` |
| `web_events` | `web_events.csv` |
| `customer_segment` | `orders.csv` (derived, via `total_spend`) |
| `customer_activity_status` | `orders.csv` + `customer_support.csv` + `web_events.csv` (derived, via most recent activity date) |

`payments.csv` currently has no downstream lineage into `customer_360`.
