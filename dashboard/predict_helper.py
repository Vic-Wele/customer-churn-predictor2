import pandas as pd
import numpy as np
import joblib
import psycopg2
import argparse
import sys
import os
from datetime import datetime

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

class ChurnPredictor:
    """Churn prediction model wrapper"""
    
    def __init__(self, model_path='data/models/logistic_regression_model.pkl',
                 scaler_path='data/models/scaler.pkl',
                 feature_names_path='data/models/feature_names.pkl'):
        """Load model and artifacts"""
        print("📦 Loading model artifacts...")
        
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_names = joblib.load(feature_names_path)
            print(f"✓ Model loaded: {model_path}")
            print(f"✓ Scaler loaded: {scaler_path}")
            print(f"✓ Features loaded: {len(self.feature_names)} features")
        except Exception as e:
            print(f"✗ Error loading model artifacts: {e}")
            sys.exit(1)
    
    def get_customer_data(self, customer_id):
        """Fetch customer data from PostgreSQL"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM customers WHERE customer_id = %s
            """
            cursor.execute(query, (customer_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                conn.close()
                return None
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            cursor.close()
            conn.close()
            
            # Create dictionary
            customer_dict = dict(zip(columns, result))
            return customer_dict
            
        except Exception as e:
            print(f"✗ Error fetching customer data: {e}")
            return None
    
    def preprocess_customer(self, customer_dict):
        """Preprocess single customer data to match training format"""
        # Create dataframe from customer
        df = pd.DataFrame([customer_dict])
        
        # Basic preprocessing (same as process.py)
        df['total_charges'] = pd.to_numeric(df['total_charges'], errors='coerce')
        df['total_charges'].fillna(df['monthly_charges'], inplace=True)
        df['senior_citizen'] = df['senior_citizen'].astype(int)
        
        # Engineer features
        df['tenure_group'] = pd.cut(df['tenure'], 
                                     bins=[0, 12, 24, 48, 72],
                                     labels=['0-1yr', '1-2yr', '2-4yr', '4yr+'])
        
        service_cols = ['phone_service', 'multiple_lines', 'internet_service',
                        'online_security', 'online_backup', 'device_protection',
                        'tech_support', 'streaming_tv', 'streaming_movies']
        
        df['total_services'] = 0
        for col in service_cols:
            if col in df.columns:
                df['total_services'] += (df[col] == 'Yes').astype(int)
        
        df['charges_category'] = pd.cut(df['monthly_charges'],
                                         bins=[0, 30, 60, 90, 150],
                                         labels=['Low', 'Medium', 'High', 'Very High'])
        
        contract_risk = {'Month-to-month': 1.0, 'One year': 0.5, 'Two year': 0.2}
        df['contract_risk'] = df['contract'].map(contract_risk)
        
        payment_risk = {'Electronic check': 1.0, 'Mailed check': 0.7,
                       'Bank transfer (automatic)': 0.3, 'Credit card (automatic)': 0.3}
        df['payment_risk'] = df['payment_method'].map(payment_risk)
        
        df['avg_monthly_revenue'] = df['total_charges'] / (df['tenure'] + 1)
        df['has_family'] = ((df['partner'] == 'Yes') | (df['dependents'] == 'Yes')).astype(int)
        df['has_internet'] = (df['internet_service'] != 'No').astype(int)
        
        # Add missing features (from Cassandra) - set to 0 for single prediction
        df['total_events'] = 0
        df['payment_fail_rate'] = 0
        df['support_frequency'] = 0
        df['total_tickets'] = 0
        df['sentiment_score'] = 0
        
        # Encode categorical
        binary_cols = ['gender', 'partner', 'dependents', 'phone_service', 'paperless_billing']
        for col in binary_cols:
            if col in df.columns:
                df[col] = (df[col] == 'Yes').astype(int)
        
        categorical_cols = ['multiple_lines', 'internet_service', 'online_security',
                           'online_backup', 'device_protection', 'tech_support',
                           'streaming_tv', 'streaming_movies', 'contract', 
                           'payment_method', 'tenure_group', 'charges_category']
        
        df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
        
        # Align with training features
        for col in self.feature_names:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
        
        # Select only training features in correct order
        X = df_encoded[self.feature_names]
        
        return X
    
    def predict(self, customer_id):
        """Make prediction for a customer"""
        print(f"\n🔮 Making prediction for customer: {customer_id}")
        print("=" * 60)
        
        # Get customer data
        customer_dict = self.get_customer_data(customer_id)
        if customer_dict is None:
            print(f"✗ Customer {customer_id} not found in database")
            return None
        
        print(f"✓ Customer data retrieved")
        
        # Preprocess
        X = self.preprocess_customer(customer_dict)
        print(f"✓ Data preprocessed ({X.shape[1]} features)")
        
        # Scale
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0]
        
        # Results
        churn_prob = probability[1]
        risk_level = 'HIGH' if churn_prob > 0.7 else 'MEDIUM' if churn_prob > 0.4 else 'LOW'
        
        print("\n" + "=" * 60)
        print("📊 PREDICTION RESULTS")
        print("=" * 60)
        print(f"Customer ID: {customer_id}")
        print(f"Churn Prediction: {'WILL CHURN' if prediction == 1 else 'WILL NOT CHURN'}")
        print(f"Churn Probability: {churn_prob:.1%}")
        print(f"Risk Level: {risk_level}")
        print("=" * 60)
        
        # Customer details
        print(f"\n📋 Customer Profile:")
        print(f"   Tenure: {customer_dict.get('tenure')} months")
        print(f"   Contract: {customer_dict.get('contract')}")
        print(f"   Monthly Charges: ${customer_dict.get('monthly_charges')}")
        print(f"   Payment Method: {customer_dict.get('payment_method')}")
        
        return {
            'customer_id': customer_id,
            'prediction': int(prediction),
            'churn_probability': float(churn_prob),
            'risk_level': risk_level,
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_batch(self, customer_ids):
        """Make predictions for multiple customers"""
        results = []
        for customer_id in customer_ids:
            result = self.predict(customer_id)
            if result:
                results.append(result)
        return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Churn Prediction Service')
    parser.add_argument('--customer', type=str, help='Single customer ID to predict')
    parser.add_argument('--batch', type=str, nargs='+', help='Multiple customer IDs')
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = ChurnPredictor()
    
    if args.customer:
        predictor.predict(args.customer)
    elif args.batch:
        print(f"\n📦 Batch prediction for {len(args.batch)} customers")
        results = predictor.predict_batch(args.batch)
        print(f"\n✓ Completed {len(results)} predictions")
    else:
        print("Usage: python predict_helper.py --customer CUSTOMER_ID")
