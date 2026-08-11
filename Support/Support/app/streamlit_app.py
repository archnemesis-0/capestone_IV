from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "customer360.duckdb"

st.set_page_config(page_title="Customer 360", layout="wide")
st.title("Customer 360 Data Product")
st.caption(
    "Search and browse the customer_360 table — the governed, one-row-per-customer "
    "view built from Bronze → Silver → Gold. See data_product.md for the full product "
    "documentation."
)

if not DB.exists():
    st.warning(
        f"Database not found at {DB}. Run the pipeline first: "
        "`cd src && python build_bronze.py && python build_silver.py && "
        "python build_gold.py && python build_customer360.py`"
    )
    st.stop()

con = duckdb.connect(str(DB), read_only=True)
customers = con.execute("SELECT * FROM customer_360").fetchdf()
con.close()

SEGMENT_OPTIONS = sorted(customers["customer_segment"].dropna().unique())
STATUS_OPTIONS = sorted(customers["customer_status"].dropna().unique())

with st.sidebar:
    st.header("Search & filter")

    search_term = st.text_input(
        "Search by name, email, or customer ID",
        placeholder="e.g. jane or CUST00042",
    )

    segment_filter = st.multiselect("Customer segment", SEGMENT_OPTIONS, default=[])
    status_filter = st.multiselect("Activity status", STATUS_OPTIONS, default=[])

filtered = customers.copy()

if search_term:
    term = search_term.strip().lower()
    haystack = (
        filtered["customer_id"].astype(str).str.lower()
        + " "
        + filtered["first_name"].astype(str).str.lower()
        + " "
        + filtered["last_name"].astype(str).str.lower()
        + " "
        + filtered["email"].astype(str).str.lower()
    )
    filtered = filtered[haystack.str.contains(term, na=False)]

if segment_filter:
    filtered = filtered[filtered["customer_segment"].isin(segment_filter)]

if status_filter:
    filtered = filtered[filtered["customer_status"].isin(status_filter)]

st.subheader(f"Results ({len(filtered):,} of {len(customers):,} customers)")

display_columns = [
    "customer_id", "first_name", "last_name", "email",
    "customer_segment", "customer_status",
    "total_orders", "total_spend",
]
st.dataframe(
    filtered[display_columns].sort_values("total_spend", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.divider()
st.subheader("Customer profile")

if filtered.empty:
    st.info("No customers match the current search/filters — adjust them to see a profile.")
    st.stop()

profile_options = {
    f"{row.customer_id} — {row.first_name} {row.last_name}": row.customer_id
    for row in filtered.itertuples()
}
selected_label = st.selectbox("Select a customer", list(profile_options.keys()))
selected_id = profile_options[selected_label]

customer = customers[customers["customer_id"] == selected_id].iloc[0]

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Identity**")
    st.write(f"Name: {customer.first_name} {customer.last_name}")
    st.write(f"Customer ID: {customer.customer_id}")
    st.write(f"Email: {customer.email}")
    st.write(f"Phone: {customer.phone}")
    st.write(f"Account status: {customer.customer_status}")

with col2:
    st.markdown("**Orders**")
    st.metric("Total orders", int(customer.total_orders))
    st.metric("Total spend", f"${customer.total_spend:,.2f}")
    st.metric("Average order value", f"${customer.average_order_value:,.2f}")
    first_order = customer.first_order_date
    last_order = customer.last_order_date
    st.write(f"First order: {first_order.date() if pd.notna(first_order) else 'N/A'}")
    st.write(f"Last order: {last_order.date() if pd.notna(last_order) else 'N/A'}")

with col3:
    st.markdown("**Support & engagement**")
    st.metric("Open tickets", int(customer.open_tickets_count))
    st.metric("Resolved tickets", int(customer.resolved_tickets_count))
    st.metric("Closed tickets", int(customer.closed_tickets_count))
    st.metric("Web events", int(customer.web_events))

st.divider()

badge_col1, badge_col2 = st.columns(2)
with badge_col1:
    st.markdown(f"**Segment:** `{customer.customer_segment}`")
with badge_col2:
    st.markdown(f"**Activity status:** `{customer.customer_status}`")
