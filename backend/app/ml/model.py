"""
Machine Learning models for financial predictions
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
import joblib
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class FinancialMLModel:
    """ML models for financial predictions and risk assessment"""
    
    def __init__(self):
        self.revenue_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.risk_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "ml_models/"
        
        # Create model directory
        os.makedirs(self.model_path, exist_ok=True)
    
    def prepare_features(self, transactions_data: List[Dict]) -> pd.DataFrame:
        """Prepare features from transaction data"""
        if not transactions_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(transactions_data)
        
        # Convert datetime
        df['date'] = pd.to_datetime(df['created_at'])
        df['amount'] = df['amount'].astype(float)
        
        # Create time-based features
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Aggregate features by day
        daily_features = df.groupby(df['date'].dt.date).agg({
            'amount': ['sum', 'mean', 'count', 'std'],
            'hour': ['mean', 'std'],
            'is_weekend': 'first'
        }).reset_index()
        
        # Flatten column names
        daily_features.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                 for col in daily_features.columns.values]
        
        # Fill NaN values
        daily_features = daily_features.fillna(0)
        
        # Create rolling features (7-day window)
        for col in ['amount_sum', 'amount_mean', 'amount_count']:
            if col in daily_features.columns:
                daily_features[f'{col}_rolling_7'] = daily_features[col].rolling(
                    window=7, min_periods=1
                ).mean()
        
        return daily_features
    
    def train_revenue_model(self, transactions_data: List[Dict]) -> Dict[str, Any]:
        """Train revenue prediction model"""
        try:
            features_df = self.prepare_features(transactions_data)
            
            if len(features_df) < 10:
                return {'error': 'Insufficient data for training'}
            
            # Prepare target variable (next day revenue)
            features_df['target'] = features_df['amount_sum'].shift(-1)
            features_df = features_df.dropna()
            
            if len(features_df) < 5:
                return {'error': 'Insufficient data after preprocessing'}
            
            # Select features
            feature_columns = [col for col in features_df.columns 
                             if col not in ['date_', 'target'] and not col.startswith('date')]
            
            X = features_df[feature_columns]
            y = features_df['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.revenue_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_pred = self.revenue_model.predict(X_train_scaled)
            test_pred = self.revenue_model.predict(X_test_scaled)
            
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            
            # Save model
            self._save_models()
            self.is_trained = True
            
            return {
                'status': 'success',
                'train_mae': round(train_mae, 2),
                'test_mae': round(test_mae, 2),
                'feature_importance': dict(zip(
                    feature_columns, 
                    self.revenue_model.feature_importances_
                ))
            }
            
        except Exception as e:
            logger.error(f"Error training revenue model: {str(e)}")
            return {'error': f'Training failed: {str(e)}'}
    
    def predict_revenue(self, recent_data: List[Dict], days_ahead: int = 7) -> List[float]:
        """Predict future revenue"""
        try:
            if not self.is_trained:
                self._load_models()
            
            features_df = self.prepare_features(recent_data)
            
            if features_df.empty:
                return [0.0] * days_ahead
            
            # Get latest features
            latest_features = features_df.iloc[-1:].select_dtypes(include=[np.number])
            
            # Remove date columns
            feature_columns = [col for col in latest_features.columns 
                             if not col.startswith('date')]
            latest_features = latest_features[feature_columns]
            
            # Scale features
            features_scaled = self.scaler.transform(latest_features)
            
            # Generate predictions
            predictions = []
            current_features = features_scaled[0].copy()
            
            for _ in range(days_ahead):
                pred = self.revenue_model.predict(current_features.reshape(1, -1))[0]
                predictions.append(max(0, pred))  # Ensure non-negative
                
                # Update features for next prediction (simple approach)
                current_features = np.roll(current_features, 1)
                current_features[0] = pred
            
            return [round(p, 2) for p in predictions]
            
        except Exception as e:
            logger.error(f"Error predicting revenue: {str(e)}")
            return [0.0] * days_ahead
    
    def _save_models(self):
        """Save trained models"""
        try:
            joblib.dump(self.revenue_model, f"{self.model_path}/revenue_model.joblib")
            joblib.dump(self.risk_model, f"{self.model_path}/risk_model.joblib")
            joblib.dump(self.scaler, f"{self.model_path}/scaler.joblib")
            logger.info("Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
    
    def _load_models(self):
        """Load trained models"""
        try:
            if os.path.exists(f"{self.model_path}/revenue_model.joblib"):
                self.revenue_model = joblib.load(f"{self.model_path}/revenue_model.joblib")
                self.risk_model = joblib.load(f"{self.model_path}/risk_model.joblib")
                self.scaler = joblib.load(f"{self.model_path}/scaler.joblib")
                self.is_trained = True
                logger.info("Models loaded successfully")
            else:
                logger.warning("No saved models found")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")

# ===============================
