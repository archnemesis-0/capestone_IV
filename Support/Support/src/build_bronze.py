import duckdb

conn = duckdb.connect("../customer360.duckdb")

conn.execute("""
CREATE OR REPLACE TABLE bronze_customers AS
SELECT *
FROM read_csv_auto('../data/source/customers.csv');
""")

conn.execute("""
CREATE OR REPLACE TABLE bronze_orders AS
SELECT *
FROM read_csv_auto('../data/source/orders.csv');
""")


conn.execute("""
CREATE OR REPLACE TABLE bronze_payments AS
SELECT *
FROM read_csv_auto('../data/source/payments.csv');
""")


conn.execute("""
CREATE OR REPLACE TABLE bronze_customer_support AS
SELECT *
FROM read_csv_auto('../data/source/customer_support.csv');
""")

conn.execute("""
CREATE OR REPLACE TABLE bronze_web_events AS
SELECT *
FROM read_csv_auto('../data/source/web_events.csv');
""")

print("Bronze tables created successfully!")