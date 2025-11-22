"""
Diagnose why ML model isn't finding anomalies
"""

from datetime import date
from data.loader import load_transaction_data
from algorithms.ml_anomaly import MLAnomalyDetector
import pandas as pd
import numpy as np

print("🔍 ML MODEL DIAGNOSTICS\n")

# Load data
import sys
from io import StringIO
old_stdout = sys.stdout
sys.stdout = StringIO()
transactions_df, _ = load_transaction_data('madina_last_quarter_sales.csv')
sys.stdout = old_stdout

# Train model
detector = MLAnomalyDetector()
historical = transactions_df[transactions_df['transaction_date'].dt.date < date(2025, 9, 8)]
success, message = detector.train(historical, contamination=0.15)  # Even more sensitive

print(f"Model trained: {message}\n")

# Get all dates
all_dates = sorted(transactions_df['transaction_date'].dt.date.unique())

# Predict on ALL dates
results = []

for test_date in all_dates:
    sys.stdout = StringIO()
    result = detector.predict(test_date, transactions_df)
    sys.stdout = old_stdout
    
    if result.get('error'):
        continue
    
    results.append({
        'date': test_date,
        'is_anomaly': result['is_anomaly'],
        'anomaly_score': result['anomaly_score'],
        'risk_score': result['risk_score'],
        'total_sales': result['features']['total_sales']
    })

# Create dataframe
df = pd.DataFrame(results)

print("="*70)
print("ML MODEL RESULTS ON ALL DATES")
print("="*70)

print(f"\nTotal dates analyzed: {len(df)}")
print(f"Flagged as anomalies: {df['is_anomaly'].sum()}")
print(f"Anomaly rate: {df['is_anomaly'].sum() / len(df) * 100:.1f}%")

print("\n🚨 DATES FLAGGED AS ANOMALIES:")
print("-"*70)

anomalies = df[df['is_anomaly'] == True].sort_values('anomaly_score')
if len(anomalies) > 0:
    for idx, row in anomalies.iterrows():
        print(f"{row['date']} | Score: {row['anomaly_score']:.3f} | "
              f"Sales: GHS {row['total_sales']:,.0f} | Risk: {row['risk_score']}/35")
else:
    print("NO ANOMALIES DETECTED!")

print("\n📊 MOST ANOMALOUS DATES (by score, even if not flagged):")
print("-"*70)

most_anomalous = df.nsmallest(10, 'anomaly_score')
for idx, row in most_anomalous.iterrows():
    flag = "🚨" if row['is_anomaly'] else "  "
    print(f"{flag} {row['date']} | Score: {row['anomaly_score']:.3f} | "
          f"Sales: GHS {row['total_sales']:,.0f}")

print("\n📈 LEAST ANOMALOUS DATES (most normal):")
print("-"*70)

least_anomalous = df.nlargest(5, 'anomaly_score')
for idx, row in least_anomalous.iterrows():
    print(f"   {row['date']} | Score: {row['anomaly_score']:.3f} | "
          f"Sales: GHS {row['total_sales']:,.0f}")

print("\n" + "="*70)