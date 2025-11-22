"""
Algorithm 5: Weekly Trend Analysis
Detects sustained underperformance over time

REQUIRES: transaction_date, amount
OPTIONAL: None
"""

import pandas as pd
import numpy as np
from datetime import timedelta


def calculate_weekly_trend_anomaly(today_date, transactions_df):
    """
    Analyze weekly trends to detect sustained problems
    
    Args:
        today_date: Date to analyze
        transactions_df: Transaction data
        
    Returns:
        dict: Risk assessment
    """
    
    # Get week boundaries (Monday to Sunday)
    days_since_monday = today_date.weekday()
    week_start = today_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    # This week's data (so far)
    this_week = transactions_df[
        (transactions_df['transaction_date'].dt.date >= week_start) &
        (transactions_df['transaction_date'].dt.date <= today_date)
    ]
    
    if len(this_week) == 0:
        return {
            'algorithm': 'weekly_trends',
            'risk_score': 0,
            'alert': False,
            'messages': ['No transactions this week yet'],
            'can_analyze': False
        }
    
    # Previous 4 weeks
    prev_weeks_data = []
    
    for i in range(1, 5):
        prev_week_start = week_start - timedelta(weeks=i)
        prev_week_end = prev_week_start + timedelta(days=6)
        
        prev_week = transactions_df[
            (transactions_df['transaction_date'].dt.date >= prev_week_start) &
            (transactions_df['transaction_date'].dt.date <= prev_week_end)
        ]
        
        if len(prev_week) > 0:
            week_total = prev_week['amount'].sum()
            prev_weeks_data.append(week_total)
    
    if len(prev_weeks_data) < 3:
        return {
            'algorithm': 'weekly_trends',
            'risk_score': 0,
            'alert': False,
            'messages': ['Insufficient historical weeks (need at least 3)'],
            'can_analyze': False
        }
    
    avg_weekly_sales = np.mean(prev_weeks_data)
    
    # This week's total so far
    this_week_total = this_week['amount'].sum()
    
    # Days elapsed this week (including today)
    days_elapsed = (today_date - week_start).days + 1
    
    # Projected week total (simple linear projection)
    if days_elapsed > 0:
        projected_week_total = (this_week_total / days_elapsed) * 7
    else:
        projected_week_total = 0
    
    risk_score = 0
    messages = []
    alert = False
    
    # Calculate projected variance
    if avg_weekly_sales > 0:
        projected_variance = ((avg_weekly_sales - projected_week_total) / avg_weekly_sales) * 100
        
        # Significant projected shortfall
        if projected_variance > 20:  # 20%+ below normal
            risk_score += 30
            alert = True
            messages.append(f"📊 Week projected at GHS {projected_week_total:,.0f}")
            messages.append(f"   Average weekly: GHS {avg_weekly_sales:,.0f}")
            messages.append(f"   On track for {projected_variance:.0f}% below normal")
        
        # Very significant shortfall
        if projected_variance > 35:
            risk_score += 15
            messages.append(f"   🚨 CRITICAL: Sustained major underperformance")
        
        # Already below average even mid-week
        if this_week_total < (avg_weekly_sales * 0.5) and days_elapsed >= 4:
            risk_score += 10
            messages.append(f"   ⚠️ Already significantly below weekly average")
    
    return {
        'algorithm': 'weekly_trends',
        'risk_score': min(risk_score, 35),
        'alert': alert,
        'messages': messages,
        'metrics': {
            'this_week_total': float(this_week_total),
            'projected_week_total': float(projected_week_total),
            'avg_weekly_sales': float(avg_weekly_sales),
            'days_elapsed': int(days_elapsed),
            'week_start': week_start.strftime('%Y-%m-%d')
        },
        'can_analyze': True
    }