"""
Test ML-based anomaly detection using Isolation Forest
"""

from datetime import date
from data.loader import load_transaction_data
from algorithms.ml_anomaly import calculate_ml_anomaly

print("🤖 TESTING ML ANOMALY DETECTION\n")

# Load data
print("Loading data...")
import sys
from io import StringIO

old_stdout = sys.stdout
sys.stdout = StringIO()
transactions_df, _ = load_transaction_data('madina_last_quarter_sales.csv')
sys.stdout = old_stdout

print("✅ Data loaded\n")

# Test on the high-risk day we found
test_date = date(2025, 9, 8)

print(f"📅 Testing on: {test_date.strftime('%A, %B %d, %Y')}")
print("   (This was the day with 70/100 risk score)\n")

print("="*60)
print("Training ML model on historical data...")
print("="*60)

result = calculate_ml_anomaly(test_date, transactions_df)

print(f"\n{'='*60}")
print(f"🤖 ML MODEL RESULTS")
print(f"{'='*60}\n")

if result['can_analyze']:
    print(f"Algorithm: {result.get('ml_model', 'Unknown')}")
    print(f"Risk Score: {result['risk_score']}/35")
    print(f"Is Anomaly: {'🚨 YES' if result['alert'] else '✅ NO'}")
    
    if result['messages']:
        print(f"\nMessages:")
        for msg in result['messages']:
            print(f"  {msg}")
    
    if 'metrics' in result:
        print(f"\nFeatures analyzed:")
        for key, value in result['metrics'].items():
            print(f"  • {key}: {value:,.2f}")
else:
    print("❌ Could not analyze:")
    for msg in result['messages']:
        print(f"  • {msg}")

print(f"\n{'='*60}\n")

# Test on a few more dates
print("Testing on multiple dates...\n")

test_dates = [
    date(2025, 9, 8),   # High risk day
    date(2025, 9, 15),  # Normal day
    date(2025, 9, 12),  # Another high risk day
]

for test_date in test_dates:
    sys.stdout = StringIO()
    result = calculate_ml_anomaly(test_date, transactions_df)
    sys.stdout = old_stdout
    
    if result['can_analyze']:
        status = "🚨 ANOMALY" if result['alert'] else "✅ NORMAL"
        print(f"{test_date} | Risk: {result['risk_score']:2}/35 | {status}")