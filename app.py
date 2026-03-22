"""
Intelligent Multi-Layer Fraud Detection Platform
Optimized for Local Development and Deployment
Version: 2.0.0
"""

import os
import logging
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from modules.feature_engineering import FeatureEngineer
from modules.multi_model_detector import MultiModelDetector
from modules.dynamic_threshold import DynamicThreshold
from modules.risk_scorer import RiskScorer, RiskReporter
from modules.explainability import ExplainabilityEngine
from modules.realtime_simulator import RealtimeSimulator

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS
CORS(app)

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize components
feature_engineer = FeatureEngineer()
multi_model_detector = MultiModelDetector()
dynamic_threshold = DynamicThreshold()
risk_scorer = RiskScorer()
explainability_engine = ExplainabilityEngine()
realtime_simulator = RealtimeSimulator()

# Global model state
model_state = {
    'trained': False,
    'training_data_shape': None,
    'training_timestamp': None,
    'model_info': {}
}


# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_trained': model_state['trained']
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and validation"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Only CSV and XLSX allowed'}), 400
        
        # Read file
        df = read_uploaded_file(file)
        
        if len(df) == 0:
            return jsonify({'error': 'File is empty'}), 400
        
        # Generate file info
        file_info = {
            'filename': secure_filename(file.filename),
            'rows': int(len(df)),
            'columns': int(len(df.columns)),
            'column_names': list(df.columns),
            'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing_values': {col: int(df[col].isnull().sum()) for col in df.columns},
            'sample_data': df.head(5).to_dict('records')
        }
        
        logger.info(f"File uploaded: {file.filename}, Rows: {len(df)}")
        
        return jsonify({
            'success': True,
            'file_info': file_info
        })
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_comprehensive():
    """Comprehensive fraud detection analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        df = read_uploaded_file(file)
        
        analysis_mode = request.form.get('analysis_mode', 'full')
        
        logger.info(f"Starting {analysis_mode} analysis on {len(df)} transactions")
        
        # Step 1: Feature Engineering
        logger.debug("Step 1: Feature Engineering")
        df_engineered = feature_engineer.engineer_features(df)
        
        # Get numeric features
        feature_cols = [col for col in df_engineered.columns 
                      if df_engineered[col].dtype in ['int64', 'float64']]
        X = df_engineered[feature_cols].fillna(0)
        
        # Step 2: Train/Update Models
        logger.debug("Step 2: Training models")
        if not model_state['trained'] or analysis_mode == 'full':
            train_size = min(10000, len(X))
            X_train = X.head(train_size)
            multi_model_detector.train(X_train)
            model_state['trained'] = True
            model_state['training_data_shape'] = X_train.shape
            model_state['training_timestamp'] = datetime.now().isoformat()
            model_state['model_info'] = multi_model_detector.get_model_info()
        
        # Step 3: Predict Anomaly Scores (batch processing)
        logger.debug("Step 3: Detecting anomalies")
        batch_size = 1000
        all_predictions = []
        
        for i in range(0, len(X), batch_size):
            batch = X.iloc[i:i+batch_size]
            predictions = multi_model_detector.predict(batch)
            all_predictions.append(predictions)
        
        # Combine batch predictions
        combined_scores = combine_predictions(all_predictions)
        
        # Step 4: Dynamic Thresholding
        logger.debug("Step 4: Calculating dynamic thresholds")
        # Calculate simple statistical thresholds
        ensemble_scores = combined_scores['ensemble']
        thresholds = {
            'low': float(np.percentile(ensemble_scores, 30)),
            'medium': float(np.percentile(ensemble_scores, 60)),
            'high': float(np.percentile(ensemble_scores, 85)),
            'critical': float(np.percentile(ensemble_scores, 95))
        }
        
        # Step 5: Risk Scoring
        logger.debug("Step 5: Computing risk scores")
        risk_results = calculate_risk_scores(df_engineered, combined_scores, risk_scorer)
        
        # Step 6: Explainability (for high-risk transactions)
        logger.debug("Step 6: Generating explanations")
        explanations = generate_explanations(
            X, combined_scores, risk_results, feature_cols, explainability_engine
        )
        
        # Step 7: Generate Visualizations
        logger.debug("Step 7: Creating visualizations")
        visualizations = create_visualizations(df, df_engineered, risk_results, combined_scores)
        
        # Step 8: Compile Statistics
        statistics = compile_statistics(df, risk_results, thresholds, combined_scores)
        
        # Step 9: Generate Reports
        summary_report = RiskReporter.generate_summary_report(risk_results)
        
        logger.info(f"Analysis complete. High-risk transactions: {statistics['fraud_detection']['flagged_transactions']}")
        
        # Calculate model performance metrics
        model_performance = {
            'sarimax_avg': float(np.mean(combined_scores.get('sarimax', [0])) * 100) if 'sarimax' in combined_scores else 0,
            'isolation_forest_avg': float(np.mean(combined_scores['isolation_forest']) * 100),
            'ocsvm_avg': float(np.mean(combined_scores['ocsvm']) * 100),
            'lstm_avg': float(np.mean(combined_scores.get('lstm_autoencoder', [0])) * 100) if 'lstm_autoencoder' in combined_scores else 0,
            'ensemble_avg': float(np.mean(combined_scores['ensemble']) * 100)
        }
        
        # Prepare response
        response = {
            'success': True,
            'statistics': statistics,
            'risk_results': {
                'total_transactions': len(risk_results),
                'high_risk_count': len([r for r in risk_results if r['category'] in ['High Risk', 'Critical Risk']]),
                'medium_risk_count': len([r for r in risk_results if r['category'] == 'Medium Risk']),
                'low_risk_count': len([r for r in risk_results if r['category'] == 'Low Risk']),
                'average_risk_score': float(np.mean([r['risk_score'] for r in risk_results])),
                'samples': risk_results[:100]
            },
            'high_risk_count': len([r for r in risk_results if r['category'] in ['High Risk', 'Critical Risk']]),
            'thresholds': {k: float(v) for k, v in thresholds.items()},
            'visualizations': visualizations,
            'explanations': explanations,
            'summary_report': summary_report,
            'model_info': model_state['model_info'],
            'model_performance': model_performance,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(error_trace)
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Server Error: {error}')
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413


# Helper functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def read_uploaded_file(file):
    """Read uploaded CSV or Excel file"""
    if file.filename.endswith('.xlsx'):
        return pd.read_excel(file)
    elif file.filename.endswith('.csv'):
        return pd.read_csv(file)
    else:
        raise ValueError('Unsupported file format')


def combine_predictions(all_predictions):
    """Combine batch predictions into single arrays"""
    combined_scores = {
        'isolation_forest': np.concatenate([p['isolation_forest'] for p in all_predictions]),
        'ocsvm': np.concatenate([p['ocsvm'] for p in all_predictions]),
        'ensemble': np.concatenate([p['ensemble'] for p in all_predictions])
    }
    
    if 'sarimax' in all_predictions[0]:
        combined_scores['sarimax'] = np.concatenate([p['sarimax'] for p in all_predictions])
    if 'lstm_autoencoder' in all_predictions[0]:
        combined_scores['lstm_autoencoder'] = np.concatenate([p['lstm_autoencoder'] for p in all_predictions])
    
    return combined_scores


def calculate_risk_scores(df_engineered, combined_scores, risk_scorer):
    """Calculate risk scores for all transactions"""
    risk_results = []
    for idx in range(len(df_engineered)):
        model_scores = {key: float(scores[idx]) for key, scores in combined_scores.items()}
        features = df_engineered.iloc[idx].to_dict()
        risk_result = risk_scorer.calculate_risk_score(model_scores, features)
        risk_result['index'] = int(idx)
        risk_results.append(risk_result)
    return risk_results


def generate_explanations(X, combined_scores, risk_results, feature_cols, explainability_engine):
    """Generate explanations for high-risk transactions"""
    high_risk_indices = [r['index'] for r in risk_results if r['risk_score'] > 60][:10]
    explanations = []
    
    for idx in high_risk_indices:
        try:
            explanation = explainability_engine.explain_prediction(
                X.iloc[idx:idx+1],
                combined_scores['ensemble'][idx],
                feature_names=feature_cols
            )
            explanation['transaction_index'] = int(idx)
            explanations.append(explanation)
        except Exception as e:
            logger.warning(f"Explanation error for index {idx}: {str(e)}")
    
    return explanations


def create_visualizations(df_original, df_engineered, risk_results, model_scores):
    """Create comprehensive visualizations"""
    visualizations = {}
    
    try:
        # 1. Risk Score Distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        risk_scores = [r['risk_score'] for r in risk_results]
        ax.hist(risk_scores, bins=50, color='#4A90E2', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Risk Score', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Risk Score Distribution', fontsize=14, fontweight='bold')
        ax.axvline(x=60, color='red', linestyle='--', label='High Risk Threshold')
        ax.legend()
        visualizations['risk_distribution'] = fig_to_base64(fig)
        plt.close()
        
        # 2. Risk Category Pie Chart
        fig, ax = plt.subplots(figsize=(8, 8))
        categories = [r['category'] for r in risk_results]
        category_counts = pd.Series(categories).value_counts()
        colors = ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
        ax.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%',
               colors=colors, startangle=90)
        ax.set_title('Risk Category Distribution', fontsize=14, fontweight='bold')
        visualizations['risk_categories'] = fig_to_base64(fig)
        plt.close()
        
        # 3. Model Score Comparison
        fig, ax = plt.subplots(figsize=(12, 6))
        model_names = list(model_scores.keys())
        avg_scores = [np.mean(model_scores[model]) for model in model_names]
        ax.bar(model_names, avg_scores, color=['#4A90E2', '#E24A90', '#90E24A', '#E2904A', '#904AE2'])
        ax.set_xlabel('Model', fontsize=12)
        ax.set_ylabel('Average Anomaly Score', fontsize=12)
        ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        visualizations['model_comparison'] = fig_to_base64(fig)
        plt.close()
        
    except Exception as e:
        logger.error(f"Visualization error: {str(e)}")
    
    return visualizations


def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string"""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    return image_base64


