import pandas as pd

import os

print("Current Working Directory:")


files = [
    "customers.csv",
    "orders.csv",
    "payments.csv",
    "customer_support.csv",
    "web_events.csv"
]

for file in files:
    print(f"\n{'='*50}")
    print(f"Profiling: {file}")
    print(f"{'='*50}")

    df=pd.read_csv(f"../data/source/{file}")

    print("Rows:",len(df))
    print("Columns:",len(df.columns))

    print("\nNull values:")
    print(df.isnull().sum())

    print("\nDuplicates:")
    print(df.duplicated().sum())

    print("\nData Types:")
    print(df.dtypes)