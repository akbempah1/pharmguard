import pandas as pd

df = pd.read_csv('madina_last_quarter_sales.csv')

print("📋 Actual columns in your CSV:")
print(df.columns.tolist())

print("\n📊 First 5 rows:")
print(df.head())