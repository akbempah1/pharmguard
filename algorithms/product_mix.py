"""
Algorithm 4: Product Mix Analysis
Detects shifts in product mix (more cheap items, fewer expensive ones)

REQUIRES: transaction_date, product_name, amount
OPTIONAL: unit_price
"""

import pandas as pd
import numpy as np
from datetime import timedelta


def calculate_product_mix_anomaly(today_date, transactions_df):
    """
    Detect anomalies in product mix
    
    Args:
        today_date: Date to analyze
        transactions_df: Transaction data
        
    Returns:
        dict: Risk assessment
    """
    
    # Historical data (last 30 days)
    historical_end = today_date - timedelta(days=1)
    historical_start = historical_end - timedelta(days=30)
    
    historical = transactions_df[
        (transactions_df['transaction_date'].dt.date >= historical_start) &
        (transactions_df['transaction_date'].dt.date <= historical_end)
    ]
    
    today = transactions_df[transactions_df['transaction_date'].dt.date == today_date]
    
    if len(today) == 0:
        return {
            'algorithm': 'product_mix_analysis',
            'risk_score': 0,
            'alert': False,
            'messages': ['No transactions today'],
            'can_analyze': False
        }
    
    if len(historical) == 0:
        return {
            'algorithm': 'product_mix_analysis',
            'risk_score': 0,
            'alert': False,
            'messages': ['Insufficient historical data'],
            'can_analyze': False
        }
    
    # Calculate average transaction value
    hist_daily = historical.groupby(historical['transaction_date'].dt.date).apply(
        lambda x: x['amount'].sum() / len(x) if len(x) > 0 else 0
    )
    hist_avg_transaction = hist_daily.mean()
    
    today_avg_transaction = today['amount'].mean()
    
    risk_score = 0
    messages = []
    alert = False
    
    # Significant drop in average transaction value
    if hist_avg_transaction > 0:
        ratio = today_avg_transaction / hist_avg_transaction
        
        if ratio < 0.6:  # 40%+ drop
            risk_score += 25
            alert = True
            percentage_drop = (1 - ratio) * 100
            messages.append(f"📉 Average transaction value down {percentage_drop:.0f}%")
            messages.append(f"   Today: GHS {today_avg_transaction:.2f} | Avg: GHS {hist_avg_transaction:.2f}")
            messages.append(f"   Possible shift to cheaper products")
    
    # Many very small transactions
    small_threshold = 10  # GHS 10
    small_transactions = len(today[today['amount'] < small_threshold])
    
    if len(today) >= 10 and small_transactions > (len(today) * 0.5):
        risk_score += 15
        alert = True
        messages.append(f"🛒 {small_transactions}/{len(today)} transactions under GHS {small_threshold}")
    
    # Few high-value transactions
    high_threshold = 50  # GHS 50
    high_transactions = len(today[today['amount'] >= high_threshold])
    hist_high_ratio = len(historical[historical['amount'] >= high_threshold]) / len(historical) if len(historical) > 0 else 0
    today_high_ratio = high_transactions / len(today) if len(today) > 0 else 0
    
    if hist_high_ratio > 0.1 and today_high_ratio < (hist_high_ratio * 0.5):  # 50% drop in high-value transaction ratio
        risk_score += 15
        alert = True
        messages.append(f"💎 Only {high_transactions} high-value sales (≥GHS {high_threshold})")
        messages.append(f"   Normal ratio: {hist_high_ratio*100:.0f}% | Today: {today_high_ratio*100:.0f}%")
    
    return {
        'algorithm': 'product_mix_analysis',
        'risk_score': min(risk_score, 30),
        'alert': alert,
        'messages': messages,
        'metrics': {
            'today_avg_transaction': float(today_avg_transaction),
            'hist_avg_transaction': float(hist_avg_transaction),
            'small_transactions': int(small_transactions),
            'high_transactions': int(high_transactions)
        },
        'can_analyze': True
    }