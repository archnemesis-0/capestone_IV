from datetime import datetime

import duckdb
import pandas as pd

connection = duckdb.connect("../customer360.duckdb")

customers_df = connection.execute(f"SELECT * FROM silver_customers_dedup").fetch_df()
gold_customer_orders = connection.execute(f"SELECT * FROM gold_customer_orders").fetch_df()
gold_customer_support = connection.execute(f"SELECT * FROM gold_customer_support").fetch_df()
gold_customer_engagement = connection.execute(f"SELECT * FROM gold_customer_engagement").fetch_df()

customer_360 = customers_df[["customer_id","first_name","last_name","email","phone","customer_status"]]
# print(customer_360.head())

customer_360 = (
    customer_360
    .merge(
        gold_customer_orders[
            [
                "customer_id",
                "total_orders",
                "total_spend",
                "average_order_value",
                "first_order_date",
                "last_order_date"
            ]
        ],
        on="customer_id",
        how="left"
    )
    .merge(
        gold_customer_support[
            [
                "customer_id",
                "open_tickets_count",
                "resolved_tickets_count",
                "closed_tickets_count",
                "last_ticket_date"
            ]
        ],
        on="customer_id",
        how="left"
    )
    .merge(
        gold_customer_engagement[
            [
                "customer_id",
                "web_events",
                "last_event_date"
            ]
        ],
        on="customer_id",
        how="left"
    )
)

customer_360[["open_tickets_count","resolved_tickets_count","closed_tickets_count","web_events","total_orders"]] = (
    customer_360[["open_tickets_count","resolved_tickets_count","closed_tickets_count","web_events","total_orders"]]
    .fillna(0)
    .astype(int)
)

customer_360[["total_spend","average_order_value"]] = (
    customer_360[["total_spend","average_order_value"]]
    .fillna(0)
    .round(2)
)

# print(customer_360.head())

def assign_segment(row):
    if row["total_spend"] >= 100000:
        return "VIP"
    elif row["total_spend"] >= 75000:
        return "HIGH_VALUE"
    elif row["total_spend"] >= 50000:
        return "FREQUENT"
    elif row["total_spend"] >= 25000:
        return "REGULAR"
    else:
        return "OCCASIONAL"


customer_360["customer_segment"] = (
    customer_360.apply(assign_segment, axis=1)
)

# print(customer_360[customer_360["customer_segment"] == "VIP"])

customer_360["last_activity_date"] = (
    customer_360[["last_order_date", "last_ticket_date", "last_event_date"]]
    .max(axis=1)
)

REFERENCE_DATE = pd.Timestamp(datetime.now().date())

def assign_customer_status(row):
    last_activity = row["last_activity_date"]

    if pd.isna(last_activity):
        return "INACTIVE"

    days_since = (REFERENCE_DATE - last_activity).days

    if days_since < 30:
        return "ACTIVE"
    elif days_since < 90:
        return "AT_RISK"
    else:
        return "INACTIVE"

customer_360["customer_status"] = (
    customer_360.apply(assign_customer_status, axis=1)
)

customer_360 = customer_360.drop(
    columns=["last_ticket_date", "last_event_date", "last_activity_date"]
)

# print(customer_360[["customer_id", "customer_activity_status"]].head())

# print(customer_360.columns)
# print("Rows:", len(customer_360))
# print("Unique customers:", customer_360["customer_id"].nunique())

connection.register("customer_360_temp", customer_360)

connection.execute("""
    CREATE OR REPLACE TABLE customer_360 AS
    SELECT *
    FROM customer_360_temp
""")

connection.unregister("customer_360_temp")

# unique_counts = connection.execute(f"SELECT COUNT(*) FROM customer_360").fetchone()[0]
# print(unique_counts)