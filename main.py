#!/usr/bin/env python3
"""
PharmGuard MVP - Main Execution Script
Flexible theft detection system that adapts to available data

Usage:
    python main.py --data madina_last_quarter_sales.csv --date 2025-09-15
    python main.py --data sales.csv --date today
"""

import argparse
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()  # ADD THIS


# Import PharmGuard modules
from data.loader import load_transaction_data
from data.loader import load_transaction_data
from data.validator import detect_data_capabilities
from algorithms.master import calculate_overall_risk
from alerts.whatsapp import send_pharmguard_alert


def parse_arguments():
    """Parse command line arguments"""
    
    parser = argparse.ArgumentParser(
        description='PharmGuard - Flexible ML Theft Detection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --data sales_today.csv --date today
  python main.py --data sales_nov20.xlsx --date 2025-11-20
  python main.py --data sales.csv --date yesterday --pharmacy "Kofi Pharmacy"
        """
    )
    
    parser.add_argument(
        '--data',
        required=True,
        help='Path to transaction data file (CSV or Excel)'
    )
    
    parser.add_argument(
        '--date',
        default='today',
        help='Date to analyze (YYYY-MM-DD, "today", or "yesterday")'
    )
    
    parser.add_argument(
        '--pharmacy',
        default='Your Pharmacy',
        help='Pharmacy name for alerts'
    )
    
    parser.add_argument(
        '--phone',
        default='+233XXXXXXXXX',
        help='Owner phone number for WhatsApp alerts (+233XXXXXXXXX)'
    )
    
    parser.add_argument(
        '--no-alerts',
        action='store_true',
        help='Skip sending WhatsApp alerts (analysis only)'
    )
    
    return parser.parse_args()


def parse_date(date_string):
    """Parse date string to date object"""
    
    if date_string.lower() == 'today':
        return date.today()
    elif date_string.lower() == 'yesterday':
        return date.today() - timedelta(days=1)
    else:
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except:
            print(f"❌ Invalid date format: {date_string}")
            print("   Use: YYYY-MM-DD, 'today', or 'yesterday'")
            sys.exit(1)


def main():
    """Main execution function"""
    
    print("\n" + "="*60)
    print("🛡️  PHARMGUARD - ML THEFT DETECTION SYSTEM")
    print("="*60 + "\n")
    
    # Parse arguments
    args = parse_arguments()
    
    # Validate data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        sys.exit(1)
    
    # Parse analysis date
    analysis_date = parse_date(args.date)
    print(f"📅 Analysis Date: {analysis_date.strftime('%A, %B %d, %Y')}\n")
    
    try:
        # Step 1: Load and validate data
        print("STEP 1: Loading and validating data...")
        print("-" * 60)
        
        transactions_df, validation_result = load_transaction_data(data_path)
        
        # Check what we can analyze
        capabilities = detect_data_capabilities(transactions_df, validation_result)
        
        print("\n🎯 Analysis Capabilities:")
        for capability, can_run in capabilities['can_run'].items():
            status = "✅" if can_run else "❌"
            print(f"   {status} {capability}")
        
        # Step 2: Run analysis
        print(f"\nSTEP 2: Running theft detection algorithms...")
        print("-" * 60)
        
        assessment = calculate_overall_risk(
            today_date=analysis_date,
            transactions_df=transactions_df
        )
        
        # Step 3: Generate alerts
        if not args.no_alerts:
            print(f"\nSTEP 3: Generating WhatsApp alerts...")
            print("-" * 60)
            
            pharmacy_config = {
                'name': args.pharmacy,
                'owner_phone': args.phone
            }
            
            alert_results = send_pharmguard_alert(pharmacy_config, assessment)
            
            if alert_results['alert_sent']:
                print("✅ Risk alert generated")
            if alert_results['summary_sent']:
                print("✅ Daily summary generated")
        else:
            print(f"\nSTEP 3: Alerts disabled (--no-alerts flag)")
        
        # Final summary
        print(f"\n{'='*60}")
        print("✅ PHARMGUARD ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"Risk Score: {assessment['total_risk_score']}/100")
        print(f"Risk Level: {assessment['risk_emoji']} {assessment['risk_level'].upper()}")
        
        if assessment['requires_alert']:
            print(f"\n⚠️  ACTION REQUIRED - See recommendations above")
        else:
            print(f"\n✅ No significant issues detected")
        
        print(f"\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()