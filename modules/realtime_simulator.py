"""
Real-time Transaction Simulator
Simulates live transaction streams for testing and performance analysis
"""

import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
import random
from threading import Thread
import queue


class TransactionGenerator:
    """
    Generates realistic transaction patterns
    Includes both normal and fraudulent transactions
    """
    
    def __init__(self, fraud_rate=0.05):
        """
        Initialize transaction generator
        
        Args:
            fraud_rate: Percentage of fraudulent transactions (default 5%)
        """
        self.fraud_rate = fraud_rate
        self.transaction_id = 0
        self.user_profiles = self._create_user_profiles(100)
        
        # Transaction type probabilities
        self.txn_types = ['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT', 'CASH_IN']
        self.txn_type_probs = [0.4, 0.25, 0.2, 0.1, 0.05]
        
    def _create_user_profiles(self, n_users):
        """Create realistic user profiles"""
        profiles = {}
        
        for i in range(n_users):
            user_id = f'C{1000000 + i}'
            profiles[user_id] = {
                'avg_amount': np.random.lognormal(8, 1.5),  # Average transaction amount
                'std_amount': np.random.lognormal(7, 1),
                'txn_frequency': np.random.uniform(1, 10),  # Transactions per day
                'preferred_hours': np.random.choice(['day', 'night', 'mixed']),
                'balance': np.random.uniform(10000, 500000)
            }
        
        return profiles
    
    def generate_normal_transaction(self):
        """Generate a normal (legitimate) transaction"""
        # Select random user
        user_id = random.choice(list(self.user_profiles.keys()))
        profile = self.user_profiles[user_id]
        
        # Generate transaction details
        txn_type = np.random.choice(self.txn_types, p=self.txn_type_probs)
        
        # Amount based on user profile
        amount = max(10, np.random.normal(profile['avg_amount'], profile['std_amount']))
        
        # Time based on user preference
        if profile['preferred_hours'] == 'day':
            hour = np.random.randint(9, 18)
        elif profile['preferred_hours'] == 'night':
            hour = np.random.randint(20, 24)
        else:
            hour = np.random.randint(0, 24)
        
        # Current step (time)
        current_time = datetime.now()
        step = current_time.hour + (current_time.day * 24)
        
        # Balance calculations
        old_balance = profile['balance']
        if txn_type in ['PAYMENT', 'TRANSFER', 'CASH_OUT', 'DEBIT']:
            new_balance = max(0, old_balance - amount)
        else:  # CASH_IN
            new_balance = old_balance + amount
        
        # Update profile balance
        profile['balance'] = new_balance
        
        # Create transaction
        transaction = {
            'transaction_id': f'TXN-{self.transaction_id:08d}',
            'step': step,
            'type': txn_type,
            'amount': round(amount, 2),
            'nameOrig': user_id,
            'oldbalanceOrg': round(old_balance, 2),
            'newbalanceOrig': round(new_balance, 2),
            'nameDest': f'M{random.randint(1000000, 9999999)}',
            'oldbalanceDest': 0,
            'newbalanceDest': 0,
            'isFraud': 0,
            'timestamp': current_time.isoformat()
        }
        
        self.transaction_id += 1
        return transaction
    
    def generate_fraudulent_transaction(self):
        """Generate a fraudulent transaction"""
        # Select random user
        user_id = random.choice(list(self.user_profiles.keys()))
        profile = self.user_profiles[user_id]
        
        # Fraud characteristics
        fraud_patterns = [
            'large_amount',
            'night_transaction',
            'rapid_succession',
            'balance_mismatch',
            'unusual_type'
        ]
        
        fraud_type = random.choice(fraud_patterns)
        
        # Generate based on fraud pattern
        if fraud_type == 'large_amount':
            amount = np.random.uniform(50000, 200000)
            hour = np.random.randint(0, 24)
            txn_type = 'CASH_OUT'
            
        elif fraud_type == 'night_transaction':
            amount = np.random.uniform(20000, 100000)
            hour = np.random.randint(2, 6)  # 2 AM - 6 AM
            txn_type = random.choice(['CASH_OUT', 'TRANSFER'])
            
        elif fraud_type == 'rapid_succession':
            amount = np.random.uniform(10000, 50000)
            hour = np.random.randint(0, 24)
            txn_type = random.choice(['TRANSFER', 'CASH_OUT'])
            
        elif fraud_type == 'balance_mismatch':
            amount = np.random.uniform(30000, 150000)
            hour = np.random.randint(0, 24)
            txn_type = 'TRANSFER'
            
        else:  # unusual_type
            amount = np.random.uniform(40000, 120000)
            hour = np.random.randint(0, 24)
            txn_type = 'CASH_OUT'
        
        # Current step
        current_time = datetime.now()
        step = hour + (current_time.day * 24)
        
        # Balance (often mismatched in fraud)
        old_balance = profile['balance']
        
        # Intentional balance mismatch for fraud
        if fraud_type == 'balance_mismatch':
            new_balance = old_balance - amount + np.random.uniform(-5000, 5000)
        else:
            new_balance = max(0, old_balance - amount)
        
        # Create transaction
        transaction = {
            'transaction_id': f'TXN-{self.transaction_id:08d}',
            'step': step,
            'type': txn_type,
            'amount': round(amount, 2),
            'nameOrig': user_id,
            'oldbalanceOrg': round(old_balance, 2),
            'newbalanceOrig': round(new_balance, 2),
            'nameDest': f'M{random.randint(1000000, 9999999)}',
            'oldbalanceDest': 0,
            'newbalanceDest': 0,
            'isFraud': 1,
            'timestamp': current_time.isoformat(),
            'fraud_pattern': fraud_type
        }
        
        self.transaction_id += 1
        return transaction
    
    def generate_transaction(self):
        """Generate a transaction (normal or fraudulent based on fraud_rate)"""
        if random.random() < self.fraud_rate:
            return self.generate_fraudulent_transaction()
        else:
            return self.generate_normal_transaction()
    
    def generate_batch(self, n_transactions):
        """Generate a batch of transactions"""
        transactions = []
        for _ in range(n_transactions):
            transactions.append(self.generate_transaction())
        return pd.DataFrame(transactions)


