import duckdb

conn = duckdb.connect("../customer360.duckdb")

conn.execute("""
CREATE OR REPLACE TABLE silver_customers AS
SELECT
    TRIM(customer_id) AS customer_id,
    TRIM(first_name) AS first_name,
    TRIM(last_name) AS last_name,
    LOWER(TRIM(email)) AS email,
    COALESCE(phone, 'UNKNOWN') AS phone,
    UPPER(TRIM(state)) AS state,
    registration_date,
    UPPER(TRIM(customer_status)) AS customer_status
FROM bronze_customers
""")

conn.execute("""
CREATE OR REPLACE TABLE silver_customers_dedup AS
SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY customer_id
               ORDER BY registration_date DESC
           ) rn
    FROM silver_customers
)
WHERE rn = 1
""")

conn.execute("""
CREATE OR REPLACE TABLE silver_orders AS
SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY order_id
               ORDER BY order_date DESC
           ) rn
    FROM bronze_orders
    WHERE order_amount >= 0
)
WHERE rn = 1
""")

conn.execute("""
CREATE OR REPLACE TABLE silver_orders_active AS
SELECT
    order_id,
    customer_id,
    order_date,
    order_amount,
    UPPER(TRIM(order_status)) AS order_status
FROM silver_orders
WHERE UPPER(TRIM(order_status)) <> 'CANCELLED'
""")


conn.execute("""
CREATE OR REPLACE TABLE silver_payments AS
SELECT
    payment_id,
    order_id,
    payment_date,
    payment_amount,
    UPPER(TRIM(payment_status)) AS payment_status
FROM bronze_payments
""")


conn.execute("""
CREATE OR REPLACE TABLE silver_customer_support AS
SELECT
    ticket_id,
    customer_id,
    ticket_date,
    UPPER(TRIM(category)) AS category,
    UPPER(TRIM(ticket_status)) AS ticket_status
FROM bronze_customer_support
""")


conn.execute("""
CREATE OR REPLACE TABLE silver_web_events AS
SELECT
    event_id,
    customer_id,
    event_date,
    UPPER(TRIM(event_type)) AS event_type,
    UPPER(TRIM(channel)) AS channel
FROM bronze_web_events
""")


tables = [
    "silver_customers",
    "silver_customers_dedup",
    "silver_orders",
    "silver_orders_active",
    "silver_payments",
    "silver_customer_support",
    "silver_web_events"
]

print("\n===== SILVER TABLE COUNTS =====")

for table in tables:
    count = conn.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {count}")

print("\nSilver Layer Build Complete!")
