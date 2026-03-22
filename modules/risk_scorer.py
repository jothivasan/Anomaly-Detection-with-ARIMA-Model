"""
Risk Scoring Engine
Converts binary anomaly detection to 0-100 risk scores
"""

import numpy as np
import pandas as pd
from enum import Enum


class RiskCategory(Enum):
    """Risk categories for fraud detection"""
    LOW = "Low Risk"
    MEDIUM = "Medium Risk"
    HIGH = "High Risk"
    CRITICAL = "Critical Risk"


class RiskScorer:
    """
    Fraud risk scoring engine
    Converts model outputs to interpretable 0-100 risk scores
    """
    
    def __init__(self):
        self.risk_thresholds = {
            'low': (0, 30),
            'medium': (31, 60),
            'high': (61, 85),
            'critical': (86, 100)
        }
        
        self.action_recommendations = {
            'low': 'Auto-approve transaction',
            'medium': 'Flag for manual review',
            'high': 'Block transaction and investigate',
            'critical': 'Block transaction and alert authorities'
        }
        
    def calculate_risk_score(self, model_scores, features):
        """
        Calculate comprehensive risk score (0-100)
        
        Args:
            model_scores: Dictionary with scores from each model
            features: Transaction features (dict or Series)
            
        Returns:
            Dictionary with risk score and details
        """
        # 1. Base score from ensemble model
        base_score = model_scores.get('ensemble', 0.5) * 100
        
        # 2. Apply risk boosters based on critical features
        boosters = self._calculate_risk_boosters(features)
        total_boost = sum(boosters.values())
        
        # 3. Calculate final score
        final_score = min(base_score + total_boost, 100)
        
        # 4. Determine risk category
        category = self._get_risk_category(final_score)
        
        # 5. Calculate confidence interval
        confidence = self._calculate_confidence(model_scores)
        
        return {
            'risk_score': round(final_score, 2),
            'base_score': round(base_score, 2),
            'boosters': boosters,
            'total_boost': round(total_boost, 2),
            'category': category,
            'confidence': round(confidence, 2),
            'action': self.action_recommendations[category.lower().replace(' risk', '')],
            'model_scores': {k: round(v * 100, 2) for k, v in model_scores.items()}
        }
    
    def _calculate_risk_boosters(self, features):
        """
        Calculate risk score boosters based on critical features
        
        Args:
            features: Transaction features
            
        Returns:
            Dictionary of booster values
        """
        boosters = {}
        
        # 1. Amount-based boosters
        if 'amount' in features:
            amount = features['amount']
            if amount > 100000:
                boosters['large_amount'] = 15
            elif amount > 50000:
                boosters['large_amount'] = 10
            elif amount > 10000:
                boosters['large_amount'] = 5
        
        # 2. Time-based boosters
        if 'is_night' in features and features['is_night']:
            if 'amount' in features and features['amount'] > 50000:
                boosters['night_large_transaction'] = 20
            else:
                boosters['night_transaction'] = 10
        
        # 3. Velocity boosters
        if 'velocity_spike' in features:
            velocity = features['velocity_spike']
            if velocity > 5:
                boosters['extreme_velocity'] = 25
            elif velocity > 3:
                boosters['high_velocity'] = 15
            elif velocity > 2:
                boosters['moderate_velocity'] = 8
        
        # 4. Behavioral boosters
        if 'is_unusual_amount' in features and features['is_unusual_amount']:
            boosters['unusual_for_user'] = 12
        
        if 'deviation_zscore' in features:
            deviation = abs(features['deviation_zscore'])
            if deviation > 5:
                boosters['extreme_deviation'] = 18
            elif deviation > 3:
                boosters['high_deviation'] = 10
        
        # 5. Balance mismatch boosters
        if 'balance_mismatch_orig' in features:
            mismatch = features['balance_mismatch_orig']
            if mismatch > 1000:
                boosters['balance_mismatch'] = 15
            elif mismatch > 100:
                boosters['balance_mismatch'] = 8
        
        # 6. Transaction type boosters
        if 'type' in features:
            txn_type = features['type']
            if txn_type == 'CASH_OUT':
                if 'amount' in features and features['amount'] > 50000:
                    boosters['risky_cash_out'] = 12
            elif txn_type == 'TRANSFER':
                if 'is_night' in features and features['is_night']:
                    boosters['night_transfer'] = 10
        
        # 7. New destination booster
        if 'user_txn_count' in features and features['user_txn_count'] == 1:
            boosters['first_transaction'] = 8
        
        # 8. Weekend booster
        if 'is_weekend' in features and features['is_weekend']:
            if 'amount' in features and features['amount'] > 20000:
                boosters['weekend_large'] = 8
        
        return boosters
    
    def _get_risk_category(self, score):
        """
        Determine risk category from score
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Risk category string
        """
        if score <= 30:
            return "Low Risk"
        elif score <= 60:
            return "Medium Risk"
        elif score <= 85:
            return "High Risk"
        else:
            return "Critical Risk"
    
    def _calculate_confidence(self, model_scores):
        """
        Calculate confidence in the prediction
        Based on agreement between models
        
        Args:
            model_scores: Dictionary of model scores
            
        Returns:
            Confidence percentage (0-100)
        """
        # Extract individual model scores
        scores = []
        for key in ['isolation_forest', 'ocsvm', 'sarimax', 'lstm_autoencoder']:
            if key in model_scores:
                scores.append(model_scores[key])
        
        if len(scores) < 2:
            return 50  # Low confidence if not enough models
        
        # Calculate variance in scores
        variance = np.var(scores)
        
        # Low variance = high agreement = high confidence
        # High variance = low agreement = low confidence
        confidence = 100 * (1 - min(variance * 4, 1))
        
        return confidence
    
    def get_risk_breakdown(self, risk_result):
        """
        Get detailed breakdown of risk score
        
        Args:
            risk_result: Result from calculate_risk_score()
            
        Returns:
            Formatted string with breakdown
        """
        lines = []
        lines.append(f"=== RISK SCORE BREAKDOWN ===")
        lines.append(f"Final Risk Score: {risk_result['risk_score']}/100")
        lines.append(f"Category: {risk_result['category']}")
        lines.append(f"Confidence: {risk_result['confidence']}%")
        lines.append(f"\nBase Score: {risk_result['base_score']}")
        lines.append(f"\nRisk Boosters:")
        
        for booster, value in risk_result['boosters'].items():
            lines.append(f"  + {booster}: +{value}")
        
        lines.append(f"\nTotal Boost: +{risk_result['total_boost']}")
        lines.append(f"\nModel Contributions:")
        
        for model, score in risk_result['model_scores'].items():
            if model != 'ensemble':
                lines.append(f"  - {model}: {score}/100")
        
        lines.append(f"\nRecommended Action:")
        lines.append(f"  {risk_result['action']}")
        
        return "\n".join(lines)
    
    def batch_score(self, model_scores_list, features_list):
        """
        Score multiple transactions at once
        
        Args:
            model_scores_list: List of model score dictionaries
            features_list: List of feature dictionaries
            
        Returns:
            List of risk results
        """
        results = []
        for scores, features in zip(model_scores_list, features_list):
            result = self.calculate_risk_score(scores, features)
            results.append(result)
        return results
    
    def get_statistics(self, risk_results):
        """
        Get statistics from multiple risk assessments
        
        Args:
            risk_results: List of risk result dictionaries
            
        Returns:
            Dictionary with statistics
        """
        scores = [r['risk_score'] for r in risk_results]
        categories = [r['category'] for r in risk_results]
        
        category_counts = {
            'Low Risk': 0,
            'Medium Risk': 0,
            'High Risk': 0,
            'Critical Risk': 0
        }
        
        for cat in categories:
            category_counts[cat] += 1
        
        return {
            'total_transactions': len(risk_results),
            'average_risk_score': np.mean(scores),
            'median_risk_score': np.median(scores),
            'max_risk_score': np.max(scores),
            'min_risk_score': np.min(scores),
            'category_distribution': category_counts,
            'high_risk_percentage': (category_counts['High Risk'] + category_counts['Critical Risk']) / len(risk_results) * 100
        }


