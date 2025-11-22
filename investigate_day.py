"""
Deep dive investigation into a specific suspicious day
"""

from datetime import date
from data.loader import load_transaction_data
from algorithms.master import calculate_overall_risk
from alerts.message_generator import generate_alert_message

print("🔍 DEEP INVESTIGATION: September 8, 2025\n")

# Load data
import sys
from io import StringIO
old_stdout = sys.stdout
sys.stdout = StringIO()
transactions_df, _ = load_transaction_data('madina_last_quarter_sales.csv')
sys.stdout = old_stdout

# Analyze the suspicious day
suspicious_date = date(2025, 9, 8)

print(f"{'='*60}")
print(f"📅 INVESTIGATING: {suspicious_date.strftime('%A, %B %d, %Y')}")
print(f"{'='*60}\n")

# Run full analysis
assessment = calculate_overall_risk(suspicious_date, transactions_df)

# Show the alert message that would be sent
alert_msg = generate_alert_message(assessment, "Madina Branch")

if alert_msg:
    print("\n" + "="*60)
    print("📱 WHATSAPP ALERT THAT WOULD BE SENT:")
    print("="*60)
    print(alert_msg)
    print("="*60 + "\n")

# Get detailed data for this day
today_data = transactions_df[transactions_df['transaction_date'].dt.date == suspicious_date]

print(f"\n{'='*60}")
print(f"📊 DETAILED TRANSACTION ANALYSIS")
print(f"{'='*60}\n")

print(f"Total Transactions: {len(today_data)}")
print(f"Total Sales: GHS {today_data['amount'].sum():,.2f}")
print(f"Average Transaction: GHS {today_data['amount'].mean():.2f}")

# Top selling products that day
print(f"\n🔝 Top 10 Products Sold:")
top_products = today_data.groupby('product_name')['amount'].sum().sort_values(ascending=False).head(10)
for i, (product, revenue) in enumerate(top_products.items(), 1):
    qty = today_data[today_data['product_name'] == product]['quantity'].sum()
    print(f"   {i:2}. {product[:45]:45} | GHS {revenue:>6,.0f} | Qty: {qty:>3.0f}")

# High-value products sold
print(f"\n💎 High-Value Products (≥GHS 50) Sold:")
high_value = today_data[today_data['unit_price'] >= 50].groupby('product_name').agg({
    'quantity': 'sum',
    'amount': 'sum'
}).sort_values('amount', ascending=False)

if len(high_value) > 0:
    for product, row in high_value.head(10).iterrows():
        print(f"   • {product[:45]:45} | GHS {row['amount']:>6,.0f} | Qty: {row['quantity']:>3.0f}")
else:
    print(f"   ⚠️ NO high-value products sold (very suspicious!)")

# Transaction size distribution
print(f"\n💰 Transaction Size Distribution:")
small = len(today_data[today_data['amount'] < 10])
medium = len(today_data[(today_data['amount'] >= 10) & (today_data['amount'] < 50)])
large = len(today_data[today_data['amount'] >= 50])

print(f"   Small (<GHS 10):  {small:3} transactions ({small/len(today_data)*100:.1f}%)")
print(f"   Medium (10-50):   {medium:3} transactions ({medium/len(today_data)*100:.1f}%)")
print(f"   Large (≥GHS 50):  {large:3} transactions ({large/len(today_data)*100:.1f}%)")

print(f"\n{'='*60}\n")