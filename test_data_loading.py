"""
Quick test script to verify data loading works
"""

from data.loader import load_transaction_data
from data.validator import detect_data_capabilities

# Test with your Madina data
print("🧪 TESTING DATA LOADING\n")

try:
    # Load data
    transactions_df, validation_result = load_transaction_data('madina_last_quarter_sales.csv')
    
    # Check capabilities
    capabilities = detect_data_capabilities(transactions_df, validation_result)
    
    print("\n🎯 Analysis Capabilities:")
    print("-" * 60)
    for capability, can_run in capabilities['can_run'].items():
        status = "✅" if can_run else "❌"
        print(f"   {status} {capability}")
    
    print("\n📊 Data Summary:")
    print("-" * 60)
    print(f"Total transactions: {len(transactions_df)}")
    print(f"Date range: {transactions_df['transaction_date'].min().date()} to {transactions_df['transaction_date'].max().date()}")
    print(f"Total sales: GHS {transactions_df['amount'].sum():,.2f}")
    print(f"Unique products: {transactions_df['product_name'].nunique()}")
    
    print("\n🔝 Top 10 Products by Revenue:")
    print("-" * 60)
    top_products = transactions_df.groupby('product_name')['amount'].sum().sort_values(ascending=False).head(10)
    for i, (product, revenue) in enumerate(top_products.items(), 1):
        print(f"   {i:2}. {product[:40]:40} GHS {revenue:>8,.2f}")
    
    print("\n✅ DATA LOADING TEST PASSED!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()