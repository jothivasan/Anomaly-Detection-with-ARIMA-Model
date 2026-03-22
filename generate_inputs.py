
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from modules.realtime_simulator import TransactionGenerator

# Create Input directory if it doesn't exist
output_dir = "Input"
os.makedirs(output_dir, exist_ok=True)

class ScenarioGenerator(TransactionGenerator):
    def generate_specific_batch(self, scenario_name, n_rows=1000):
        data = []
        
        print(f"Generating Scenario: {scenario_name}")
        
        for i in range(n_rows):
            # Default logic
            is_fraud = False
            txn = None
            
            # 1. Baseline Normal (Low Fraud)
            if scenario_name == "01_Baseline_Normal":
                if random.random() < 0.01: # 1% fraud
                    txn = self.generate_fraudulent_transaction()
                else:
                    txn = self.generate_normal_transaction()

            # 2. High Fraud Wave (Aggressive)
            elif scenario_name == "02_High_Fraud_Wave":
                if random.random() < 0.25: # 25% fraud
                    txn = self.generate_fraudulent_transaction()
                else:
                    txn = self.generate_normal_transaction()

            # 3. Night Ops Attack (2 AM - 5 AM focus)
            elif scenario_name == "03_Night_Ops_Attack":
                if random.random() < 0.15:
                    txn = self.generate_fraudulent_transaction()
                    # Force time to be night
                    txn['step'] = random.randint(2, 5) + (random.randint(0, 30) * 24)
                    txn['fraud_pattern'] = 'night_transaction'
                else:
                    txn = self.generate_normal_transaction()

            # 4. Whale Theft (Massive Amounts)
            elif scenario_name == "04_Whale_Theft":
                if random.random() < 0.05:
                    txn = self.generate_fraudulent_transaction()
                    # Force massive amount
                    txn['amount'] = np.random.uniform(500000, 2000000)
                    txn['fraud_pattern'] = 'whale_theft'
                else:
                    txn = self.generate_normal_transaction()

            # 5. Velocity Swarm (Bot Attack)
            elif scenario_name == "05_Velocity_Swarm":
                if random.random() < 0.20:
                    txn = self.generate_fraudulent_transaction()
                    # Force rapid succession logic (simulated by step clustering)
                    base_step = random.randint(10, 20)
                    txn['step'] = base_step
                    txn['fraud_pattern'] = 'rapid_succession'
                else:
                    txn = self.generate_normal_transaction()
            
            # 6. Balance Drainer (Account Takeover)
            elif scenario_name == "06_Balance_Drainer":
                if random.random() < 0.10:
                    txn = self.generate_fraudulent_transaction()
                    # Force emptying account
                    txn['amount'] = txn['oldbalanceOrg'] 
                    txn['newbalanceOrig'] = 0
                    txn['fraud_pattern'] = 'balance_drain'
                else:
                    txn = self.generate_normal_transaction()

            # 7. Cashing Out (Laundering)
            elif scenario_name == "07_Cashing_Out":
                if random.random() < 0.15:
                    txn = self.generate_fraudulent_transaction()
                    txn['type'] = 'CASH_OUT'
                else:
                    txn = self.generate_normal_transaction()

            # 8. Weekend Spike
            elif scenario_name == "08_Weekend_Spike":
                # Simulated weekend steps (assuming step 1 is Monday 00:00)
                # Days 6 and 7, 13 and 14 etc are weekends
                if random.random() < 0.05:
                    txn = self.generate_fraudulent_transaction()
                else:
                    txn = self.generate_normal_transaction()
                
                # Force weekend timestamps for all
                day = random.choice([5, 6, 12, 13]) 
                txn['step'] = (day * 24) + random.randint(0, 23)

            # 9. Complex Hybrid (Mixed Vectors)
            elif scenario_name == "09_Complex_Hybrid":
                # Mix of everything
                if random.random() < 0.15:
                    txn = self.generate_fraudulent_transaction()
                else:
                    txn = self.generate_normal_transaction()

            # 10. Stealth Mode (Hard to detect)
            elif scenario_name == "10_Stealth_Mode":
                if random.random() < 0.10:
                    txn = self.generate_fraudulent_transaction()
                    # Make amount look normal (lower range)
                    txn['amount'] = np.random.uniform(100, 5000)
                    # Fix balance mismatch to be subtle
                    txn['newbalanceOrig'] = txn['oldbalanceOrg'] - txn['amount']
                    txn['fraud_pattern'] = 'stealth'
                else:
                    txn = self.generate_normal_transaction()
            
            data.append(txn)

        return pd.DataFrame(data)

# scenarios to generate
scenarios = [
    "01_Baseline_Normal",
    "02_High_Fraud_Wave",
    "03_Night_Ops_Attack",
    "04_Whale_Theft",
    "05_Velocity_Swarm",
    "06_Balance_Drainer",
    "07_Cashing_Out",
    "08_Weekend_Spike",
    "09_Complex_Hybrid",
    "10_Stealth_Mode"
]

gen = ScenarioGenerator()

for scenario in scenarios:
    df = gen.generate_specific_batch(scenario, n_rows=2000) # 2000 rows per file
    
    # Save as CSV
    filename = f"{scenario}.csv"
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False)
    print(f"Created {filepath} - {len(df)} transactions")

print("\nAll 10 test scenarios generated successfully in 'Input/' folder.")
