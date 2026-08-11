from conftest import row_count, scalar

REQUIRED_COLUMNS = {
    "customer_id",
    "total_orders",
    "total_spend",
    "average_order_value",
    "first_order_date",
    "last_order_date",
    "open_tickets_count",
    "resolved_tickets_count",
    "web_events",
    "customer_segment",
    "customer_activity_status",
}

VALID_SEGMENTS = {"VIP", "HIGH_VALUE", "FREQUENT", "REGULAR", "OCCASIONAL"}
VALID_ACTIVITY_STATUSES = {"ACTIVE", "DORMANT", "CHURNED", "NO_ACTIVITY"}


def test_customer_360_has_required_columns(conn):
    columns = {r[0] for r in conn.execute("DESCRIBE customer_360").fetchall()}
    missing = REQUIRED_COLUMNS - columns
    assert not missing, f"customer_360 is missing required columns: {missing}"


def test_customer_360_has_one_row_per_customer(conn):
    duplicates = scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT customer_id
            FROM customer_360
            GROUP BY customer_id
            HAVING COUNT(*) > 1
        )
    """)
    assert duplicates == 0


def test_customer_360_row_count_matches_silver_customers_dedup(conn):
    assert row_count(conn, "customer_360") == row_count(conn, "silver_customers_dedup")


def test_customer_360_has_no_null_customer_ids(conn):
    nulls = scalar(conn, "SELECT COUNT(*) FROM customer_360 WHERE customer_id IS NULL")
    assert nulls == 0


def test_customer_360_has_no_negative_spend_or_orders(conn):
    negative = scalar(conn, """
        SELECT COUNT(*)
        FROM customer_360
        WHERE total_spend < 0 OR total_orders < 0 OR average_order_value < 0
    """)
    assert negative == 0


def test_customer_360_segment_values_are_valid(conn):
    segments = {r[0] for r in conn.execute("SELECT DISTINCT customer_segment FROM customer_360").fetchall()}
    assert segments.issubset(VALID_SEGMENTS)


def test_customer_360_activity_status_values_are_valid(conn):
    statuses = {r[0] for r in conn.execute("SELECT DISTINCT customer_activity_status FROM customer_360").fetchall()}
    assert statuses.issubset(VALID_ACTIVITY_STATUSES)


def test_customer_360_activity_status_is_never_null(conn):
    nulls = scalar(conn, "SELECT COUNT(*) FROM customer_360 WHERE customer_activity_status IS NULL")
    assert nulls == 0


def test_customer_360_first_order_not_after_last_order(conn):
    inverted = scalar(conn, """
        SELECT COUNT(*)
        FROM customer_360
        WHERE first_order_date IS NOT NULL
          AND last_order_date IS NOT NULL
          AND first_order_date > last_order_date
    """)
    assert inverted == 0


def test_customer_360_customers_with_no_orders_have_zero_spend(conn):
    inconsistent = scalar(conn, """
        SELECT COUNT(*)
        FROM customer_360
        WHERE total_orders = 0 AND (total_spend <> 0 OR average_order_value <> 0)
    """)
    assert inconsistent == 0
