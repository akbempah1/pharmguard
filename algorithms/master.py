"""
Master Risk Calculator
Combines all algorithm results into overall risk score

FLEXIBLE: Runs only algorithms that have sufficient data
"""

import pandas as pd
from datetime import datetime

from algorithms.daily_sales import calculate_daily_sales_anomaly
from algorithms.high_value_products import calculate_high_value_product_anomaly
from algorithms.product_mix import calculate_product_mix_anomaly
from algorithms.weekly_trends import calculate_weekly_trend_anomaly
from algorithms.ml_anomaly import calculate_ml_anomaly

from config import RISK_LEVELS


def calculate_overall_risk(today_date, transactions_df, **kwargs):
    """
    Master function that runs all applicable algorithms
    
    Args:
        today_date: Date to analyze (datetime.date)
        transactions_df: Standardized transaction data
        **kwargs: Optional parameters:
            - high_value_products: List of high-value product names
            - branch_id: Branch to analyze
            
    Returns:
        dict: Complete risk assessment
    """
    
    print(f"\n{'='*60}")
    print(f"🔍 ANALYZING: {today_date.strftime('%A, %B %d, %Y')}")
    print(f"{'='*60}\n")
    
    # Run all algorithms
    results = {}
    
    # Algorithm 1: Daily Sales Anomaly
    print("Running: Daily Sales Anomaly Detection...")
    results['daily_sales'] = calculate_daily_sales_anomaly(
        today_date, 
        transactions_df,
        branch_id=kwargs.get('branch_id')
    )
    
    # Algorithm 2: High-Value Product Tracking
    print("Running: High-Value Product Tracking...")
    results['high_value_products'] = calculate_high_value_product_anomaly(
        today_date,
        transactions_df,
        high_value_products=kwargs.get('high_value_products')
    )
    
    # Algorithm 3: Product Mix
    print("Running: Product Mix Analysis...")
    results['product_mix'] = calculate_product_mix_anomaly(
        today_date,
        transactions_df
    )
    
    # Algorithm 4: Weekly Trends
    print("Running: Weekly Trend Analysis...")
    results['weekly_trends'] = calculate_weekly_trend_anomaly(
        today_date,
        transactions_df
    )
    
    # Algorithm 5: ML-Based Anomaly Detection
    print("Running: ML Anomaly Detection (Isolation Forest)...")
    results['ml_anomaly'] = calculate_ml_anomaly(
        today_date,
        transactions_df
    )
    
    print()
    
    # Combine risk scores (only from algorithms that could analyze)
    total_risk_score = 0
    active_algorithms = []
    all_messages = []
    
    for algo_name, result in results.items():
        if result.get('can_analyze', False):
            total_risk_score += result['risk_score']
            active_algorithms.append(algo_name)
            
            if result.get('alert', False):
                all_messages.extend(result['messages'])
    
    # Cap at 100
    total_risk_score = min(total_risk_score, 100)
    
    # Determine risk level
    risk_level = 'low'
    for level, (min_score, max_score) in RISK_LEVELS.items():
        if min_score <= total_risk_score <= max_score:
            risk_level = level
            break
    
    # Risk level emoji and color
    risk_emoji = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🟠',
        'critical': '🔴'
    }
    
    # Recommended action
    if risk_level == 'critical':
        action = "🚨 URGENT: Investigate immediately, review CCTV if available, consider suspension pending investigation"
    elif risk_level == 'high':
        action = "⚠️ Investigate today, review transactions in detail, check physical inventory"
    elif risk_level == 'medium':
        action = "👀 Monitor closely, check again tomorrow, prepare to investigate"
    else:
        action = "✅ Normal operations, no immediate action needed"
    
    # Create comprehensive report
    assessment = {
        'date': today_date,
        'total_risk_score': total_risk_score,
        'risk_level': risk_level,
        'risk_emoji': risk_emoji[risk_level],
        'recommended_action': action,
        'alert_messages': all_messages,
        'algorithms_run': active_algorithms,
        'algorithm_results': results,
        'requires_alert': total_risk_score >= 40  # From config.ALERT_THRESHOLD
    }
    
    # Print summary
    print_risk_summary(assessment)
    
    return assessment


def print_risk_summary(assessment):
    """Print human-readable risk summary"""
    
    print(f"\n{'='*60}")
    print(f"📊 RISK ASSESSMENT SUMMARY")
    print(f"{'='*60}")
    print(f"Date: {assessment['date'].strftime('%A, %B %d, %Y')}")
    print(f"Risk Score: {assessment['total_risk_score']}/100")
    print(f"Risk Level: {assessment['risk_emoji']} {assessment['risk_level'].upper()}")
    print(f"\nAlgorithms Run: {len(assessment['algorithms_run'])}")
    for algo in assessment['algorithms_run']:
        result = assessment['algorithm_results'][algo]
        score = result['risk_score']
        status = "🚨 ALERT" if result.get('alert') else "✓ OK"
        
        # Add ML model name if present
        model_name = ""
        if 'ml_model' in result:
            model_name = f" ({result['ml_model']})"
        
        print(f"  • {algo}{model_name}: {score} points [{status}]")
    
    if assessment['alert_messages']:
        print(f"\n⚠️  Issues Detected ({len(assessment['alert_messages'])}):")
        for msg in assessment['alert_messages']:
            print(f"  {msg}")
    else:
        print(f"\n✅ No significant issues detected")
    
    print(f"\n💡 Recommended Action:")
    print(f"  {assessment['recommended_action']}")
    print(f"{'='*60}\n")