def compile_statistics(df, risk_results, thresholds, model_scores):
    """Compile comprehensive statistics"""
    risk_scores = [r['risk_score'] for r in risk_results]
    
    statistics = {
        'total_transactions': len(df),
        'risk_summary': {
            'mean_risk_score': float(np.mean(risk_scores)),
            'median_risk_score': float(np.median(risk_scores)),
            'std_risk_score': float(np.std(risk_scores)),
            'min_risk_score': float(np.min(risk_scores)),
            'max_risk_score': float(np.max(risk_scores))
        },
        'category_distribution': {
            'Low Risk': len([r for r in risk_results if r['category'] == 'Low Risk']),
            'Medium Risk': len([r for r in risk_results if r['category'] == 'Medium Risk']),
            'High Risk': len([r for r in risk_results if r['category'] == 'High Risk']),
            'Critical Risk': len([r for r in risk_results if r['category'] == 'Critical Risk'])
        },
        'fraud_detection': {
            'flagged_transactions': len([r for r in risk_results if r['risk_score'] > 60]),
            'flagged_percentage': float(len([r for r in risk_results if r['risk_score'] > 60]) / len(risk_results) * 100),
            'critical_transactions': len([r for r in risk_results if r['category'] == 'Critical Risk'])
        },
        'model_statistics': {
            model: {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores))
            }
            for model, scores in model_scores.items()
        },
        'thresholds': thresholds,
        'data_quality': {
            'columns': len(df.columns),
            'missing_values': int(df.isnull().sum().sum()),
            'duplicate_rows': int(df.duplicated().sum())
        }
    }
    
    return statistics


if __name__ == '__main__':
    print("=" * 80)
    print("INTELLIGENT MULTI-LAYER FRAUD DETECTION PLATFORM")
    print("=" * 80)
    print("Features:")
    print("  + Multi-Model Ensemble (SARIMAX, Isolation Forest, One-Class SVM, LSTM)")
    print("  + Dynamic Adaptive Thresholding")
    print("  + Risk Scoring Engine (0-100 scale)")
    print("  + Explainable AI (SHAP)")
    print("  + Real-time Simulation")
    print("  + Advanced Feature Engineering")
    print("=" * 80)
    print(f"Server starting at http://localhost:5000")
    print("=" * 80)
    
    # Run application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
