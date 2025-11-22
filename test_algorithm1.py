"""
Test daily sales anomaly detection
"""

from datetime import datetime, date
from data.loader import load_transaction_data
from algorithms.daily_sales import calculate_daily_sales_anomaly

print("🧪 TESTING ALGORITHM 1: Daily Sales Anomaly\n")

# Load data
transactions_df, _ = load_transaction_data('madina_last_quarter_sales.csv')

# Test on a specific date - let's pick a date from the middle of the dataset
test_date = date(2025, 9, 15)  # September 15, 2025

print(f"📅 Analyzing: {test_date.strftime('%A, %B %d, %Y')}\n")
print("="*60)

# Run the algorithm
result = calculate_daily_sales_anomaly(test_date, transactions_df)

# Print results
print(f"\n{'='*60}")
print(f"📊 ALGORITHM 1 RESULTS")
print(f"{'='*60}")

if result['can_analyze']:
    print(f"Risk Score: {result['risk_score']}/40")
    print(f"Alert: {'🚨 YES' if result['alert'] else '✅ NO'}")
    
    print(f"\nMetrics:")
    for key, value in result['metrics'].items():
        print(f"  • {key}: {value}")
    
    if result['messages']:
        print(f"\nIssues Detected:")
        for msg in result['messages']:
            print(f"  {msg}")
    else:
        print(f"\n✅ No issues detected - sales are normal")
else:
    print(f"❌ Could not analyze:")
    for msg in result['messages']:
        print(f"  • {msg}")

print(f"\n{'='*60}\n")

# Test another date
print("\n" + "="*60)
print("Testing multiple dates to see pattern...")
print("="*60 + "\n")

test_dates = [
    date(2025, 9, 1),
    date(2025, 9, 10),
    date(2025, 9, 15),
    date(2025, 9, 20),
    date(2025, 9, 25),
]

for test_date in test_dates:
    result = calculate_daily_sales_anomaly(test_date, transactions_df)
    
    if result['can_analyze']:
        status = "🚨 ALERT" if result['alert'] else "✅ OK"
        print(f"{test_date} ({result['metrics']['day_of_week']:9}): "
              f"GHS {result['metrics']['today_sales']:>8,.0f} "
              f"| Score: {result['risk_score']:2}/40 {status}")