class RealtimeSimulator:
    """
    Simulates real-time transaction stream
    Measures system performance and detection accuracy
    """
    
    def __init__(self, detector=None, fraud_rate=0.05):
        """
        Initialize simulator
        
        Args:
            detector: Fraud detection system
            fraud_rate: Fraud rate in simulation
        """
        self.generator = TransactionGenerator(fraud_rate)
        self.detector = detector
        self.metrics = {
            'total_transactions': 0,
            'total_fraud': 0,
            'detected_fraud': 0,
            'false_positives': 0,
            'true_positives': 0,
            'false_negatives': 0,
            'true_negatives': 0,
            'latencies': [],
            'throughput': []
        }
        self.transaction_queue = queue.Queue()
        self.is_running = False
        
    def simulate_stream(self, duration_seconds=60, rate_per_second=10):
        """
        Simulate transaction stream for specified duration
        
        Args:
            duration_seconds: How long to simulate
            rate_per_second: Transactions per second
        """
        print(f"Starting real-time simulation...")
        print(f"Duration: {duration_seconds}s, Rate: {rate_per_second} txn/sec")
        print("-" * 60)
        
        self.is_running = True
        start_time = time.time()
        
        transactions_generated = 0
        
        while time.time() - start_time < duration_seconds:
            batch_start = time.time()
            
            # Generate transactions for this second
            for _ in range(rate_per_second):
                txn = self.generator.generate_transaction()
                self.transaction_queue.put(txn)
                transactions_generated += 1
            
            # Process transactions
            self._process_batch()
            
            # Calculate throughput
            batch_time = time.time() - batch_start
            throughput = rate_per_second / batch_time if batch_time > 0 else 0
            self.metrics['throughput'].append(throughput)
            
            # Sleep to maintain rate
            sleep_time = max(0, 1 - batch_time)
            time.sleep(sleep_time)
            
            # Print progress every 10 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                self._print_progress(elapsed)
        
        self.is_running = False
        
        print("\n" + "=" * 60)
        print("Simulation Complete!")
        print("=" * 60)
        self._print_final_results()
        
    def _process_batch(self):
        """Process queued transactions"""
        while not self.transaction_queue.empty():
            txn = self.transaction_queue.get()
            self._process_transaction(txn)
    
    def _process_transaction(self, txn):
        """Process a single transaction"""
        start_time = time.time()
        
        # Update metrics
        self.metrics['total_transactions'] += 1
        is_actual_fraud = txn.get('isFraud', 0) == 1
        
        if is_actual_fraud:
            self.metrics['total_fraud'] += 1
        
        # Detect fraud (if detector available)
        if self.detector:
            # Here you would call your actual detector
            # For simulation, use simple rule-based detection
            is_detected_fraud = self._simple_detection(txn)
        else:
            is_detected_fraud = self._simple_detection(txn)
        
        # Update confusion matrix
        if is_actual_fraud and is_detected_fraud:
            self.metrics['true_positives'] += 1
            self.metrics['detected_fraud'] += 1
        elif is_actual_fraud and not is_detected_fraud:
            self.metrics['false_negatives'] += 1
        elif not is_actual_fraud and is_detected_fraud:
            self.metrics['false_positives'] += 1
        elif not is_actual_fraud and not is_detected_fraud:
            self.metrics['true_negatives'] += 1
        
        # Record latency
        latency = (time.time() - start_time) * 1000  # Convert to ms
        self.metrics['latencies'].append(latency)
    
    def _simple_detection(self, txn):
        """Simple rule-based fraud detection for simulation"""
        score = 0
        
        # Large amount
        if txn['amount'] > 50000:
            score += 30
        
        # Night transaction
        hour = txn['step'] % 24
        if hour >= 22 or hour <= 6:
            score += 20
        
        # Cash out
        if txn['type'] == 'CASH_OUT':
            score += 15
        
        # Balance mismatch
        expected_new_balance = txn['oldbalanceOrg'] - txn['amount']
        if abs(txn['newbalanceOrig'] - expected_new_balance) > 1000:
            score += 25
        
        return score > 50
    
    def _print_progress(self, elapsed):
        """Print simulation progress"""
        accuracy = self._calculate_accuracy()
        avg_latency = np.mean(self.metrics['latencies'][-100:]) if self.metrics['latencies'] else 0
        
        print(f"\n[{int(elapsed)}s] Processed: {self.metrics['total_transactions']} | "
              f"Accuracy: {accuracy:.1f}% | "
              f"Latency: {avg_latency:.1f}ms")
    
    def _print_final_results(self):
        """Print final simulation results"""
        # Calculate metrics
        accuracy = self._calculate_accuracy()
        precision = self._calculate_precision()
        recall = self._calculate_recall()
        f1_score = self._calculate_f1()
        
        avg_latency = np.mean(self.metrics['latencies'])
        p50_latency = np.percentile(self.metrics['latencies'], 50)
        p95_latency = np.percentile(self.metrics['latencies'], 95)
        p99_latency = np.percentile(self.metrics['latencies'], 99)
        
        avg_throughput = np.mean(self.metrics['throughput'])
        
        print(f"\nPerformance Metrics:")
        print(f"  Total Transactions: {self.metrics['total_transactions']}")
        print(f"  Actual Fraud: {self.metrics['total_fraud']} ({self.metrics['total_fraud']/self.metrics['total_transactions']*100:.1f}%)")
        print(f"  Detected Fraud: {self.metrics['detected_fraud']}")
        
        print(f"\nAccuracy Metrics:")
        print(f"  Accuracy: {accuracy:.2f}%")
        print(f"  Precision: {precision:.2f}%")
        print(f"  Recall: {recall:.2f}%")
        print(f"  F1-Score: {f1_score:.2f}%")
        
        print(f"\nConfusion Matrix:")
        print(f"  True Positives: {self.metrics['true_positives']}")
        print(f"  True Negatives: {self.metrics['true_negatives']}")
        print(f"  False Positives: {self.metrics['false_positives']}")
        print(f"  False Negatives: {self.metrics['false_negatives']}")
        
        print(f"\nLatency Metrics:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P50: {p50_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  P99: {p99_latency:.2f}ms")
        
        print(f"\nThroughput:")
        print(f"  Average: {avg_throughput:.0f} txn/sec")
        
    def _calculate_accuracy(self):
        """Calculate detection accuracy"""
        total = self.metrics['total_transactions']
        if total == 0:
            return 0
        
        correct = self.metrics['true_positives'] + self.metrics['true_negatives']
        return (correct / total) * 100
    
    def _calculate_precision(self):
        """Calculate precision"""
        tp = self.metrics['true_positives']
        fp = self.metrics['false_positives']
        
        if tp + fp == 0:
            return 0
        
        return (tp / (tp + fp)) * 100
    
    def _calculate_recall(self):
        """Calculate recall"""
        tp = self.metrics['true_positives']
        fn = self.metrics['false_negatives']
        
        if tp + fn == 0:
            return 0
        
        return (tp / (tp + fn)) * 100
    
    def _calculate_f1(self):
        """Calculate F1 score"""
        precision = self._calculate_precision()
        recall = self._calculate_recall()
        
        if precision + recall == 0:
            return 0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def get_metrics(self):
        """Get all metrics"""
        return {
            'accuracy': self._calculate_accuracy(),
            'precision': self._calculate_precision(),
            'recall': self._calculate_recall(),
            'f1_score': self._calculate_f1(),
            'avg_latency': np.mean(self.metrics['latencies']),
            'p95_latency': np.percentile(self.metrics['latencies'], 95),
            'throughput': np.mean(self.metrics['throughput']),
            'total_transactions': self.metrics['total_transactions'],
            'total_fraud': self.metrics['total_fraud']
        }


# Example usage
if __name__ == "__main__":
    # Test transaction generation
    print("Testing Transaction Generator...")
    generator = TransactionGenerator(fraud_rate=0.1)
    
    # Generate sample transactions
    print("\nNormal Transaction:")
    normal_txn = generator.generate_normal_transaction()
    for key, value in normal_txn.items():
        print(f"  {key}: {value}")
    
    print("\nFraudulent Transaction:")
    fraud_txn = generator.generate_fraudulent_transaction()
    for key, value in fraud_txn.items():
        print(f"  {key}: {value}")
    
    # Test real-time simulation
    print("\n" + "=" * 60)
    print("Testing Real-time Simulator...")
    print("=" * 60)
    
    simulator = RealtimeSimulator(fraud_rate=0.05)
    simulator.simulate_stream(duration_seconds=30, rate_per_second=50)
