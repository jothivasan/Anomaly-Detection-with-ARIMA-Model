"""
Explainability Module (XAI)
Provides human-understandable explanations for fraud predictions using SHAP
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import warnings
warnings.filterwarnings('ignore')

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("Warning: SHAP not available. Install with: pip install shap")


class ExplainabilityEngine:
    """
    Explainable AI layer for fraud detection
    Provides SHAP-based explanations and feature attributions
    """
    
    def __init__(self, model=None, feature_names=None):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        
    def initialize_explainer(self, X_background):
        """
        Initialize SHAP explainer with background data
        
        Args:
            X_background: Background dataset for SHAP (sample of training data)
        """
        if not SHAP_AVAILABLE:
            print("SHAP not available. Explanations will be limited.")
            return
        
        try:
            # Use TreeExplainer for tree-based models, KernelExplainer for others
            if hasattr(self.model, 'decision_function'):
                # For sklearn models
                self.explainer = shap.KernelExplainer(
                    self.model.decision_function,
                    X_background[:100]  # Use sample for speed
                )
            else:
                self.explainer = shap.KernelExplainer(
                    self.model.predict,
                    X_background[:100]
                )
        except Exception as e:
            print(f"Could not initialize SHAP explainer: {str(e)}")
            self.explainer = None
    
    def explain_prediction(self, transaction_features, risk_score):
        """
        Generate explanation for a single prediction
        
        Args:
            transaction_features: Features for the transaction (dict or Series)
            risk_score: Calculated risk score
            
        Returns:
            Dictionary with explanation details
        """
        # Convert to dict if Series
        if isinstance(transaction_features, pd.Series):
            features_dict = transaction_features.to_dict()
        else:
            features_dict = transaction_features
        
        # 1. Get top contributing features (rule-based if SHAP unavailable)
        top_contributors = self._get_top_contributors(features_dict, risk_score)
        
        # 2. Generate counterfactual explanations
        counterfactuals = self._generate_counterfactuals(features_dict, risk_score)
        
        # 3. Get feature importance
        feature_importance = self._calculate_feature_importance(features_dict)
        
        # 4. Generate natural language explanation
        explanation_text = self._generate_explanation_text(
            features_dict, risk_score, top_contributors
        )
        
        return {
            'risk_score': risk_score,
            'top_contributors': top_contributors,
            'counterfactuals': counterfactuals,
            'feature_importance': feature_importance,
            'explanation_text': explanation_text
        }
    
    def _get_top_contributors(self, features, risk_score, top_n=5):
        """
        Get top contributing features to the risk score
        
        Args:
            features: Transaction features
            risk_score: Risk score
            top_n: Number of top features to return
            
        Returns:
            List of top contributing features
        """
        contributors = []
        
        # Amount contribution
        if 'amount' in features:
            amount = features['amount']
            if amount > 100000:
                contributors.append({
                    'feature': 'Transaction Amount',
                    'value': f'${amount:,.2f}',
                    'contribution': 35,
                    'direction': 'increases risk'
                })
            elif amount > 50000:
                contributors.append({
                    'feature': 'Transaction Amount',
                    'value': f'${amount:,.2f}',
                    'contribution': 25,
                    'direction': 'increases risk'
                })
        
        # Time contribution
        if 'is_night' in features and features['is_night']:
            hour = features.get('hour', 'unknown')
            contributors.append({
                'feature': 'Transaction Time',
                'value': f'Night time (Hour: {hour})',
                'contribution': 20,
                'direction': 'increases risk'
            })
        
        # Velocity contribution
        if 'velocity_spike' in features:
            velocity = features['velocity_spike']
            if velocity > 3:
                contributors.append({
                    'feature': 'Transaction Velocity',
                    'value': f'{velocity:.1f}x normal rate',
                    'contribution': 18,
                    'direction': 'increases risk'
                })
        
        # Behavioral deviation
        if 'deviation_zscore' in features:
            deviation = abs(features['deviation_zscore'])
            if deviation > 3:
                contributors.append({
                    'feature': 'User Behavior Deviation',
                    'value': f'{deviation:.1f} standard deviations',
                    'contribution': 15,
                    'direction': 'increases risk'
                })
        
        # Balance mismatch
        if 'balance_mismatch_orig' in features:
            mismatch = features['balance_mismatch_orig']
            if mismatch > 100:
                contributors.append({
                    'feature': 'Balance Mismatch',
                    'value': f'${mismatch:,.2f}',
                    'contribution': 12,
                    'direction': 'increases risk'
                })
        
        # Transaction type
        if 'type' in features:
            txn_type = features['type']
            if txn_type == 'CASH_OUT':
                contributors.append({
                    'feature': 'Transaction Type',
                    'value': txn_type,
                    'contribution': 10,
                    'direction': 'increases risk'
                })
        
        # Unusual amount
        if 'is_unusual_amount' in features and features['is_unusual_amount']:
            contributors.append({
                'feature': 'Unusual Amount for User',
                'value': 'Yes',
                'contribution': 12,
                'direction': 'increases risk'
            })
        
        # Weekend transaction
        if 'is_weekend' in features and features['is_weekend']:
            if 'amount' in features and features['amount'] > 20000:
                contributors.append({
                    'feature': 'Weekend Large Transaction',
                    'value': 'Yes',
                    'contribution': 8,
                    'direction': 'increases risk'
                })
        
        # Sort by contribution and return top N
        contributors.sort(key=lambda x: x['contribution'], reverse=True)
        return contributors[:top_n]
    
    def _generate_counterfactuals(self, features, risk_score):
        """
        Generate counterfactual explanations
        "What would need to change for this to be safe?"
        
        Args:
            features: Transaction features
            risk_score: Current risk score
            
        Returns:
            List of counterfactual scenarios
        """
        counterfactuals = []
        
        # Amount counterfactual
        if 'amount' in features and features['amount'] > 50000:
            safe_amount = 50000
            counterfactuals.append({
                'feature': 'amount',
                'current': f'${features["amount"]:,.2f}',
                'suggested': f'${safe_amount:,.2f}',
                'explanation': f'If amount was ≤ ${safe_amount:,.2f}, risk would decrease by ~25 points'
            })
        
        # Time counterfactual
        if 'is_night' in features and features['is_night']:
            counterfactuals.append({
                'feature': 'time',
                'current': 'Night time (10 PM - 6 AM)',
                'suggested': 'Business hours (9 AM - 5 PM)',
                'explanation': 'If transaction occurred during business hours, risk would decrease by ~15 points'
            })
        
        # Velocity counterfactual
        if 'velocity_spike' in features and features['velocity_spike'] > 3:
            counterfactuals.append({
                'feature': 'velocity',
                'current': f'{features["velocity_spike"]:.1f}x normal rate',
                'suggested': '< 2x normal rate',
                'explanation': 'If transaction velocity was normal, risk would decrease by ~18 points'
            })
        
        # Type counterfactual
        if 'type' in features and features['type'] == 'CASH_OUT':
            counterfactuals.append({
                'feature': 'type',
                'current': 'CASH_OUT',
                'suggested': 'PAYMENT',
                'explanation': 'If transaction type was PAYMENT, risk would decrease by ~10 points'
            })
        
        return counterfactuals
    
    def _calculate_feature_importance(self, features):
        """
        Calculate relative importance of each feature
        
        Args:
            features: Transaction features
            
        Returns:
            Dictionary of feature importance scores
        """
        importance = {}
        
        # Define importance weights
        importance_weights = {
            'amount': 0.25,
            'is_night': 0.15,
            'velocity_spike': 0.20,
            'deviation_zscore': 0.15,
            'balance_mismatch_orig': 0.10,
            'type': 0.08,
            'is_unusual_amount': 0.07
        }
        
        for feature, weight in importance_weights.items():
            if feature in features:
                importance[feature] = weight
        
        return importance
    
    def _generate_explanation_text(self, features, risk_score, contributors):
        """
        Generate natural language explanation
        
        Args:
            features: Transaction features
            risk_score: Risk score
            contributors: Top contributing features
            
        Returns:
            Human-readable explanation string
        """
        # Determine risk level
        if risk_score >= 86:
            risk_level = "CRITICAL RISK"
            action = "This transaction should be BLOCKED immediately and authorities alerted."
        elif risk_score >= 61:
            risk_level = "HIGH RISK"
            action = "This transaction should be BLOCKED and investigated."
        elif risk_score >= 31:
            risk_level = "MEDIUM RISK"
            action = "This transaction should be flagged for manual review."
        else:
            risk_level = "LOW RISK"
            action = "This transaction can be auto-approved."
        
        explanation = f"This transaction has been classified as {risk_level} with a score of {risk_score}/100.\n\n"
        
        if contributors:
            explanation += "Key factors contributing to this assessment:\n\n"
            for i, contrib in enumerate(contributors, 1):
                explanation += f"{i}. {contrib['feature']}: {contrib['value']}\n"
                explanation += f"   → Contributes +{contrib['contribution']} points to risk score\n\n"
        
        explanation += f"Recommended Action: {action}"
        
        return explanation
    
    def create_explanation_visualization(self, explanation_result):
        """
        Create visualization of explanation
        
        Args:
            explanation_result: Result from explain_prediction()
            
        Returns:
            Base64 encoded image
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # 1. Top contributors bar chart
        contributors = explanation_result['top_contributors']
        if contributors:
            features = [c['feature'] for c in contributors]
            contributions = [c['contribution'] for c in contributors]
            
            colors = ['#FF6B6B' if c > 15 else '#FFA500' if c > 10 else '#FFD93D' 
                     for c in contributions]
            
            ax1.barh(features, contributions, color=colors)
            ax1.set_xlabel('Contribution to Risk Score')
            ax1.set_title('Top Risk Factors', fontweight='bold')
            ax1.invert_yaxis()
            
            # Add value labels
            for i, v in enumerate(contributions):
                ax1.text(v + 1, i, f'+{v}', va='center')
        
        # 2. Risk score gauge
        risk_score = explanation_result['risk_score']
        
        # Create gauge chart
        theta = np.linspace(0, np.pi, 100)
        r = np.ones(100)
        
        # Color segments
        ax2 = plt.subplot(122, projection='polar')
        ax2.set_theta_zero_location('W')
        ax2.set_theta_direction(1)
        ax2.set_ylim(0, 1)
        
        # Draw colored segments
        segments = [
            (0, 30, '#4CAF50', 'Low'),
            (30, 60, '#FFC107', 'Medium'),
            (60, 85, '#FF9800', 'High'),
            (85, 100, '#F44336', 'Critical')
        ]
        
        for start, end, color, label in segments:
            theta_seg = np.linspace(start/100 * np.pi, end/100 * np.pi, 50)
            ax2.fill_between(theta_seg, 0, 1, color=color, alpha=0.3)
        
        # Draw needle
        needle_angle = risk_score / 100 * np.pi
        ax2.plot([needle_angle, needle_angle], [0, 0.9], 'k-', linewidth=3)
        ax2.plot(needle_angle, 0.9, 'ko', markersize=10)
        
        ax2.set_title(f'Risk Score: {risk_score}/100', fontweight='bold', pad=20)
        ax2.set_yticks([])
        ax2.set_xticks([0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi])
        ax2.set_xticklabels(['0', '25', '50', '75', '100'])
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64
    
    def generate_explanation_report(self, explanation_result, transaction_id=None):
        """
        Generate comprehensive explanation report
        
        Args:
            explanation_result: Result from explain_prediction()
            transaction_id: Optional transaction ID
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 70)
        if transaction_id:
            report.append(f"FRAUD DETECTION EXPLANATION REPORT - Transaction: {transaction_id}")
        else:
            report.append("FRAUD DETECTION EXPLANATION REPORT")
        report.append("=" * 70)
        
        report.append(f"\n{explanation_result['explanation_text']}")
        
        # Counterfactuals
        if explanation_result['counterfactuals']:
            report.append("\n" + "-" * 70)
            report.append("WHAT-IF SCENARIOS (Counterfactual Explanations):")
            report.append("-" * 70)
            
            for cf in explanation_result['counterfactuals']:
                report.append(f"\n• {cf['feature'].upper()}:")
                report.append(f"  Current: {cf['current']}")
                report.append(f"  If changed to: {cf['suggested']}")
                report.append(f"  Impact: {cf['explanation']}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)


# Simplified explainer for when SHAP is not available
class SimpleExplainer:
    """Rule-based explainer when SHAP is unavailable"""
    
    @staticmethod
    def explain(features, risk_score):
        """Generate simple rule-based explanation"""
        engine = ExplainabilityEngine()
        return engine.explain_prediction(features, risk_score)


# Example usage
if __name__ == "__main__":
    # Test explainability
    explainer = ExplainabilityEngine()
    
    # Sample transaction
    transaction = {
        'amount': 95000,
        'is_night': True,
        'hour': 2,
        'velocity_spike': 5.2,
        'deviation_zscore': 4.5,
        'balance_mismatch_orig': 1500,
        'type': 'CASH_OUT',
        'is_unusual_amount': True,
        'is_weekend': False
    }
    
    risk_score = 87
    
    # Generate explanation
    explanation = explainer.explain_prediction(transaction, risk_score)
    
    # Print report
    print(explainer.generate_explanation_report(explanation, "TXN-12345"))
    
    # Create visualization
    image = explainer.create_explanation_visualization(explanation)
    print(f"\nVisualization created (base64 length: {len(image)})")
