"""
Generate WhatsApp-formatted alert messages
"""

from datetime import datetime
from config import RISK_LEVELS


def generate_alert_message(assessment, pharmacy_name="Pharmacy"):
    """
    Generate WhatsApp alert message for risk assessment
    
    Args:
        assessment: Risk assessment dict from master.py
        pharmacy_name: Name of pharmacy
        
    Returns:
        str: Formatted WhatsApp message (or None if no alert needed)
    """
    
    # Only generate alert if threshold exceeded
    if not assessment['requires_alert']:
        return None
    
    date = assessment['date'].strftime('%d %b %Y')
    risk_score = assessment['total_risk_score']
    risk_level = assessment['risk_level'].upper()
    risk_emoji = assessment['risk_emoji']
    messages = assessment['alert_messages']
    action = assessment['recommended_action']
    
    # Build message
    alert = f"""🚨 *PHARMGUARD THEFT ALERT INVESTIGATION NEEDED*

🏪 Pharmacy: *{pharmacy_name}*
📅 Date: {date}
⚠️  Risk Level: *{risk_emoji} {risk_level}*
📊 Risk Score: *{risk_score}/100*

*Issues Detected:*
"""
    
    # Add all alert messages
    for i, msg in enumerate(messages, 1):
        alert += f"\n{i}. {msg}"
    
    alert += f"\n\n*Recommended Action:*\n{action}"
    
    # Add algorithm breakdown
    alert += "\n\n*Analysis Breakdown:*"
    for algo_name, result in assessment['algorithm_results'].items():
        if result.get('can_analyze') and result['risk_score'] > 0:
            score = result['risk_score']
            alert += f"\n• {algo_name.replace('_', ' ').title()}: {score} pts"
    
    alert += "\n\n_📱 Powered by PharmGuard - ML Theft Detection_"
    
    return alert


def generate_daily_summary(assessment, pharmacy_name="Pharmacy"):
    """
    Generate end-of-day summary message
    
    Args:
        assessment: Risk assessment dict
        pharmacy_name: Name of pharmacy
        
    Returns:
        str: Formatted summary message
    """
    
    date = assessment['date'].strftime('%d %b %Y, %A')
    risk_score = assessment['total_risk_score']
    risk_level = assessment['risk_level'].upper()
    risk_emoji = assessment['risk_emoji']
    
    summary = f"""📊 *PHARMGUARD DAILY AUDIT REPORT*

🏪 Pharmacy: *{pharmacy_name}*
📅 Date: {date}

*Overall Status:*
{risk_emoji} Risk Level: *{risk_level}*
📊 Risk Score: {risk_score}/100

"""
    
    # Add status message based on risk
    if risk_level == 'CRITICAL':
        summary += "🚨 *CRITICAL ISSUES DETECTED*\nImmediate investigation required.\n"
    elif risk_level == 'HIGH':
        summary += "⚠️  *HIGH RISK DETECTED*\nInvestigation recommended today.\n"
    elif risk_level == 'MEDIUM':
        summary += "🟡 *MEDIUM RISK*\nMonitor closely tomorrow.\n"
    else:
        summary += "✅ *ALL CLEAR*\nNo significant issues detected.\n"
    
    # Add metrics if available
    if 'daily_sales' in assessment['algorithm_results']:
        ds_result = assessment['algorithm_results']['daily_sales']
        if ds_result.get('can_analyze'):
            metrics = ds_result.get('metrics', {})
            today_sales = metrics.get('today_sales', 0)
            today_trans = metrics.get('today_transactions', 0)
            summary += f"\n*Today's Performance:*\n"
            summary += f"💰 Total Sales: GHS {today_sales:,.0f}\n"
            summary += f"🧾 Transactions: {today_trans}\n"
    
    summary += f"\n_📱 Detailed alerts sent separately if issues detected_"
    summary += "\n_Powered by PharmGuard Automated Pharmacy Audits_"
    
    return summary