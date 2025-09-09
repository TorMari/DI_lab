import pandas as pd
import time
import os
import pyarrow.parquet as pq


csv_file = "financial_transactions.csv"
df_csv = pd.read_csv(csv_file)
print(df_csv.head())

parquet_file = "data.parquet"
df_csv.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
table = pq.read_table("data.parquet")
print(table.column("description"))


start = time.time()
df_csv = pd.read_csv(csv_file)
result_csv = df_csv[df_csv['amount'] > 3000]
end = time.time()
print(f"Час запиту CSV: {end - start:.4f} секунд")


start = time.time()
df_parquet = pd.read_parquet(parquet_file, engine="pyarrow")
result_parquet = df_parquet[df_parquet['amount'] > 3000]
end = time.time()
print(f"Час запиту Parquet: {end - start:.4f} секунд")

###########################################################################################################


start = time.time()
top_csv = (
   df_csv[df_csv['type'] == "debit"]
   .sort_values("date", ascending=True)
   .head(10)
)
end = time.time()
print(f"\nЧас запиту CSV (sort+head): {end - start:.4f} секунд")


start = time.time()
top_csv = (
   df_parquet[df_parquet['type'] == "debit"]
   .sort_values("date", ascending=True)
   .head(10)
)
end = time.time()
print(f"Час запиту Parquet (sort+head): {end - start:.4f} секунд")


###########################################################################################################

print(f"\nРозмір CSV: {os.path.getsize(csv_file)/1024:.2f} KB")
print(f"Розмір Parquet: {os.path.getsize(parquet_file)/1024:.2f} KB\n")

