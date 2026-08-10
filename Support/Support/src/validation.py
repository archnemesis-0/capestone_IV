import duckdb

conn = duckdb.connect("../customer360.duckdb")

print("===== REFERENTIAL INTEGRITY CHECKS =====")

# Orders must reference valid customers

invalid_orders = conn.execute("""
SELECT COUNT(*)
FROM silver_orders o
LEFT JOIN silver_customers_dedup c
ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
""").fetchone()[0]

print(f"Orders with invalid customer_id: {invalid_orders}")

# Support tickets must reference valid customers

invalid_tickets = conn.execute("""
SELECT COUNT(*)
FROM silver_customer_support s
LEFT JOIN silver_customers_dedup c
ON s.customer_id = c.customer_id
WHERE c.customer_id IS NULL
""").fetchone()[0]

print(f"Support tickets with invalid customer_id: {invalid_tickets}")


print("\n===== CUSTOMER QUALITY CHECKS =====")

null_customer_ids = conn.execute("""
SELECT COUNT(*)
FROM silver_customers_dedup
WHERE customer_id IS NULL
""").fetchone()[0]

print(f"Null customer_ids: {null_customer_ids}")

duplicate_customers = conn.execute("""
SELECT COUNT(*)
FROM (
    SELECT customer_id
    FROM silver_customers_dedup
    GROUP BY customer_id
    HAVING COUNT(*) > 1
)
""").fetchone()[0]

print(f"Duplicate customer_ids: {duplicate_customers}")


print("\n===== ORDER QUALITY CHECKS =====")

negative_orders = conn.execute("""
SELECT COUNT(*)
FROM silver_orders
WHERE order_amount < 0
""").fetchone()[0]

print(f"Negative order amounts: {negative_orders}")