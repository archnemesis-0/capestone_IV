import duckdb

conn = duckdb.connect("../customer360.duckdb")

print(conn.execute("""
DESCRIBE bronze_customers
""").fetchdf())