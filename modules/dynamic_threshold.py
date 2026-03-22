"""
Dynamic Thresholding System
Adaptive anomaly detection boundaries based on context
"""

import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict


class DynamicThreshold:
    """
    Context-aware dynamic thresholding for fraud detection
    Adjusts thresholds based on:
    - Transaction type
    - Time of day
    - Historical fraud rate
    - User behavior patterns
    """
    
    def __init__(self):
        self.base_threshold = 0.5  # Base anomaly score threshold
        self.fraud_history = []
        self.type_multipliers = {
            'PAYMENT': 1.0,
            'TRANSFER': 0.9,  # Stricter for transfers
            'CASH_OUT': 0.85,  # Stricter for cash out
            'DEBIT': 1.0,
            'CASH_IN': 1.1  # More lenient for cash in
        }
        
    def calculate_threshold(self, transaction, anomaly_score):
        """
        Calculate dynamic threshold for a transaction
        
        Args:
            transaction: Dictionary or Series with transaction details
            anomaly_score: Base anomaly score from models
            
        Returns:
            Adjusted threshold value
        """
        threshold = self.base_threshold
        
        # 1. Adjust based on transaction type
        if 'type' in transaction:
            txn_type = transaction['type']
            threshold *= self.type_multipliers.get(txn_type, 1.0)
        
        # 2. Adjust based on time of day
        if 'hour' in transaction or 'is_night' in transaction:
            if 'is_night' in transaction and transaction['is_night']:
                threshold *= 0.9  # Stricter at night
            elif 'hour' in transaction:
                hour = transaction['hour']
                if 22 <= hour or hour <= 6:
                    threshold *= 0.9  # Stricter at night
                elif 9 <= hour <= 17:
                    threshold *= 1.05  # More lenient during business hours
        
        # 3. Adjust based on amount
        if 'amount' in transaction:
            amount = transaction['amount']
            if amount > 100000:
                threshold *= 0.85  # Stricter for large amounts
            elif amount > 50000:
                threshold *= 0.9
            elif amount < 100:
                threshold *= 1.1  # More lenient for small amounts
        
        # 4. Adjust based on recent fraud rate
        recent_fraud_rate = self._get_recent_fraud_rate()
        if recent_fraud_rate > 0.05:  # If fraud rate > 5%
            threshold *= 0.9  # Be more strict
        elif recent_fraud_rate < 0.01:  # If fraud rate < 1%
            threshold *= 1.05  # Be more lenient
        
        # 5. Adjust based on user behavior
        if 'is_unusual_amount' in transaction and transaction['is_unusual_amount']:
            threshold *= 0.85  # Stricter for unusual amounts
        
        if 'velocity_spike' in transaction and transaction['velocity_spike'] > 3:
            threshold *= 0.8  # Stricter for velocity spikes
        
        # 6. Weekend adjustment
        if 'is_weekend' in transaction and transaction['is_weekend']:
            threshold *= 0.95  # Slightly stricter on weekends
        
        # Ensure threshold stays in reasonable range
        threshold = np.clip(threshold, 0.3, 0.8)
        
        return threshold
    
    def is_fraud(self, transaction, anomaly_score):
        """
        Determine if transaction is fraudulent based on dynamic threshold
        
        Args:
            transaction: Transaction details
            anomaly_score: Anomaly score from models (0-1)
            
        Returns:
            Boolean indicating if transaction is fraud
        """
        threshold = self.calculate_threshold(transaction, anomaly_score)
        return anomaly_score > threshold
    
    def update_fraud_history(self, is_fraud):
        """
        Update fraud history for adaptive thresholding
        
        Args:
            is_fraud: Boolean indicating if transaction was fraud
        """
        self.fraud_history.append(is_fraud)
        
        # Keep only last 1000 transactions
        if len(self.fraud_history) > 1000:
            self.fraud_history = self.fraud_history[-1000:]
    
    def _get_recent_fraud_rate(self, window=100):
        """
        Calculate recent fraud rate
        
        Args:
            window: Number of recent transactions to consider
            
        Returns:
            Fraud rate (0-1)
        """
        if len(self.fraud_history) == 0:
            return 0.01  # Default 1% fraud rate
        
        recent = self.fraud_history[-window:]
        return sum(recent) / len(recent)
    
    def get_threshold_explanation(self, transaction, anomaly_score):
        """
        Get detailed explanation of threshold calculation
        
        Args:
            transaction: Transaction details
            anomaly_score: Anomaly score
            
        Returns:
            Dictionary with threshold breakdown
        """
        base = self.base_threshold
        adjustments = []
        current = base
        
        # Track each adjustment
        if 'type' in transaction:
            txn_type = transaction['type']
            multiplier = self.type_multipliers.get(txn_type, 1.0)
            if multiplier != 1.0:
                current *= multiplier
                adjustments.append({
                    'factor': 'Transaction Type',
                    'value': txn_type,
                    'multiplier': multiplier,
                    'impact': (multiplier - 1) * 100
                })
        
        if 'is_night' in transaction and transaction['is_night']:
            current *= 0.9
            adjustments.append({
                'factor': 'Night Transaction',
                'value': True,
                'multiplier': 0.9,
                'impact': -10
            })
        
        if 'amount' in transaction:
            amount = transaction['amount']
            if amount > 100000:
                current *= 0.85
                adjustments.append({
                    'factor': 'Large Amount',
                    'value': f'${amount:,.2f}',
                    'multiplier': 0.85,
                    'impact': -15
                })
        
        recent_fraud_rate = self._get_recent_fraud_rate()
        if recent_fraud_rate > 0.05:
            current *= 0.9
            adjustments.append({
                'factor': 'High Recent Fraud Rate',
                'value': f'{recent_fraud_rate*100:.1f}%',
                'multiplier': 0.9,
                'impact': -10
            })
        
        final_threshold = np.clip(current, 0.3, 0.8)
        
        return {
            'base_threshold': base,
            'adjustments': adjustments,
            'final_threshold': final_threshold,
            'anomaly_score': anomaly_score,
            'is_fraud': anomaly_score > final_threshold,
            'margin': anomaly_score - final_threshold
        }
    
    def get_statistics(self):
        """Get threshold statistics"""
        return {
            'base_threshold': self.base_threshold,
            'recent_fraud_rate': self._get_recent_fraud_rate(),
            'total_transactions': len(self.fraud_history),
            'type_multipliers': self.type_multipliers
        }


