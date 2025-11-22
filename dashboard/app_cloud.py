"""
PharmGuard Cloud Version
Upload CSV and get instant analysis
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
        # DEBUG: Print what we're analyzing
        print(f"\n{'='*60}")
        print(f"ANALYZING DATE: {analysis_date}")
        print(f"{'='*60}")
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

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        
        transactions_df, _ = load_transaction_data(filepath)
        # DEBUG: Check data for this specific date
        today_data = transactions_df[transactions_df['transaction_date'].dt.date == analysis_date]
        print(f"Transactions on {analysis_date}: {len(today_data)}")
        print(f"Sales on {analysis_date}: GHS {today_data['amount'].sum():,.2f}")
        
        assessment = calculate_overall_risk(analysis_date, transactions_df)
        # DEBUG: Check assessment
        print(f"Risk Score: {assessment['total_risk_score']}")
        print(f"Risk Level: {assessment['risk_level']}")
        
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
            'algorithms': {}
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
        all_dates = sorted(transactions_df['transaction_date'].dt.date.unique())
        
        results = []
        
        for analysis_date in all_dates:
            assessment = calculate_overall_risk(analysis_date, transactions_df)
            
            daily_sales = 0
            if assessment['algorithm_results']['daily_sales'].get('can_analyze'):
                daily_sales = assessment['algorithm_results']['daily_sales']['metrics'].get('today_sales', 0)
            
            results.append({
                'date': analysis_date.isoformat(),
                'risk_score': int(assessment['total_risk_score']),
                'risk_level': str(assessment['risk_level']),
                'sales': float(daily_sales),
                'requires_alert': bool(assessment['requires_alert'])
            })
        
        sys.stdout = old_stdout
        
        return jsonify({
            'total_days': len(all_dates),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)