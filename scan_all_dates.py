"""
Scan all dates in the dataset to find suspicious days
"""

from datetime import date, timedelta
from data.loader import load_transaction_data
from algorithms.master import calculate_overall_risk
import pandas as pd

print("🔍 SCANNING ALL DATES FOR ANOMALIES\n")

# Load data (suppress verbose output)
import sys
from io import StringIO

old_stdout = sys.stdout
sys.stdout = StringIO()
transactions_df, _ = load_transaction_data('madina_last_quarter_sales.csv')
sys.stdout = old_stdout

print(f"✅ Loaded data: {len(transactions_df)} transactions")

# Get all unique dates in dataset
all_dates = sorted(transactions_df['transaction_date'].dt.date.unique())
print(f"📅 Date range: {all_dates[0]} to {all_dates[-1]}")
print(f"📊 Total days: {len(all_dates)}\n")

print("Scanning... (this may take a minute)\n")

# Scan all dates
results = []

for analysis_date in all_dates:
    # Suppress verbose output during scan
    sys.stdout = StringIO()
    assessment = calculate_overall_risk(analysis_date, transactions_df)
    sys.stdout = old_stdout
    
    results.append({
        'date': analysis_date,
        'day_of_week': analysis_date.strftime('%A'),
        'risk_score': assessment['total_risk_score'],
        'risk_level': assessment['risk_level'],
        'requires_alert': assessment['requires_alert'],
        'daily_sales': assessment['algorithm_results']['daily_sales']['metrics']['today_sales'] 
                      if assessment['algorithm_results']['daily_sales'].get('can_analyze') else 0,
        'transactions': assessment['algorithm_results']['daily_sales']['metrics']['today_transactions']
                       if assessment['algorithm_results']['daily_sales'].get('can_analyze') else 0
    })

# Create dataframe
results_df = pd.DataFrame(results)

print("="*80)
print("📊 SCAN RESULTS SUMMARY")
print("="*80)

# Overall statistics
print(f"\n📈 Overall Statistics:")
print(f"   Average Risk Score: {results_df['risk_score'].mean():.1f}/100")
print(f"   Highest Risk Score: {results_df['risk_score'].max()}/100")
print(f"   Days with alerts: {results_df['requires_alert'].sum()}/{len(results_df)}")

# Risk level distribution
print(f"\n🎯 Risk Level Distribution:")
risk_counts = results_df['risk_level'].value_counts()
for level in ['critical', 'high', 'medium', 'low']:
    count = risk_counts.get(level, 0)
    pct = (count / len(results_df)) * 100
    emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[level]
    print(f"   {emoji} {level.upper():8} : {count:3} days ({pct:5.1f}%)")

# Top 10 highest risk days
print(f"\n🚨 TOP 10 HIGHEST RISK DAYS:")
print("-"*80)
top_risky = results_df.nlargest(10, 'risk_score')
for idx, row in top_risky.iterrows():
    emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[row['risk_level']]
    print(f"{row['date']} ({row['day_of_week']:9}) | "
          f"{emoji} {row['risk_score']:3}/100 | "
          f"GHS {row['daily_sales']:>7,.0f} | "
          f"{row['transactions']:3} trans")

# Days requiring alerts
alert_days = results_df[results_df['requires_alert']]
if len(alert_days) > 0:
    print(f"\n⚠️  DAYS REQUIRING INVESTIGATION ({len(alert_days)} days):")
    print("-"*80)
    for idx, row in alert_days.iterrows():
        emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[row['risk_level']]
        print(f"{row['date']} ({row['day_of_week']:9}) | "
              f"{emoji} Risk: {row['risk_score']:3}/100 | "
              f"Sales: GHS {row['daily_sales']:>7,.0f}")
else:
    print(f"\n✅ NO DAYS REQUIRING ALERTS")
    print("   All days showed normal patterns - no theft indicators detected")

# Bottom 10 days by sales (potential theft days)
print(f"\n📉 BOTTOM 10 DAYS BY SALES (Potential Theft Indicators):")
print("-"*80)
bottom_sales = results_df.nlargest(10, 'risk_score')  # Also show risk scores
for idx, row in bottom_sales.iterrows():
    emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}[row['risk_level']]
    print(f"{row['date']} ({row['day_of_week']:9}) | "
          f"GHS {row['daily_sales']:>7,.0f} | "
          f"{emoji} Risk: {row['risk_score']:3}/100")

print(f"\n{'='*80}\n")