import duckdb
import pandas as pd

connection = duckdb.connect("../customer360.duckdb")

orders_df = connection.execute(f"SELECT * FROM silver_orders").fetch_df()
customers_df = connection.execute(f"SELECT * FROM silver_customers_dedup").fetch_df()
active_orders_df = connection.execute(f"SELECT * FROM silver_orders_active").fetch_df()
payments_df = connection.execute(f"SELECT * FROM silver_payments").fetch_df()
customer_support_df = connection.execute(f"SELECT * FROM silver_customer_support").fetch_df()
web_events_df = connection.execute(f"SELECT * FROM silver_web_events").fetch_df()

# print(active_orders_df[active_orders_df["order_amount"] <= 0])

gold_customer_orders = (
    active_orders_df
    .groupby("customer_id")
    .agg(
        total_orders=("order_id", "nunique"),
        total_spend=("order_amount", "sum"),
        average_order_value=("order_amount", "mean"),
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max")
    )
    .reset_index()
)

# print(gold_customer_orders.head())

gold_customer_support = (
    customer_support_df
    .groupby("customer_id")
    .agg(
        ticket_counts=("ticket_id", "nunique"),
        first_ticket_date=("ticket_date", "min"),
        last_ticket_date=("ticket_date", "max")
    )
    .reset_index()
)

# print(gold_customer_support.head(10))

resolved_tickets = (
    customer_support_df[
        customer_support_df["ticket_status"]
        .str.upper()
        .eq("RESOLVED")
    ]
    .groupby("customer_id")["ticket_id"]
    .nunique()
    .reset_index(name="resolved_tickets_count")
)

closed_tickets = (
    customer_support_df[
        customer_support_df["ticket_status"]
        .str.upper()
        .eq("CLOSED")
    ]
    .groupby("customer_id")["ticket_id"]
    .nunique()
    .reset_index(name="closed_tickets_count")
)

open_tickets = (
    customer_support_df[
        customer_support_df["ticket_status"]
        .str.upper()
        .eq("OPEN")
    ]
    .groupby("customer_id")["ticket_id"]
    .nunique()
    .reset_index(name="open_tickets_count")
)

gold_customer_support = (
    gold_customer_support
    .merge(resolved_tickets, on="customer_id", how="left")
    .merge(closed_tickets, on="customer_id", how="left")
    .merge(open_tickets, on="customer_id", how="left")
)

# print(gold_customer_support.head())

gold_customer_support[["resolved_tickets_count","closed_tickets_count","open_tickets_count"]] = (
    gold_customer_support[["resolved_tickets_count","closed_tickets_count","open_tickets_count"]]
    .fillna(0)
    .astype(int)
)

# print(gold_customer_support.head())

# print(gold_customer_support["ticket_counts"].sum(), (open_tickets["open_tickets_count"].sum() + resolved_tickets["resolved_tickets_count"].sum() + closed_tickets["closed_tickets_count"].sum()))

# print(web_events_df["channel"].unique())
# print(web_events_df["event_type"].unique())

gold_customer_engagement = (
    web_events_df
    .groupby("customer_id")
    .agg(
        web_events=("event_id", "nunique"),
        first_event_date=("event_date", "min"),
        last_event_date=("event_date", "max")
    )
    .reset_index()
)

# print(gold_customer_engagement.head())

event_counts = (
    web_events_df
    .pivot_table(
        index="customer_id",
        columns="event_type",
        values="event_id",
        aggfunc="nunique",
        fill_value=0
    )
    .reset_index()
)

event_counts = event_counts.rename(columns={
    "CART": "cart_events",
    "PRODUCT_VIEW": "product_view_events",
    "LOGIN": "login_events",
    "SEARCH": "search_events",
    "PAGE_VIEW": "page_view_events"
})

# print(event_counts.head())

channel_counts = (
    web_events_df
    .pivot_table(
        index="customer_id",
        columns="channel",
        values="event_id",
        aggfunc="nunique",
        fill_value=0
    )
    .reset_index()
)

channel_counts = channel_counts.rename(columns={
    "EMAIL": "email_events",
    "MOBILE": "mobile_events",
    "WEB": "web_channel_events"
})

# print(channel_counts.head())

gold_customer_engagement = (
    gold_customer_engagement
    .merge(
        event_counts,
        on="customer_id",
        how="left"
    )
    .merge(
        channel_counts,
        on="customer_id",
        how="left"
    )
)

# print(gold_customer_engagement.head())
# print(gold_customer_engagement[
#     (gold_customer_engagement["cart_events"] + 
#     gold_customer_engagement["product_view_events"] + 
#     gold_customer_engagement["login_events"] +
#     gold_customer_engagement["search_events"] +
#     gold_customer_engagement["page_view_events"]) !=
#     (gold_customer_engagement["email_events"] + 
#     gold_customer_engagement["web_channel_events"] +
#     gold_customer_engagement["mobile_events"])])

def save_dataframe(df, table_name):
    temp_name = f"{table_name}_temp"

    connection.register(temp_name, df)

    connection.execute(f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT *
        FROM {temp_name}
    """)

    connection.unregister(temp_name)

    print(f"Saved: {table_name}")

save_dataframe(
    gold_customer_orders,
    "gold_customer_orders"
)

save_dataframe(
    gold_customer_support,
    "gold_customer_support"
)

save_dataframe(
    gold_customer_engagement,
    "gold_customer_engagement"
)

tables = [
    "gold_customer_orders",
    "gold_customer_support",
    "gold_customer_engagement"
]

for table in tables:
    count = connection.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {count:,} rows")