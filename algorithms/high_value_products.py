"""
Algorithm 2: High-Value Product Tracking
Detects when expensive products are selling less than usual

REQUIRES: transaction_date, product_name, amount, quantity
OPTIONAL: unit_price
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from config import HIGH_VALUE_THRESHOLD


def identify_high_value_products(transactions_df, threshold=HIGH_VALUE_THRESHOLD, manual_list=None):
    """
    Identify high-value products from transaction history
    
    Args:
        transactions_df: Transaction data
        threshold: Price threshold for "high-value" (default from config)
        manual_list: Optional manual list of high-value product names
        
    Returns:
        list: Product names considered high-value
    """
    
    if manual_list:
        print(f"📋 Using manual high-value product list ({len(manual_list)} products)")
        return manual_list
    
    # Auto-detect from average unit price
    if 'unit_price' in transactions_df.columns:
        product_prices = transactions_df.groupby('product_name')['unit_price'].mean()
    else:
        # Calculate from amount/quantity
        product_prices = transactions_df.groupby('product_name').apply(
            lambda x: (x['amount'].sum() / x['quantity'].sum()) if x['quantity'].sum() > 0 else 0
        )
    
    high_value_products = product_prices[product_prices >= threshold].index.tolist()
    
    print(f"💎 Auto-detected {len(high_value_products)} high-value products (≥GHS {threshold})")
    
    if len(high_value_products) > 0:
        print(f"   Examples: {', '.join(high_value_products[:5])}")
    
    return high_value_products


def calculate_high_value_product_anomaly(today_date, transactions_df, high_value_products=None):
    """
    Detect anomalies in high-value product sales
    
    Args:
        today_date: Date to analyze
        transactions_df: Transaction data
        high_value_products: List of high-value product names (auto-detected if None)
        
    Returns:
        dict: Risk assessment
    """
    
    # Identify high-value products if not provided
    if high_value_products is None:
        high_value_products = identify_high_value_products(transactions_df)
    
    if len(high_value_products) == 0:
        return {
            'algorithm': 'high_value_product_tracking',
            'risk_score': 0,
            'alert': False,
            'messages': ['No high-value products identified'],
            'can_analyze': False
        }
    
    # Historical data (last 30 days)
    historical_end = today_date - timedelta(days=1)
    historical_start = historical_end - timedelta(days=30)
    
    historical = transactions_df[
        (transactions_df['transaction_date'].dt.date >= historical_start) &
        (transactions_df['transaction_date'].dt.date <= historical_end) &
        (transactions_df['product_name'].isin(high_value_products))
    ]
    
    today = transactions_df[
        (transactions_df['transaction_date'].dt.date == today_date) &
        (transactions_df['product_name'].isin(high_value_products))
    ]
    
    if len(historical) == 0:
        return {
            'algorithm': 'high_value_product_tracking',
            'risk_score': 0,
            'alert': False,
            'messages': ['Insufficient historical data for high-value products'],
            'can_analyze': False
        }
    
    # Calculate historical daily averages
    hist_daily = historical.groupby(historical['transaction_date'].dt.date).agg({
        'quantity': 'sum',
        'amount': 'sum'
    })
    
    hist_avg_qty = hist_daily['quantity'].mean()
    hist_avg_value = hist_daily['amount'].mean()
    
    # Today's metrics
    today_qty = today['quantity'].sum() if len(today) > 0 else 0
    today_value = today['amount'].sum() if len(today) > 0 else 0
    
    # Risk scoring
    risk_score = 0
    messages = []
    alert = False
    
    # Significant drop in quantity
    if hist_avg_qty > 0:
        qty_ratio = today_qty / hist_avg_qty
        
        if qty_ratio < 0.5:  # 50% drop or more
            risk_score += 25
            alert = True
            messages.append(f"💎 High-value products: Only {today_qty:.0f} units sold")
            messages.append(f"   Average: {hist_avg_qty:.0f} units | Today: {today_qty:.0f} units")
        
        # Zero high-value sales on a normal day
        if today_qty == 0 and hist_avg_qty > 2:
            risk_score += 20
            alert = True
            messages.append(f"🚨 ZERO high-value product sales today (very unusual)")
    
    # Significant drop in value
    if hist_avg_value > 0:
        value_ratio = today_value / hist_avg_value
        
        if value_ratio < 0.4:  # 60% drop or more
            risk_score += 15
            alert = True
            messages.append(f"💰 High-value sales: GHS {today_value:.0f} (avg: GHS {hist_avg_value:.0f})")
    
    # Specific high-value products not sold
    if len(today) > 0:
        products_sold_today = today['product_name'].unique()
        products_not_sold = [p for p in high_value_products if p not in products_sold_today]
        
        if len(products_not_sold) >= len(high_value_products) * 0.7:  # 70%+ not sold
            risk_score += 10
            messages.append(f"📦 {len(products_not_sold)}/{len(high_value_products)} high-value products NOT sold today")
    
    return {
        'algorithm': 'high_value_product_tracking',
        'risk_score': min(risk_score, 35),
        'alert': alert,
        'messages': messages,
        'metrics': {
            'high_value_products_count': len(high_value_products),
            'today_qty': float(today_qty),
            'avg_qty': float(hist_avg_qty),
            'today_value': float(today_value),
            'avg_value': float(hist_avg_value)
        },
        'can_analyze': True
    }