class AdaptiveThresholdOptimizer:
    """
    Optimize thresholds based on historical performance
    Uses precision-recall trade-off to find optimal thresholds
    """
    
    def __init__(self):
        self.optimal_thresholds = {}
        
    def optimize(self, y_true, y_scores, transaction_types):
        """
        Find optimal thresholds for each transaction type
        
        Args:
            y_true: True labels (0/1)
            y_scores: Predicted anomaly scores
            transaction_types: Transaction types for each sample
            
        Returns:
            Dictionary of optimal thresholds per type
        """
        unique_types = set(transaction_types)
        
        for txn_type in unique_types:
            # Filter data for this type
            mask = transaction_types == txn_type
            type_true = y_true[mask]
            type_scores = y_scores[mask]
            
            if len(type_true) == 0:
                continue
            
            # Find threshold that maximizes F1 score
            best_f1 = 0
            best_threshold = 0.5
            
            for threshold in np.arange(0.1, 0.9, 0.05):
                predictions = (type_scores > threshold).astype(int)
                
                # Calculate F1 score
                tp = np.sum((predictions == 1) & (type_true == 1))
                fp = np.sum((predictions == 1) & (type_true == 0))
                fn = np.sum((predictions == 0) & (type_true == 1))
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                if f1 > best_f1:
                    best_f1 = f1
                    best_threshold = threshold
            
            self.optimal_thresholds[txn_type] = {
                'threshold': best_threshold,
                'f1_score': best_f1
            }
        
        return self.optimal_thresholds
    
    def get_threshold(self, transaction_type):
        """Get optimal threshold for a transaction type"""
        if transaction_type in self.optimal_thresholds:
            return self.optimal_thresholds[transaction_type]['threshold']
        return 0.5  # Default


# Example usage
if __name__ == "__main__":
    # Test dynamic thresholding
    dt = DynamicThreshold()
    
    # Test transaction 1: Normal payment during day
    txn1 = {
        'type': 'PAYMENT',
        'amount': 500,
        'hour': 14,
        'is_night': False,
        'is_unusual_amount': False
    }
    
    score1 = 0.45
    threshold1 = dt.calculate_threshold(txn1, score1)
    print(f"Transaction 1 - Score: {score1}, Threshold: {threshold1:.3f}, Fraud: {dt.is_fraud(txn1, score1)}")
    
    # Test transaction 2: Large cash out at night
    txn2 = {
        'type': 'CASH_OUT',
        'amount': 150000,
        'hour': 2,
        'is_night': True,
        'is_unusual_amount': True,
        'velocity_spike': 5
    }
    
    score2 = 0.55
    threshold2 = dt.calculate_threshold(txn2, score2)
    print(f"Transaction 2 - Score: {score2}, Threshold: {threshold2:.3f}, Fraud: {dt.is_fraud(txn2, score2)}")
    
    # Get explanation
    explanation = dt.get_threshold_explanation(txn2, score2)
    print("\nThreshold Explanation:")
    print(f"Base: {explanation['base_threshold']}")
    print(f"Adjustments: {explanation['adjustments']}")
    print(f"Final: {explanation['final_threshold']:.3f}")
    print(f"Decision: {'FRAUD' if explanation['is_fraud'] else 'NORMAL'}")
