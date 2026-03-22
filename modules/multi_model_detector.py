"""
Multi-Model Detection Engine
Implements ensemble of 4 complementary fraud detection models
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

# TensorFlow/Keras for LSTM Autoencoder
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. LSTM Autoencoder will be disabled.")


class MultiModelDetector:
    """
    Ensemble-based fraud detection using 4 models:
    1. SARIMAX (Time Series)
    2. Isolation Forest (Anomaly Detection)
    3. One-Class SVM (Outlier Detection)
    4. LSTM Autoencoder (Deep Learning)
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.is_trained = False
        
        # Model weights for ensemble
        self.weights = {
            'sarimax': 0.25,
            'isolation_forest': 0.30,
            'ocsvm': 0.20,
            'lstm_autoencoder': 0.25
        }
        
    def train(self, X_train, y_train=None):
        """
        Train all models
        
        Args:
            X_train: Training features (DataFrame or numpy array)
            y_train: Training labels (optional, only for supervised models)
        """
        print("Training Multi-Model Detector...")
        
        # Convert to DataFrame if needed
        if isinstance(X_train, np.ndarray):
            X_train = pd.DataFrame(X_train)
        
        # 1. Train Isolation Forest
        print("  [1/4] Training Isolation Forest...")
        self._train_isolation_forest(X_train)
        
        # 2. Train One-Class SVM
        print("  [2/4] Training One-Class SVM...")
        self._train_ocsvm(X_train)
        
        # 3. Train SARIMAX (if time series data available)
        print("  [3/4] Training SARIMAX...")
        if 'amount' in X_train.columns:
            self._train_sarimax(X_train['amount'].values)
        
        # 4. Train LSTM Autoencoder
        if TENSORFLOW_AVAILABLE:
            print("  [4/4] Training LSTM Autoencoder...")
            self._train_lstm_autoencoder(X_train)
        else:
            print("  [4/4] LSTM Autoencoder skipped (TensorFlow not available)")
        
        self.is_trained = True
        print("Training complete!")
        
    def _train_isolation_forest(self, X):
        """Train Isolation Forest model"""
        # Select numeric columns
        X_numeric = X.select_dtypes(include=[np.number])
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_numeric)
        
        # Train model
        model = IsolationForest(
            n_estimators=100,
            contamination=0.01,  # Assume 1% fraud rate
            max_features=min(10, X_scaled.shape[1]),
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled)
        
        self.models['isolation_forest'] = model
        self.scalers['isolation_forest'] = scaler
        
    def _train_ocsvm(self, X):
        """Train One-Class SVM model"""
        # Select numeric columns
        X_numeric = X.select_dtypes(include=[np.number])
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_numeric)
        
        # Sample data if too large (SVM is slow on large datasets)
        if len(X_scaled) > 10000:
            indices = np.random.choice(len(X_scaled), 10000, replace=False)
            X_scaled = X_scaled[indices]
        
        # Train model
        model = OneClassSVM(
            kernel='rbf',
            gamma='auto',
            nu=0.01  # Assume 1% outliers
        )
        model.fit(X_scaled)
        
        self.models['ocsvm'] = model
        self.scalers['ocsvm'] = scaler
        
    def _train_sarimax(self, time_series_data):
        """Train SARIMAX model"""
        try:
            # Limit data size for faster training
            data = time_series_data[:min(5000, len(time_series_data))]
            
            # Train SARIMAX
            model = sm.tsa.statespace.SARIMAX(
                data,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            results = model.fit(disp=False, maxiter=50)
            
            self.models['sarimax'] = results
            
            # Calculate residual statistics for anomaly detection
            residuals = results.resid
            self.sarimax_mean = np.mean(residuals)
            self.sarimax_std = np.std(residuals)
            
        except Exception as e:
            print(f"    Warning: SARIMAX training failed: {str(e)}")
            self.models['sarimax'] = None
            
    def _train_lstm_autoencoder(self, X):
        """Train LSTM Autoencoder model"""
        # Select numeric columns
        X_numeric = X.select_dtypes(include=[np.number])
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_numeric)
        
        # Reshape for LSTM (samples, timesteps, features)
        # For simplicity, treat each transaction as a single timestep
        X_reshaped = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))
        
        # Build autoencoder
        input_dim = X_scaled.shape[1]
        
        # Encoder
        encoder_input = layers.Input(shape=(1, input_dim))
        encoded = layers.LSTM(30, activation='relu', return_sequences=True)(encoder_input)
        encoded = layers.LSTM(15, activation='relu', return_sequences=False)(encoded)
        encoded = layers.Dense(8, activation='relu')(encoded)
        
        # Decoder
        decoded = layers.RepeatVector(1)(encoded)
        decoded = layers.LSTM(15, activation='relu', return_sequences=True)(decoded)
        decoded = layers.LSTM(30, activation='relu', return_sequences=True)(decoded)
        decoded = layers.TimeDistributed(layers.Dense(input_dim))(decoded)
        
        # Autoencoder model
        autoencoder = keras.Model(encoder_input, decoded)
        autoencoder.compile(optimizer='adam', loss='mse')
        
        # Train (only on normal transactions if labels available)
        # For unsupervised, train on all data
        autoencoder.fit(
            X_reshaped, X_reshaped,
            epochs=20,
            batch_size=32,
            validation_split=0.1,
            verbose=0
        )
        
        self.models['lstm_autoencoder'] = autoencoder
        self.scalers['lstm_autoencoder'] = scaler
        
        # Calculate reconstruction error statistics
        reconstructions = autoencoder.predict(X_reshaped, verbose=0)
        mse = np.mean(np.power(X_reshaped - reconstructions, 2), axis=(1, 2))
        self.lstm_mean = np.mean(mse)
        self.lstm_std = np.std(mse)
        
    def predict(self, X):
        """
        Predict anomaly scores for new data
        
        Args:
            X: Features (DataFrame or numpy array)
            
        Returns:
            Dictionary with individual model scores and ensemble score
        """
        if not self.is_trained:
            raise ValueError("Models not trained. Call train() first.")
        
        # Convert to DataFrame if needed
        if isinstance(X, np.ndarray):
            X = pd.DataFrame(X)
        
        scores = {}
        
        # 1. Isolation Forest
        scores['isolation_forest'] = self._predict_isolation_forest(X)
        
        # 2. One-Class SVM
        scores['ocsvm'] = self._predict_ocsvm(X)
        
        # 3. SARIMAX
        if 'sarimax' in self.models and self.models['sarimax'] is not None:
            scores['sarimax'] = self._predict_sarimax(X)
        else:
            scores['sarimax'] = np.zeros(len(X))
        
        # 4. LSTM Autoencoder
        if 'lstm_autoencoder' in self.models:
            scores['lstm_autoencoder'] = self._predict_lstm_autoencoder(X)
        else:
            scores['lstm_autoencoder'] = np.zeros(len(X))
        
        # 5. Ensemble score (weighted average)
        scores['ensemble'] = self._calculate_ensemble_score(scores)
        
        return scores
    
    def _predict_isolation_forest(self, X):
        """Predict using Isolation Forest"""
        X_numeric = X.select_dtypes(include=[np.number])
        X_scaled = self.scalers['isolation_forest'].transform(X_numeric)
        
        # Get anomaly scores (-1 for outliers, 1 for inliers)
        predictions = self.models['isolation_forest'].decision_function(X_scaled)
        
        # Convert to 0-1 scale (higher = more anomalous)
        scores = 1 / (1 + np.exp(predictions))  # Sigmoid transformation
        
        return scores
    
    def _predict_ocsvm(self, X):
        """Predict using One-Class SVM"""
        X_numeric = X.select_dtypes(include=[np.number])
        X_scaled = self.scalers['ocsvm'].transform(X_numeric)
        
        # Get decision function values
        predictions = self.models['ocsvm'].decision_function(X_scaled)
        
        # Convert to 0-1 scale
        scores = 1 / (1 + np.exp(predictions))
        
        return scores
    
    def _predict_sarimax(self, X):
        """Predict using SARIMAX"""
        if 'amount' not in X.columns:
            return np.zeros(len(X))
        
        try:
            # For each transaction, calculate residual-based anomaly score
            amounts = X['amount'].values
            
            # Simple approach: compare to historical mean/std
            z_scores = np.abs((amounts - self.sarimax_mean) / self.sarimax_std)
            
            # Convert to 0-1 scale
            scores = 1 / (1 + np.exp(-z_scores + 3))  # Sigmoid with threshold at 3 std
            
            return scores
        except Exception as e:
            print(f"SARIMAX prediction error: {str(e)}")
            return np.zeros(len(X))
    
    def _predict_lstm_autoencoder(self, X):
        """Predict using LSTM Autoencoder"""
        X_numeric = X.select_dtypes(include=[np.number])
        X_scaled = self.scalers['lstm_autoencoder'].transform(X_numeric)
        X_reshaped = X_scaled.reshape((X_scaled.shape[0], 1, X_scaled.shape[1]))
        
        # Get reconstructions
        reconstructions = self.models['lstm_autoencoder'].predict(X_reshaped, verbose=0)
        
        # Calculate reconstruction error
        mse = np.mean(np.power(X_reshaped - reconstructions, 2), axis=(1, 2))
        
        # Convert to anomaly scores
        z_scores = (mse - self.lstm_mean) / self.lstm_std
        scores = 1 / (1 + np.exp(-z_scores + 3))
        
        return scores
    
    def _calculate_ensemble_score(self, scores):
        """Calculate weighted ensemble score"""
        ensemble = (
            self.weights['isolation_forest'] * scores['isolation_forest'] +
            self.weights['ocsvm'] * scores['ocsvm'] +
            self.weights['sarimax'] * scores['sarimax'] +
            self.weights['lstm_autoencoder'] * scores['lstm_autoencoder']
        )
        
        return ensemble
    
    def get_model_info(self):
        """Get information about trained models"""
        info = {
            'is_trained': self.is_trained,
            'models': list(self.models.keys()),
            'weights': self.weights
        }
        return info

