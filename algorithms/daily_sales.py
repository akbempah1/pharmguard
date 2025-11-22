"""
Algorithm 1: Daily Sales Anomaly Detection
Detects if today's sales are unusually low compared to historical patterns

REQUIRES: transaction_date, amount
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_daily_sales_anomaly(today_date, transactions_df, branch_id=None):
    """
    Detect daily sales anomalies
    
    Args:
        today_date: Date to analyze (datetime.date)
        transactions_df: DataFrame with standardized columns
        branch_id: Optional branch filter
        
    Returns:
        dict: Risk assessment with score and messages
    """
    
    # Filter by branch if specified
    if branch_id and 'branch_id' in transactions_df.columns:
        df = transactions_df[transactions_df['branch_id'] == branch_id].copy()
    else:
        df = transactions_df.copy()
    
    # TODAY'S DATA - ALWAYS GET THIS FIRST
    today = df[df['transaction_date'].dt.date == today_date]
    
    if len(today) == 0:
        return {
            'algorithm': 'daily_sales_anomaly',
            'risk_score': 0,
            'alert': False,
            'messages': ['No transactions today yet'],
            'can_analyze': True,  # Changed to True
            'metrics': {
                'today_sales': 0.0,
                'today_transactions': 0,
                'day_of_week': today_date.strftime('%A')
            }
        }
    
    today_sales = today['amount'].sum()
    today_transactions = len(today)
    today_day_of_week = today_date.weekday()
    
    # ALWAYS PREPARE BASE RESULT WITH TODAY'S DATA
    base_result = {
        'algorithm': 'daily_sales_anomaly',
        'risk_score': 0,
        'alert': False,
        'messages': [],
        'can_analyze': True,  # Always True now
        'metrics': {
            'today_sales': float(today_sales),
            'today_transactions': int(today_transactions),
            'day_of_week': today_date.strftime('%A')
        }
    }
    
    # NOW TRY TO GET HISTORICAL DATA FOR COMPARISON
    # Historical data: last 90 days, excluding today
    historical_end = today_date - timedelta(days=1)
    historical_start = historical_end - timedelta(days=90)
    
    historical = df[
        (df['transaction_date'].dt.date >= historical_start) &
        (df['transaction_date'].dt.date <= historical_end)
    ].copy()
    
    # IF NO HISTORICAL DATA, RETURN BASIC METRICS WITHOUT COMPARISON
    if len(historical) == 0:
        base_result['messages'].append('ℹ️ No historical data for comparison (first month of operations)')
        return base_result
    
    # Filter to same day of week for fair comparison
    historical['day_of_week'] = historical['transaction_date'].dt.dayofweek
    same_day_historical = historical[historical['day_of_week'] == today_day_of_week]
    
    # Calculate daily totals for those days
    daily_totals = same_day_historical.groupby(same_day_historical['transaction_date'].dt.date).agg({
        'amount': 'sum',
        'transaction_date': 'count'
    }).rename(columns={'transaction_date': 'transaction_count'})
    
    # IF NOT ENOUGH SAME-DAY HISTORY, RETURN BASIC METRICS
    if len(daily_totals) < 4:
        base_result['messages'].append(f'ℹ️ Limited history for {today_date.strftime("%A")} comparison (only {len(daily_totals)} past {today_date.strftime("%A")}s)')
        return base_result
    
    # WE HAVE ENOUGH DATA - DO FULL ANALYSIS
    avg_sales = daily_totals['amount'].mean()
    std_sales = daily_totals['amount'].std()
    avg_transactions = daily_totals['transaction_count'].mean()
    
    # Add to metrics
    base_result['metrics']['avg_sales'] = float(avg_sales)
    base_result['metrics']['avg_transactions'] = float(avg_transactions)
    
    # Calculate Z-score
    if std_sales > 0:
        z_score = (today_sales - avg_sales) / std_sales
        base_result['metrics']['z_score'] = float(z_score)
    else:
        z_score = 0
        base_result['metrics']['z_score'] = 0.0
    
    # Risk scoring
    risk_score = 0
    messages = []
    alert = False
    
    # Significant drop in sales
    if z_score < -1.5:  # More than 1.5 std dev below average
        percentage_drop = ((avg_sales - today_sales) / avg_sales) * 100
        risk_score += 30
        alert = True
        messages.append(f"💰 Sales {percentage_drop:.0f}% below normal for {today_date.strftime('%A')}")
        messages.append(f"   Today: GHS {today_sales:,.0f} | Average: GHS {avg_sales:,.0f}")
    
    # Very significant drop
    if z_score < -2.0:
        risk_score += 15
        messages.append(f"   ⚠️ More than 2 standard deviations below normal")
    
    # Fewer transactions than usual
    if avg_transactions > 0 and today_transactions < (avg_transactions * 0.6):
        risk_score += 15
        alert = True
        messages.append(f"📉 Only {today_transactions} transactions (avg: {avg_transactions:.0f})")
    
    # Very few transactions on a weekday
    if today_transactions < 50 and today_day_of_week < 5:  # Weekday
        risk_score += 10
        messages.append(f"⚠️ Suspiciously low transaction count for weekday")
    
    # Update result with analysis
    base_result['risk_score'] = min(risk_score, 40)  # Cap at 40
    base_result['alert'] = alert
    base_result['messages'] = messages
    
    return base_result