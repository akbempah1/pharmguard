"""
Test all 4 algorithms on a specific date
"""

from datetime import date
from data.loader import load_transaction_data
from algorithms.daily_sales import calculate_daily_sales_anomaly
from algorithms.high_value_products import calculate_high_value_product_anomaly
from algorithms.product_mix import calculate_product_mix_anomaly
from algorithms.weekly_trends import calculate_weekly_trend_anomaly

print("🧪 TESTING ALL 4 ALGORITHMS\n")

# Load data
print("Loading data...")
transactions_df, _ = load_transaction_data('madina_last_quarter_sales.csv')

# Test date
test_date = date(2025, 9, 15)

print(f"\n{'='*60}")
print(f"📅 Analyzing: {test_date.strftime('%A, %B %d, %Y')}")
print(f"{'='*60}\n")

# Run all algorithms
results = {}

print("Running Algorithm 1: Daily Sales Anomaly...")
results['daily_sales'] = calculate_daily_sales_anomaly(test_date, transactions_df)

print("Running Algorithm 2: High-Value Product Tracking...")
results['high_value'] = calculate_high_value_product_anomaly(test_date, transactions_df)

print("Running Algorithm 3: Product Mix Analysis...")
results['product_mix'] = calculate_product_mix_anomaly(test_date, transactions_df)

print("Running Algorithm 4: Weekly Trends...")
results['weekly_trends'] = calculate_weekly_trend_anomaly(test_date, transactions_df)

# Calculate total risk score
total_risk = 0
alerts = []

print(f"\n{'='*60}")
print(f"📊 COMBINED RISK ASSESSMENT")
print(f"{'='*60}\n")

for algo_name, result in results.items():
    if result.get('can_analyze'):
        score = result['risk_score']
        total_risk += score
        status = "🚨 ALERT" if result['alert'] else "✅ OK"
        print(f"{algo_name:20} | Score: {score:2} | {status}")
        
        if result['alert']:
            alerts.extend(result['messages'])

print(f"\n{'='*60}")
print(f"TOTAL RISK SCORE: {total_risk}/100")
print(f"{'='*60}")

if alerts:
    print(f"\n⚠️  Issues Detected ({len(alerts)}):")
    for msg in alerts:
        print(f"  {msg}")
else:
    print(f"\n✅ No significant issues detected - all algorithms passed")

print()