# Discovering the Customer 360 Data Product

This capstone doesn't have a dedicated catalog tool (e.g. DataHub, Amundsen,
Unity Catalog) wired up — instead, discovery is file-based and DuckDB-native, which is
appropriate for the project's scope. This doc shows how a new consumer would find and
start using `customer_360` with what's already in the repo.

## 1. Find out the product exists

Start at [`data_product.md`](../data_product.md) in the repo root — it's the entry
point for anyone asking "what data products does this team publish?" It states the
product's purpose, owner, consumers, refresh cadence, and links out to the data
dictionary, lineage, and quality report.

## 2. Understand what's in it

The data dictionary in [`data_product.md`](../data_product.md#6-data-dictionary--customer_360)
lists every column, its type, and its meaning — enough to decide whether the table
answers your question without having to read pipeline code.

## 3. Confirm where the data comes from and how fresh it is

[`docs/lineage.md`](lineage.md) shows source-to-column lineage; the "Refresh" section of
`data_product.md` states this is currently a manual batch pipeline (not scheduled).

## 4. Check it's trustworthy

[`quality_report.md`](../quality_report.md) documents the automated pytest quality
suite (41 checks across Bronze/Silver/Gold/Customer 360) and the current pass/fail
result. A consumer can re-run `python -m pytest tests/ -v` themselves to verify the
table they're about to query is currently passing all checks.

## 5. Discover it programmatically (self-service, no docs needed)

Because `customer_360` lives in a DuckDB file, any consumer with read access to
`customer360.duckdb` can self-discover it without reading any documentation at all:

```python
import duckdb

con = duckdb.connect("customer360.duckdb", read_only=True)

# List every table in the warehouse
print(con.execute("SHOW TABLES").fetchdf())

# Inspect the schema of the product table
print(con.execute("DESCRIBE customer_360").fetchdf())

# Sample the data
print(con.execute("SELECT * FROM customer_360 LIMIT 5").fetchdf())
```

Table naming is a deliberate discovery aid: the `bronze_` / `silver_` / `gold_` prefixes
signal maturity/trust level, and the unprefixed `customer_360` name signals "this is the
finished product, not an intermediate table."

## 6. Consume it

The reference consumer is the Streamlit app — [`app/streamlit_app.py`](../app/streamlit_app.py)
— which queries `customer_360` directly (read-only) to power a customer search and
profile view. Run it with:

```bash
cd app
streamlit run streamlit_app.py
```

A new consumer building their own dashboard or notebook would follow the same pattern:
connect read-only to `customer360.duckdb`, query `customer_360`, and treat
`quality_report.md`'s pass/fail state as the trust signal before relying on the numbers.
