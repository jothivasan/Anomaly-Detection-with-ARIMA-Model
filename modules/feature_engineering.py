"""
Feature Engineering Module
Transforms raw transaction data into 60+ engineered features
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """
    Advanced feature engineering for fraud detection
    Creates behavioral, temporal, and statistical features
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.user_profiles = {}
        
    def engineer_features(self, df):
        """
        Main feature engineering pipeline
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # 1. Amount-based features
        df = self._create_amount_features(df)
        
        # 2. Temporal features
        df = self._create_temporal_features(df)
        
        # 3. Balance features
        df = self._create_balance_features(df)
        
        # 4. Velocity features
        df = self._create_velocity_features(df)
        
        # 5. Behavioral features
        df = self._create_behavioral_features(df)
        
        # 6. Transaction type features
        df = self._create_type_features(df)
        
        return df
    
    def _create_amount_features(self, df):
        """Create amount-based features"""
        if 'amount' in df.columns:
            # Log transformation
            df['amount_log'] = np.log1p(df['amount'])
            
            # Z-score normalization
            df['amount_zscore'] = (df['amount'] - df['amount'].mean()) / df['amount'].std()
            
            # Percentile rank
            df['amount_percentile'] = df['amount'].rank(pct=True)
            
            # Binning
            df['amount_bin'] = pd.cut(df['amount'], 
                                     bins=[0, 100, 1000, 10000, 100000, float('inf')],
                                     labels=[0, 1, 2, 3, 4])
            df['amount_bin'] = df['amount_bin'].astype(float)
            
            # Square root transformation
            df['amount_sqrt'] = np.sqrt(df['amount'])
            
            # Cube root transformation
            df['amount_cbrt'] = np.cbrt(df['amount'])
            
        return df
    
    def _create_temporal_features(self, df):
        """Create time-based features"""
        if 'step' in df.columns:
            # Convert step to hours (assuming 1 step = 1 hour)
            df['hour'] = df['step'] % 24
            df['day'] = df['step'] // 24
            df['week'] = df['step'] // (24 * 7)
            
            # Time of day categories
            df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
            df['is_morning'] = ((df['hour'] >= 6) & (df['hour'] < 12)).astype(int)
            df['is_afternoon'] = ((df['hour'] >= 12) & (df['hour'] < 18)).astype(int)
            df['is_evening'] = ((df['hour'] >= 18) & (df['hour'] < 22)).astype(int)
            
            # Day of week (0 = Monday, 6 = Sunday)
            df['day_of_week'] = df['day'] % 7
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
            # Cyclical encoding for hour
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            
            # Cyclical encoding for day of week
            df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
            
        return df
    
    def _create_balance_features(self, df):
        """Create balance-related features"""
        # Origin balance features
        if 'oldbalanceOrg' in df.columns and 'newbalanceOrig' in df.columns:
            df['balance_delta_orig'] = df['newbalanceOrig'] - df['oldbalanceOrg']
            df['balance_ratio_orig'] = np.where(
                df['oldbalanceOrg'] > 0,
                df['newbalanceOrig'] / df['oldbalanceOrg'],
                0
            )
            df['balance_pct_change_orig'] = np.where(
                df['oldbalanceOrg'] > 0,
                (df['newbalanceOrig'] - df['oldbalanceOrg']) / df['oldbalanceOrg'] * 100,
                0
            )
            
        # Destination balance features
        if 'oldbalanceDest' in df.columns and 'newbalanceDest' in df.columns:
            df['balance_delta_dest'] = df['newbalanceDest'] - df['oldbalanceDest']
            df['balance_ratio_dest'] = np.where(
                df['oldbalanceDest'] > 0,
                df['newbalanceDest'] / df['oldbalanceDest'],
                0
            )
            df['balance_pct_change_dest'] = np.where(
                df['oldbalanceDest'] > 0,
                (df['newbalanceDest'] - df['oldbalanceDest']) / df['oldbalanceDest'] * 100,
                0
            )
            
        # Balance mismatch detection
        if 'amount' in df.columns and 'balance_delta_orig' in df.columns:
            df['balance_mismatch_orig'] = np.abs(df['balance_delta_orig'] + df['amount'])
            df['balance_mismatch_dest'] = np.abs(df['balance_delta_dest'] - df['amount'])
            
        return df
    
    def _create_velocity_features(self, df):
        """Create transaction velocity features"""
        if 'nameOrig' in df.columns and 'step' in df.columns:
            # Sort by user and time
            df = df.sort_values(['nameOrig', 'step'])
            
            # Transactions per user
            df['user_txn_count'] = df.groupby('nameOrig').cumcount() + 1
            
            # Time since last transaction
            df['time_since_last_txn'] = df.groupby('nameOrig')['step'].diff()
            df['time_since_last_txn'] = df['time_since_last_txn'].fillna(0)
            
            # Transactions in last 1 hour
            df['txn_count_1h'] = df.groupby('nameOrig')['step'].transform(
                lambda x: x.rolling(window=1, min_periods=1).count()
            )
            
            # Transactions in last 24 hours
            df['txn_count_24h'] = df.groupby('nameOrig')['step'].transform(
                lambda x: x.rolling(window=24, min_periods=1).count()
            )
            
            # Average amount in last 24 hours
            if 'amount' in df.columns:
                df['avg_amount_24h'] = df.groupby('nameOrig')['amount'].transform(
                    lambda x: x.rolling(window=24, min_periods=1).mean()
                )
                
                # Velocity spike detection
                df['velocity_spike'] = np.where(
                    df['avg_amount_24h'] > 0,
                    df['amount'] / df['avg_amount_24h'],
                    0
                )
                
        return df
    
    def _create_behavioral_features(self, df):
        """Create user behavioral features"""
        if 'nameOrig' in df.columns and 'amount' in df.columns:
            # User statistics
            user_stats = df.groupby('nameOrig')['amount'].agg([
                ('user_avg_amount', 'mean'),
                ('user_std_amount', 'std'),
                ('user_min_amount', 'min'),
                ('user_max_amount', 'max'),
                ('user_median_amount', 'median')
            ]).reset_index()
            
            df = df.merge(user_stats, on='nameOrig', how='left')
            
            # Deviation from user's average
            df['deviation_from_avg'] = np.abs(df['amount'] - df['user_avg_amount'])
            df['deviation_zscore'] = np.where(
                df['user_std_amount'] > 0,
                (df['amount'] - df['user_avg_amount']) / df['user_std_amount'],
                0
            )
            
            # Is this amount unusual for this user?
            df['is_unusual_amount'] = (np.abs(df['deviation_zscore']) > 3).astype(int)
            
        return df
    
    def _create_type_features(self, df):
        """Create transaction type features"""
        if 'type' in df.columns:
            # One-hot encoding
            type_dummies = pd.get_dummies(df['type'], prefix='type')
            df = pd.concat([df, type_dummies], axis=1)
            
            # Type frequency for user
            if 'nameOrig' in df.columns:
                df['user_type_count'] = df.groupby(['nameOrig', 'type']).cumcount() + 1
                
        return df
    
    def get_feature_names(self, df):
        """Get list of all engineered features"""
        base_features = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 
                        'newbalanceOrig', 'nameDest', 'oldbalanceDest', 'newbalanceDest']
        
        all_features = [col for col in df.columns if col not in base_features]
        return all_features
    
    def get_numeric_features(self, df):
        """Get only numeric features for model input"""
        numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Exclude target variables if present
        exclude = ['isFraud', 'isFlaggedFraud']
        numeric_features = [f for f in numeric_features if f not in exclude]
        
        return numeric_features


def create_features_for_single_transaction(transaction_dict, historical_data=None):
    """
    Create features for a single transaction (real-time use case)
    
    Args:
        transaction_dict: Dictionary with transaction details
        historical_data: DataFrame with user's historical transactions
        
    Returns:
        Dictionary with engineered features
    """
    # Convert to DataFrame
    df = pd.DataFrame([transaction_dict])
    
    # If historical data available, append and engineer
    if historical_data is not None:
        df = pd.concat([historical_data, df], ignore_index=True)
    
    # Engineer features
    engineer = FeatureEngineer()
    df_engineered = engineer.engineer_features(df)
    
    # Return only the last row (current transaction)
    return df_engineered.iloc[-1].to_dict()

