from conftest import row_count, scalar


def test_silver_customers_dedup_has_no_duplicate_customer_ids(conn):
    duplicates = scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT customer_id
            FROM silver_customers_dedup
            GROUP BY customer_id
            HAVING COUNT(*) > 1
        )
    """)
    assert duplicates == 0


def test_silver_customers_dedup_has_no_null_customer_ids(conn):
    nulls = scalar(conn, "SELECT COUNT(*) FROM silver_customers_dedup WHERE customer_id IS NULL")
    assert nulls == 0


def test_silver_customers_dedup_row_count_not_greater_than_bronze(conn):
    assert row_count(conn, "silver_customers_dedup") <= row_count(conn, "bronze_customers")


def test_silver_customers_email_is_lowercase(conn):
    non_lowercase = scalar(conn, """
        SELECT COUNT(*)
        FROM silver_customers_dedup
        WHERE email IS NOT NULL AND email <> LOWER(email)
    """)
    assert non_lowercase == 0


def test_silver_customers_phone_is_never_null(conn):
    nulls = scalar(conn, "SELECT COUNT(*) FROM silver_customers_dedup WHERE phone IS NULL")
    assert nulls == 0


def test_silver_customers_status_is_standardized(conn):
    bad_status = scalar(conn, """
        SELECT COUNT(*)
        FROM silver_customers_dedup
        WHERE customer_status NOT IN ('ACTIVE', 'INACTIVE')
    """)
    assert bad_status == 0


def test_silver_orders_has_no_negative_amounts(conn):
    negative = scalar(conn, "SELECT COUNT(*) FROM silver_orders WHERE order_amount < 0")
    assert negative == 0


def test_silver_orders_has_no_duplicate_order_ids(conn):
    duplicates = scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT order_id
            FROM silver_orders
            GROUP BY order_id
            HAVING COUNT(*) > 1
        )
    """)
    assert duplicates == 0


def test_silver_orders_active_excludes_cancelled(conn):
    cancelled = scalar(conn, "SELECT COUNT(*) FROM silver_orders_active WHERE order_status = 'CANCELLED'")
    assert cancelled == 0


def test_silver_orders_reference_valid_customers(conn):
    orphans = scalar(conn, """
        SELECT COUNT(*)
        FROM silver_orders o
        LEFT JOIN silver_customers_dedup c ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)
    assert orphans == 0


def test_silver_customer_support_reference_valid_customers(conn):
    orphans = scalar(conn, """
        SELECT COUNT(*)
        FROM silver_customer_support s
        LEFT JOIN silver_customers_dedup c ON s.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)
    assert orphans == 0


def test_silver_web_events_reference_valid_customers(conn):
    orphans = scalar(conn, """
        SELECT COUNT(*)
        FROM silver_web_events w
        LEFT JOIN silver_customers_dedup c ON w.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)
    assert orphans == 0


def test_silver_customer_support_status_is_standardized(conn):
    bad_status = scalar(conn, """
        SELECT COUNT(*)
        FROM silver_customer_support
        WHERE ticket_status NOT IN ('OPEN', 'RESOLVED', 'CLOSED')
    """)
    assert bad_status == 0
