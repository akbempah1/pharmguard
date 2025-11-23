"""
PharmGuard Cloud Version
Upload CSV and get instant analysis with intelligent insights
"""

from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date, timedelta
import pandas as pd
import sys
from pathlib import Path
import secrets

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import load_transaction_data
from algorithms.master import calculate_overall_risk

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Create uploads folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main upload page"""
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload CSV or Excel file'}), 400
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Load and validate data
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        transactions_df, validation_result = load_transaction_data(filepath)
        
        sys.stdout = old_stdout
        
        # Get date range
        all_dates = sorted(transactions_df['transaction_date'].dt.date.unique())
        
        # Store in session
        session['current_file'] = unique_filename
        session['date_range'] = {
            'min': all_dates[0].isoformat(),
            'max': all_dates[-1].isoformat()
        }
        
        return jsonify({
            'success': True,
            'filename': filename,
            'rows': len(transactions_df),
            'date_range': {
                'min': all_dates[0].isoformat(),
                'max': all_dates[-1].isoformat()
            },
            'total_dates': len(all_dates)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500


@app.route('/dashboard')
def dashboard():
    """Show dashboard after upload"""
    if 'current_file' not in session:
        return render_template('upload.html', error='Please upload a file first')
    
    date_range = session.get('date_range', {})
    
    return render_template('dashboard_cloud.html',
                         min_date=date_range.get('min'),
                         max_date=date_range.get('max'),
                         selected_date=date_range.get('max'))


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze specific date"""
    if 'current_file' not in session:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        data = request.get_json()
        date_str = data.get('date')
        
        if not date_str:
            return jsonify({'error': 'No date provided'}), 400
        
        analysis_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Load data
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], session['current_file'])
        
        # DON'T suppress stdout yet - we want to see debug output
        transactions_df, _ = load_transaction_data(filepath)
        
        # DEBUG: Check raw data for this date BEFORE running algorithms
        today_data = transactions_df[transactions_df['transaction_date'].dt.date == analysis_date]
        print(f"\n{'='*60}")
        print(f"ANALYZING DATE: {analysis_date}")
        print(f"Raw transactions on {analysis_date}: {len(today_data)}")
        print(f"Raw sales on {analysis_date}: GHS {today_data['amount'].sum():,.2f}")
        print(f"{'='*60}")
        
        # NOW suppress stdout for algorithm execution
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        assessment = calculate_overall_risk(analysis_date, transactions_df)
        
        # Restore stdout
        sys.stdout = old_stdout
        
        # DEBUG: Check assessment results
        print(f"Risk Score: {assessment['total_risk_score']}")
        print(f"Risk Level: {assessment['risk_level']}")
        
        # DEBUG: Check what daily_sales algorithm returned
        if 'daily_sales' in assessment['algorithm_results']:
            ds_result = assessment['algorithm_results']['daily_sales']
            print(f"Daily Sales Algorithm:")
            print(f"  can_analyze: {ds_result.get('can_analyze')}")
            if ds_result.get('can_analyze'):
                print(f"  Today Sales: {ds_result['metrics'].get('today_sales', 'N/A')}")
                print(f"  Today Trans: {ds_result['metrics'].get('today_transactions', 'N/A')}")
            else:
                print(f"  REASON: Cannot analyze")
        print(f"{'='*60}\n")
        
        # Convert to JSON-serializable format
        result = {
            'date': analysis_date.isoformat(),
            'risk_score': int(assessment['total_risk_score']),
            'risk_level': str(assessment['risk_level']),
            'risk_emoji': str(assessment['risk_emoji']),
            'requires_alert': bool(assessment['requires_alert']),
            'recommended_action': str(assessment['recommended_action']),
            'alert_messages': [str(msg) for msg in assessment['alert_messages']],
            'algorithms': {},
            'debug_raw_sales': float(today_data['amount'].sum()),
            'debug_raw_trans': int(len(today_data))
        }
        
        # Add algorithm details
        for algo_name, algo_result in assessment['algorithm_results'].items():
            if algo_result.get('can_analyze'):
                algo_display = {
                    'risk_score': int(algo_result['risk_score']),
                    'alert': bool(algo_result.get('alert', False)),
                    'messages': [str(msg) for msg in algo_result.get('messages', [])],
                    'metrics': {}
                }
                
                if 'ml_model' in algo_result:
                    algo_display['ml_model'] = str(algo_result['ml_model'])
                
                if 'metrics' in algo_result:
                    for key, value in algo_result['metrics'].items():
                        if isinstance(value, (int, float)):
                            algo_display['metrics'][key] = float(value)
                        elif isinstance(value, bool):
                            algo_display['metrics'][key] = bool(value)
                        else:
                            algo_display['metrics'][key] = str(value)
                
                result['algorithms'][algo_name] = algo_display
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"\nERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/scan_all', methods=['POST'])
def scan_all():
    """Scan all dates in uploaded file"""
    if 'current_file' not in session:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], session['current_file'])
        
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        transactions_df, _ = load_transaction_data(filepath)
        
        # Get only dates with actual transactions
        dates_with_data = transactions_df['transaction_date'].dt.date.unique()
        all_dates = sorted(dates_with_data)
        
        results = []
        
        for analysis_date in all_dates:
            assessment = calculate_overall_risk(analysis_date, transactions_df)
            
            daily_sales = 0
            if assessment['algorithm_results']['daily_sales'].get('can_analyze'):
                daily_sales = assessment['algorithm_results']['daily_sales']['metrics'].get('today_sales', 0)
            else:
                # Fallback to raw calculation
                today_data = transactions_df[transactions_df['transaction_date'].dt.date == analysis_date]
                daily_sales = today_data['amount'].sum()
            
            results.append({
                'date': analysis_date.isoformat(),
                'risk_score': int(assessment['total_risk_score']),
                'risk_level': str(assessment['risk_level']),
                'sales': float(daily_sales),
                'requires_alert': bool(assessment['requires_alert'])
            })
        
        sys.stdout = old_stdout
        
        # Generate intelligent insights
        insights = generate_insights(results, transactions_df)
        
        return jsonify({
            'total_days': len(all_dates),
            'results': results,
            'insights': insights
        })
        
    except Exception as e:
        import traceback
        print(f"\nERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


def generate_insights(results, transactions_df):
    """Generate intelligent insights from scan results"""
    from collections import defaultdict
    
    total_days = len(results)
    
    if total_days == 0:
        return {}
    
    # Calculate key metrics
    high_risk_days = [r for r in results if r['risk_score'] >= 60]
    medium_risk_days = [r for r in results if 40 <= r['risk_score'] < 60]
    avg_risk = sum(r['risk_score'] for r in results) / total_days
    total_sales = sum(r['sales'] for r in results)
    avg_daily_sales = total_sales / total_days
    
    # Determine severity
    if avg_risk > 50:
        severity = "CRITICAL"
        emoji = "🔴"
    elif avg_risk > 35:
        severity = "HIGH"
        emoji = "🟠"
    elif avg_risk > 20:
        severity = "MODERATE"
        emoji = "🟡"
    else:
        severity = "LOW"
        emoji = "🟢"
    
    # Generate executive summary
    severity_messages = {
        "CRITICAL": "⚠️ URGENT: Multiple serious issues detected. Immediate action required to prevent significant losses.",
        "HIGH": "⚠️ WARNING: Several concerning patterns identified. Schedule investigation within 48 hours.",
        "MODERATE": "ℹ️ MONITOR: Some anomalies detected. Review flagged days and monitor for escalation.",
        "LOW": "✅ HEALTHY: Operations appear normal. Continue routine monitoring."
    }
    
    executive_summary = f"""{emoji} Overall Risk Level: {severity}

Period Health: {total_days} days analyzed
- {len(high_risk_days)} days require immediate investigation ({(len(high_risk_days)/total_days*100):.1f}%)
- {len(medium_risk_days)} days show moderate concerns
- Average risk score: {avg_risk:.1f}/100

{severity_messages[severity]}"""
    
    # Identify top concerns
    top_concerns = sorted(results, key=lambda x: x['risk_score'], reverse=True)[:3]
    top_concerns_list = []
    for i, day in enumerate(top_concerns, 1):
        if day['risk_score'] >= 60:
            top_concerns_list.append({
                'rank': i,
                'date': day['date'],
                'risk_score': day['risk_score'],
                'sales': day['sales'],
                'description': f"Risk: {day['risk_score']}/100 | Sales: GHS {day['sales']:,.0f}"
            })
    
    # Detect patterns
    patterns = []
    
    # Day of week analysis
    day_scores = defaultdict(list)
    day_sales = defaultdict(list)
    
    for r in results:
        date_obj = datetime.fromisoformat(r['date'])
        day_name = date_obj.strftime('%A')
        day_scores[day_name].append(r['risk_score'])
        day_sales[day_name].append(r['sales'])
    
    # Find problematic days
    for day, scores in day_scores.items():
        if len(scores) >= 2:
            avg_score = sum(scores) / len(scores)
            avg_sales = sum(day_sales[day]) / len(day_sales[day])
            
            if avg_score > 45:
                patterns.append({
                    'type': 'Day-of-Week',
                    'pattern': f"{day}s consistently show higher risk (avg: {avg_score:.1f}/100)",
                    'action': f"Review {day} operations and staffing",
                    'severity': 'high' if avg_score > 60 else 'medium'
                })
            
            # Check if specific day has significantly lower sales
            overall_avg = avg_daily_sales
            if avg_sales < overall_avg * 0.85:
                patterns.append({
                    'type': 'Sales Pattern',
                    'pattern': f"{day}s average GHS {avg_sales:,.0f} vs overall GHS {overall_avg:,.0f} ({((avg_sales/overall_avg-1)*100):.1f}%)",
                    'action': f"Investigate why {day}s underperform",
                    'severity': 'medium'
                })
    
    # Trend detection
    if total_days >= 14:
        # Split into weeks
        weeks = [results[i:i+7] for i in range(0, len(results), 7)]
        if len(weeks) >= 2:
            first_week_avg = sum(r['risk_score'] for r in weeks[0]) / len(weeks[0])
            last_week_avg = sum(r['risk_score'] for r in weeks[-1]) / len(weeks[-1])
            
            change = ((last_week_avg - first_week_avg) / first_week_avg) * 100 if first_week_avg > 0 else 0
            
            if abs(change) > 20:
                direction = "increasing" if change > 0 else "improving"
                severity = 'high' if change > 0 else 'low'
                patterns.append({
                    'type': 'Trend',
                    'pattern': f"Risk scores {direction} by {abs(change):.1f}% over period",
                    'action': f"{'Urgent: Investigate cause of deterioration' if change > 0 else 'Positive: Continue current practices'}",
                    'severity': severity
                })
            
            # Sales trend
            first_week_sales = sum(r['sales'] for r in weeks[0]) / len(weeks[0])
            last_week_sales = sum(r['sales'] for r in weeks[-1]) / len(weeks[-1])
            sales_change = ((last_week_sales - first_week_sales) / first_week_sales) * 100 if first_week_sales > 0 else 0
            
            if abs(sales_change) > 15:
                direction = "declining" if sales_change < 0 else "improving"
                patterns.append({
                    'type': 'Sales Trend',
                    'pattern': f"Sales {direction} by {abs(sales_change):.1f}% (GHS {first_week_sales:,.0f} → GHS {last_week_sales:,.0f})",
                    'action': f"{'Investigate cause of sales decline' if sales_change < 0 else 'Analyze success factors'}",
                    'severity': 'high' if sales_change < 0 else 'low'
                })
    
    # Generate recommendations
    recommendations = []
    
    if len(high_risk_days) > 0:
        top_dates = ', '.join([r['date'] for r in top_concerns_list[:3]])
        recommendations.append({
            'priority': 'IMMEDIATE',
            'action': f"Investigate {len(high_risk_days)} high-risk day(s)",
            'details': f"Priority dates: {top_dates}",
            'impact': 'HIGH',
            'timeframe': 'Within 24 hours'
        })
    
    if len(high_risk_days) >= 5:
        recommendations.append({
            'priority': 'THIS WEEK',
            'action': "Conduct comprehensive operational audit",
            'details': "Multiple issues suggest systematic problem requiring full review",
            'impact': 'HIGH',
            'timeframe': 'Within 7 days'
        })
    
    # Pattern-based recommendations
    high_severity_patterns = [p for p in patterns if p.get('severity') == 'high']
    if high_severity_patterns:
        recommendations.append({
            'priority': 'THIS WEEK',
            'action': "Address recurring patterns",
            'details': f"{len(high_severity_patterns)} pattern(s) require attention: {high_severity_patterns[0]['pattern']}",
            'impact': 'MEDIUM',
            'timeframe': 'Within 7 days'
        })
    
    recommendations.append({
        'priority': 'ONGOING',
        'action': "Continue daily monitoring with PharmGuard",
        'details': "Early detection prevents issue escalation and significant losses",
        'impact': 'MEDIUM',
        'timeframe': 'Daily'
    })
    
    # Estimate financial impact
    estimated_losses = 0
    for day in high_risk_days:
        expected = avg_daily_sales
        actual = day['sales']
        if actual < expected:
            estimated_losses += (expected - actual)
    
    # Project annual impact
    days_in_period = total_days
    high_risk_rate = len(high_risk_days) / total_days
    days_per_year = 365
    projected_annual_losses = (estimated_losses / days_in_period) * days_per_year
    
    financial_impact = {
        'total_sales': total_sales,
        'avg_daily_sales': avg_daily_sales,
        'estimated_losses': estimated_losses,
        'projected_annual_losses': projected_annual_losses,
        'high_risk_days_count': len(high_risk_days),
        'roi_calculation': {
            'pharmguard_annual_cost': 4800,  # GHS 400/month * 12
            'potential_savings': estimated_losses * 0.5,  # Assume catching 50% of issues
            'net_benefit': (estimated_losses * 0.5) - 4800,
            'roi_multiple': ((estimated_losses * 0.5) / 4800) if 4800 > 0 else 0
        }
    }
    
    return {
        'executive_summary': executive_summary,
        'severity': severity,
        'severity_emoji': emoji,
        'top_concerns': top_concerns_list,
        'patterns': patterns,
        'recommendations': recommendations,
        'financial_impact': financial_impact,
        'metrics': {
            'total_days': total_days,
            'high_risk_days': len(high_risk_days),
            'medium_risk_days': len(medium_risk_days),
            'avg_risk_score': avg_risk,
            'total_sales': total_sales,
            'avg_daily_sales': avg_daily_sales
        }
    }


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)