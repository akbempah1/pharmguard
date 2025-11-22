"""
WhatsApp alert integration using Twilio
"""

import os
from twilio.rest import Client
from alerts.message_generator import generate_alert_message, generate_daily_summary


def send_whatsapp_message(phone_number, message):
    """
    Send WhatsApp message via Twilio
    
    Args:
        phone_number: Recipient phone (format: +233XXXXXXXXX)
        message: Message text
        
    Returns:
        dict: Sending result
    """
    
    # Get Twilio credentials from environment variables
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    # Check if credentials are set
    if not all([account_sid, auth_token, from_number]):
        print("⚠️  WhatsApp sending DISABLED - Twilio credentials not set")
        print("   Set environment variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER")
        print("\n📱 MESSAGE PREVIEW:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        return {
            'success': False,
            'mode': 'preview',
            'error': 'Twilio credentials not configured'
        }
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send message
        message_obj = client.messages.create(
            from_=from_number,
            body=message,
            to=f'whatsapp:{phone_number}'
        )
        
        print(f"✅ WhatsApp message sent successfully!")
        print(f"   Message SID: {message_obj.sid}")
        print(f"   Status: {message_obj.status}")
        
        return {
            'success': True,
            'mode': 'live',
            'message_sid': message_obj.sid,
            'status': message_obj.status
        }
    
    except Exception as e:
        print(f"❌ Failed to send WhatsApp message: {str(e)}")
        return {
            'success': False,
            'mode': 'live',
            'error': str(e)
        }


def send_pharmguard_alert(pharmacy_config, assessment):
    """
    Send PharmGuard alerts based on risk assessment
    
    Args:
        pharmacy_config: dict with pharmacy details
        assessment: Risk assessment from master.py
        
    Returns:
        dict: Sending results
    """
    
    pharmacy_name = pharmacy_config.get('name', 'Pharmacy')
    owner_phone = pharmacy_config.get('owner_phone', '+233XXXXXXXXX')
    
    results = {
        'alert_sent': False,
        'summary_sent': False,
        'errors': []
    }
    
    # Send alert if risk threshold exceeded
    if assessment['requires_alert']:
        print("\n🚨 HIGH RISK DETECTED - Sending alert...")
        alert_message = generate_alert_message(assessment, pharmacy_name)
        
        if alert_message:
            result = send_whatsapp_message(owner_phone, alert_message)
            
            if result['success']:
                results['alert_sent'] = True
            else:
                results['errors'].append(result.get('error', 'Unknown error'))
    
    # Always send daily summary
    print("\n📊 Sending daily summary...")
    summary_message = generate_daily_summary(assessment, pharmacy_name)
    result = send_whatsapp_message(owner_phone, summary_message)
    
    if result['success']:
        results['summary_sent'] = True
    else:
        results['errors'].append(result.get('error', 'Unknown error'))
    
    return results