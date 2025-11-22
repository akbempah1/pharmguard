"""
PharmGuard Web Dashboard
Flask application for visualizing theft detection results
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import json
import sys
from pathlib import Path

# Add parent directory to path to import PharmGuard modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.loader import load_transaction_data
from algorithms.master import calculate_overall_risk

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pharmguard-secret-key-change-in-production'

# Global data cache
DATA_CACHE = {
    'transactions_df': None,
    'all_dates': None,
    'loaded': False
}


def load_data():
    """Load transaction data into cache"""
    if DATA_CACHE['loaded']:
        return
    
    data_file = Path(__file__).parent.parent / 'madina_last_quarter_sales.csv'
    
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    # Suppress output during loading
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    transactions_df, _ = load_transaction_data(str(data_file))
    
    sys.stdout = old_stdout
    
    DATA_CACHE['transactions_df'] = transactions_df
    DATA_CACHE['all_dates'] = sorted(transactions_df['transaction_date'].dt.date.unique())
    DATA_CACHE['loaded'] = True


@app.route('/')
def index():
    """Main dashboard page"""
    load_data()
    
    # Get date range
    min_date = DATA_CACHE['all_dates'][0]
    max_date = DATA_CACHE['all_dates'][-1]
    
    # Default to most recent date
    selected_date = max_date
    
    return render_template('index.html', 
                         min_date=min_date.isoformat(),
                         max_date=max_date.isoformat(),
                         selected_date=selected_date.isoformat())


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint to analyze a specific date"""
    load_data()
    
    data = request.get_json()
    date_str = data.get('date')
    
    if not date_str:
        return jsonify({'error': 'No date provided'}), 400
    
    try:
        analysis_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Suppress output during analysis
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    assessment = calculate_overall_risk(analysis_date, DATA_CACHE['transactions_df'])
    
    sys.stdout = old_stdout
    
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
            
            # Add ML model name if present
            if 'ml_model' in algo_result:
                algo_display['ml_model'] = str(algo_result['ml_model'])
            
            # Convert metrics to JSON-serializable format
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


@app.route('/api/overview')
def overview():
    """API endpoint for overall statistics"""
    load_data()
    
    transactions_df = DATA_CACHE['transactions_df']
    all_dates = DATA_CACHE['all_dates']
    
    # Calculate statistics for all dates (sample for speed)
    # Use every 3rd date for faster loading
    sample_dates = all_dates[::3] if len(all_dates) > 30 else all_dates
    
    daily_stats = []
    
    import io
    old_stdout = sys.stdout
    
    for analysis_date in sample_dates:
        # Suppress output
        sys.stdout = io.StringIO()
        
        assessment = calculate_overall_risk(analysis_date, transactions_df)
        
        # Get daily sales
        daily_sales = 0
        if assessment['algorithm_results']['daily_sales'].get('can_analyze'):
            daily_sales = assessment['algorithm_results']['daily_sales']['metrics'].get('today_sales', 0)
        
        daily_stats.append({
            'date': analysis_date.isoformat(),
            'risk_score': int(assessment['total_risk_score']),
            'risk_level': str(assessment['risk_level']),
            'sales': float(daily_sales),
            'requires_alert': bool(assessment['requires_alert'])
        })
    
    sys.stdout = old_stdout
    
    # Calculate summary statistics
    df_stats = pd.DataFrame(daily_stats)
    
    summary = {
        'total_days': len(all_dates),
        'date_range': {
            'start': all_dates[0].isoformat(),
            'end': all_dates[-1].isoformat()
        },
        'risk_distribution': {str(k): int(v) for k, v in df_stats['risk_level'].value_counts().to_dict().items()},
        'alert_days': int(df_stats['requires_alert'].sum()),
        'avg_risk_score': float(df_stats['risk_score'].mean()),
        'total_sales': float(transactions_df['amount'].sum()),
        'daily_stats': daily_stats
    }
    
    return jsonify(summary)


@app.route('/api/chart/risk_timeline')
def chart_risk_timeline():
    """Generate risk score timeline chart"""
    load_data()
    
    overview_data = overview().get_json()
    daily_stats = overview_data['daily_stats']
    
    # Prepare data for chart
    dates = [stat['date'] for stat in daily_stats]
    risk_scores = [stat['risk_score'] for stat in daily_stats]
    risk_levels = [stat['risk_level'] for stat in daily_stats]
    
    # Color mapping
    color_map = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'orange',
        'critical': 'red'
    }
    colors = [color_map.get(level, 'gray') for level in risk_levels]
    
    # Create Plotly chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=risk_scores,
        mode='lines+markers',
        name='Risk Score',
        line=dict(color='rgb(31, 119, 180)', width=2),
        marker=dict(
            size=8,
            color=risk_scores,
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title="Risk Score")
        ),
        hovertemplate='Date: %{x}<br>Risk Score: %{y}/100<extra></extra>'
    ))
    
    # Add threshold lines
    fig.add_hline(y=40, line_dash="dash", line_color="orange", 
                  annotation_text="Alert Threshold (40)")
    fig.add_hline(y=60, line_dash="dash", line_color="red", 
                  annotation_text="High Risk (60)")
    
    fig.update_layout(
        title='Risk Score Timeline',
        xaxis_title='Date',
        yaxis_title='Risk Score',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))


@app.route('/api/chart/sales_vs_risk')
def chart_sales_vs_risk():
    """Generate sales vs risk correlation chart"""
    load_data()
    
    overview_data = overview().get_json()
    daily_stats = overview_data['daily_stats']
    
    sales = [stat['sales'] for stat in daily_stats]
    risk_scores = [stat['risk_score'] for stat in daily_stats]
    dates = [stat['date'] for stat in daily_stats]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sales,
        y=risk_scores,
        mode='markers',
        marker=dict(
            size=10,
            color=risk_scores,
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(title="Risk Score")
        ),
        text=dates,
        hovertemplate='Sales: GHS %{x:,.0f}<br>Risk: %{y}/100<br>Date: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Sales vs Risk Correlation',
        xaxis_title='Daily Sales (GHS)',
        yaxis_title='Risk Score',
        template='plotly_white',
        height=400
    )
    
    return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))


if __name__ == '__main__':
    app.run(debug=True, port=5000)