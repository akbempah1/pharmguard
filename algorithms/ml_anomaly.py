"""
Algorithm 6: ML-Based Anomaly Detection
Uses Isolation Forest (scikit-learn) for unsupervised anomaly detection

REQUIRES: transaction_date, amount, quantity
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path


class MLAnomalyDetector:
    """
    Machine Learning anomaly detector using Isolation Forest
    """
    
    def __init__(self, model_path='models/isolation_forest.pkl'):
        self.model = None
        self.scaler = None
        self.model_path = Path(model_path)
        self.is_trained = False
    
    def train(self, transactions_df, contamination=0.1):
        """
        Train Isolation Forest on historical data
        
        Args:
            transactions_df: Historical transaction data
            contamination: Expected proportion of outliers (default 10%)
        """
        
        # Aggregate daily features
        daily_features = self._extract_daily_features(transactions_df)
        
        if len(daily_features) < 30:
            return False, "Insufficient data for training (need 30+ days)"
        
        # Prepare features
        feature_columns = ['total_sales', 'transaction_count', 'avg_transaction_value', 
                          'high_value_ratio', 'high_value_total', 'small_transaction_ratio',
                          'sales_concentration', 'avg_quantity', 'day_of_week']
        
        X = daily_features[feature_columns].values
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_scaled)
        
        self.is_trained = True
        
        # Save model
        self._save_model()
        
        return True, f"Model trained on {len(daily_features)} days"
    
    def _extract_daily_features(self, transactions_df):
        """Extract features for each day"""
        
        features_list = []
        
        for date in transactions_df['transaction_date'].dt.date.unique():
            day_data = transactions_df[transactions_df['transaction_date'].dt.date == date]
            
            if len(day_data) == 0:
                continue
            
            # Day of week (important for pattern)
            day_of_week = date.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Basic metrics
            total_sales = day_data['amount'].sum()
            transaction_count = len(day_data)
            avg_transaction = day_data['amount'].mean()
            
            # Value distribution
            high_value_count = (day_data['amount'] >= 50).sum()
            high_value_ratio = high_value_count / transaction_count if transaction_count > 0 else 0
            high_value_total = day_data[day_data['amount'] >= 50]['amount'].sum()
            
            small_count = (day_data['amount'] < 10).sum()
            small_ratio = small_count / transaction_count if transaction_count > 0 else 0
            
            # Sales concentration (are sales evenly distributed or concentrated?)
            top_10_sales = day_data.nlargest(min(10, len(day_data)), 'amount')['amount'].sum()
            sales_concentration = top_10_sales / total_sales if total_sales > 0 else 0
            
            # Average quantity per transaction
            avg_quantity = day_data['quantity'].mean()
            
            features_list.append({
                'date': date,
                'total_sales': total_sales,
                'transaction_count': transaction_count,
                'avg_transaction_value': avg_transaction,
                'high_value_ratio': high_value_ratio,
                'high_value_total': high_value_total,
                'small_transaction_ratio': small_ratio,
                'sales_concentration': sales_concentration,
                'avg_quantity': avg_quantity,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend
            })
        
        return pd.DataFrame(features_list)
    
    def predict(self, today_date, transactions_df):
        """
        Predict if today is an anomaly
        
        Returns:
            dict: Prediction results with anomaly score
        """
        
        if not self.is_trained:
            # Try to load saved model
            if not self._load_model():
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0,
                    'error': 'Model not trained'
                }
        
        # Get today's data
        today_data = transactions_df[transactions_df['transaction_date'].dt.date == today_date]
        
        if len(today_data) == 0:
            return {
                'is_anomaly': False,
                'anomaly_score': 0,
                'error': 'No data for this date'
            }
        
        # Extract features for today
        day_of_week = today_date.weekday()
        transaction_count = len(today_data)
        total_sales = today_data['amount'].sum()
        
        high_value_count = (today_data['amount'] >= 50).sum()
        high_value_ratio = high_value_count / transaction_count if transaction_count > 0 else 0
        high_value_total = today_data[today_data['amount'] >= 50]['amount'].sum()
        
        small_count = (today_data['amount'] < 10).sum()
        small_ratio = small_count / transaction_count if transaction_count > 0 else 0
        
        top_10_sales = today_data.nlargest(min(10, len(today_data)), 'amount')['amount'].sum()
        sales_concentration = top_10_sales / total_sales if total_sales > 0 else 0
        
        features = {
            'total_sales': total_sales,
            'transaction_count': transaction_count,
            'avg_transaction_value': today_data['amount'].mean(),
            'high_value_ratio': high_value_ratio,
            'high_value_total': high_value_total,
            'small_transaction_ratio': small_ratio,
            'sales_concentration': sales_concentration,
            'avg_quantity': today_data['quantity'].mean(),
            'day_of_week': day_of_week
        }
        
        X = np.array([[
            features['total_sales'],
            features['transaction_count'],
            features['avg_transaction_value'],
            features['high_value_ratio'],
            features['high_value_total'],
            features['small_transaction_ratio'],
            features['sales_concentration'],
            features['avg_quantity'],
            features['day_of_week']
        ]])
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]  # 1 = normal, -1 = anomaly
        anomaly_score = self.model.score_samples(X_scaled)[0]  # Lower = more anomalous
        
        # Convert to 0-100 risk score
        # Map anomaly_score (typically -0.5 to 0.5) to 0-100
        # Lower score = higher risk
        risk_score = max(0, min(100, int((0.5 - anomaly_score) * 70)))
        
        return {
            'is_anomaly': prediction == -1,
            'anomaly_score': float(anomaly_score),
            'risk_score': risk_score,
            'features': features,
            'error': None
        }
    
    def _save_model(self):
        """Save trained model to disk"""
        self.model_path.parent.mkdir(exist_ok=True)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler
            }, f)
    
    def _load_model(self):
        """Load trained model from disk"""
        if not self.model_path.exists():
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.scaler = data['scaler']
                self.is_trained = True
            return True
        except:
            return False


def calculate_ml_anomaly(today_date, transactions_df):
    """
    Wrapper function for ML anomaly detection
    
    Returns:
        dict: Risk assessment
    """
    
    detector = MLAnomalyDetector()
    
    # Train if not already trained
    if not detector.is_trained and not detector._load_model():
        # Train on all historical data except today
        historical = transactions_df[transactions_df['transaction_date'].dt.date < today_date]
        success, message = detector.train(historical)
        
        if not success:
            return {
                'algorithm': 'ml_anomaly_detection',
                'risk_score': 0,
                'alert': False,
                'messages': [message],
                'can_analyze': False
            }
    
    # Predict
    result = detector.predict(today_date, transactions_df)
    
    if result.get('error'):
        return {
            'algorithm': 'ml_anomaly_detection',
            'risk_score': 0,
            'alert': False,
            'messages': [result['error']],
            'can_analyze': False
        }
    
    # Scoring
    risk_score = result['risk_score']
    is_anomaly = result['is_anomaly']
    
    messages = []
    if is_anomaly:
        messages.append(f"🤖 ML Model flagged this day as anomalous")
        messages.append(f"   Anomaly Score: {result['anomaly_score']:.3f} (lower = more suspicious)")
        messages.append(f"   Based on: sales, transaction patterns, value distribution")
    
    return {
        'algorithm': 'ml_anomaly_detection',
        'risk_score': min(risk_score, 35),  # Cap at 35
        'alert': is_anomaly,
        'messages': messages,
        'metrics': result['features'],
        'can_analyze': True,
        'ml_model': 'Isolation Forest (scikit-learn)'
    }