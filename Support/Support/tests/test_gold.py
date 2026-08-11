from conftest import scalar


def test_gold_customer_orders_has_no_duplicate_customers(conn):
    duplicates = scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT customer_id
            FROM gold_customer_orders
            GROUP BY customer_id
            HAVING COUNT(*) > 1
        )
    """)
    assert duplicates == 0


def test_gold_customer_orders_has_no_negative_spend(conn):
    negative = scalar(conn, "SELECT COUNT(*) FROM gold_customer_orders WHERE total_spend < 0")
    assert negative == 0


def test_gold_customer_orders_average_order_value_is_consistent(conn):
    inconsistent = scalar(conn, """
        SELECT COUNT(*)
        FROM gold_customer_orders
        WHERE total_orders > 0
          AND ABS(average_order_value - (total_spend / total_orders)) > 0.01
    """)
    assert inconsistent == 0


def test_gold_customer_support_ticket_counts_reconcile(conn):
    mismatched = scalar(conn, """
        SELECT COUNT(*)
        FROM gold_customer_support
        WHERE ticket_counts <> (resolved_tickets_count + closed_tickets_count + open_tickets_count)
    """)
    assert mismatched == 0


def test_gold_customer_support_has_no_negative_ticket_counts(conn):
    negative = scalar(conn, """
        SELECT COUNT(*)
        FROM gold_customer_support
        WHERE open_tickets_count < 0 OR resolved_tickets_count < 0 OR closed_tickets_count < 0
    """)
    assert negative == 0


def test_gold_customer_engagement_has_no_duplicate_customers(conn):
    duplicates = scalar(conn, """
        SELECT COUNT(*) FROM (
            SELECT customer_id
            FROM gold_customer_engagement
            GROUP BY customer_id
            HAVING COUNT(*) > 1
        )
    """)
    assert duplicates == 0


def test_gold_customer_engagement_event_type_counts_reconcile(conn):
    mismatched = scalar(conn, """
        SELECT COUNT(*)
        FROM gold_customer_engagement
        WHERE web_events <> (
            cart_events + product_view_events + login_events + search_events + page_view_events
        )
    """)
    assert mismatched == 0
