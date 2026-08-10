import pandas as pd
import pytest

from conftest import SOURCE_DIR, row_count

BRONZE_TABLES = {
    "bronze_customers": "customers.csv",
    "bronze_orders": "orders.csv",
    "bronze_payments": "payments.csv",
    "bronze_customer_support": "customer_support.csv",
    "bronze_web_events": "web_events.csv",
}


@pytest.mark.parametrize("table", BRONZE_TABLES.keys())
def test_bronze_table_exists_and_not_empty(conn, table):
    assert row_count(conn, table) > 0, f"{table} is empty"


@pytest.mark.parametrize("table,source_file", BRONZE_TABLES.items())
def test_bronze_row_count_matches_source_csv(conn, table, source_file):
    expected = len(pd.read_csv(SOURCE_DIR / source_file))
    actual = row_count(conn, table)
    assert actual == expected, (
        f"{table} has {actual} rows, source {source_file} has {expected} rows"
    )


def test_bronze_customers_has_expected_columns(conn):
    columns = {r[0] for r in conn.execute("DESCRIBE bronze_customers").fetchall()}
    expected = {
        "customer_id", "first_name", "last_name", "email",
        "phone", "state", "registration_date", "customer_status",
    }
    assert expected.issubset(columns)