class RiskReporter:
    """Generate risk assessment reports"""
    
    @staticmethod
    def generate_summary_report(risk_results):
        """
        Generate summary report for multiple transactions
        
        Args:
            risk_results: List of risk assessment results
            
        Returns:
            Formatted report string
        """
        scorer = RiskScorer()
        stats = scorer.get_statistics(risk_results)
        
        report = []
        report.append("=" * 60)
        report.append("FRAUD RISK ASSESSMENT SUMMARY REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal Transactions Analyzed: {stats['total_transactions']}")
        report.append(f"\nRisk Score Statistics:")
        report.append(f"  Average: {stats['average_risk_score']:.2f}")
        report.append(f"  Median: {stats['median_risk_score']:.2f}")
        report.append(f"  Range: {stats['min_risk_score']:.2f} - {stats['max_risk_score']:.2f}")
        report.append(f"\nRisk Category Distribution:")
        
        for category, count in stats['category_distribution'].items():
            percentage = (count / stats['total_transactions']) * 100
            report.append(f"  {category}: {count} ({percentage:.1f}%)")
        
        report.append(f"\nHigh-Risk Transactions: {stats['high_risk_percentage']:.1f}%")
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    @staticmethod
    def generate_transaction_report(risk_result, transaction_id=None):
        """
        Generate detailed report for single transaction
        
        Args:
            risk_result: Risk assessment result
            transaction_id: Optional transaction ID
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        if transaction_id:
            report.append(f"TRANSACTION RISK REPORT - ID: {transaction_id}")
        else:
            report.append("TRANSACTION RISK REPORT")
        report.append("=" * 60)
        
        # Risk score with visual indicator
        score = risk_result['risk_score']
        category = risk_result['category']
        
        # Visual risk meter
        filled = int(score / 10)
        meter = "█" * filled + "░" * (10 - filled)
        report.append(f"\nRisk Score: {score}/100")
        report.append(f"[{meter}]")
        report.append(f"\nRisk Category: {category}")
        report.append(f"Confidence: {risk_result['confidence']}%")
        
        # Model scores
        report.append(f"\nModel Scores:")
        for model, score in risk_result['model_scores'].items():
            if model != 'ensemble':
                report.append(f"  • {model.replace('_', ' ').title()}: {score}/100")
        
        # Risk factors
        if risk_result['boosters']:
            report.append(f"\nRisk Factors Detected:")
            for factor, boost in risk_result['boosters'].items():
                report.append(f"  ⚠ {factor.replace('_', ' ').title()}: +{boost} points")
        
        # Recommendation
        report.append(f"\nRecommended Action:")
        report.append(f"  → {risk_result['action']}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)

