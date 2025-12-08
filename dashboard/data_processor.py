"""
Data Processing Module for Dashboard
Handles uploaded data processing, model training, and insights generation
"""
import pandas as pd
import numpy as np
import joblib
import os
import sys
import tempfile
import subprocess
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix
)
from imblearn.over_sampling import SMOTE
import psycopg2

# Add parent directory to path
sys.path.insert(0, os.path.abspath('..'))

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

def validate_uploaded_data(df):
    """Validate uploaded CSV file has required columns"""
    required_columns = [
        'customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents',
        'tenure', 'PhoneService', 'MultipleLines', 'InternetService',
        'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
        'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
        'PaperlessBilling', 'PaymentMethod', 'MonthlyCharges',
        'TotalCharges', 'Churn'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}"
    
    if len(df) == 0:
        return False, "Uploaded file is empty"
    
    return True, "Data validated successfully"

def process_uploaded_data(df, use_spark=False):
    """Process uploaded data using Pandas or Spark"""
    if use_spark:
        return process_with_spark(df)
    else:
        return process_with_pandas(df)

def process_with_pandas(df):
    """Process data using Pandas (faster for smaller datasets)"""
    print("📊 Processing data with Pandas...")
    
    # Rename columns to match database schema (only if they exist)
    column_mapping = {
        'customerID': 'customer_id',
        'SeniorCitizen': 'senior_citizen',
        'PhoneService': 'phone_service',
        'MultipleLines': 'multiple_lines',
        'InternetService': 'internet_service',
        'OnlineSecurity': 'online_security',
        'OnlineBackup': 'online_backup',
        'DeviceProtection': 'device_protection',
        'TechSupport': 'tech_support',
        'StreamingTV': 'streaming_tv',
        'StreamingMovies': 'streaming_movies',
        'PaperlessBilling': 'paperless_billing',
        'PaymentMethod': 'payment_method',
        'MonthlyCharges': 'monthly_charges',
        'TotalCharges': 'total_charges'
    }
    
    # Only rename columns that exist
    existing_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mapping)
    
    # Clean data
    if 'total_charges' in df.columns:
        df['total_charges'] = pd.to_numeric(df['total_charges'], errors='coerce')
        if 'monthly_charges' in df.columns:
            df['total_charges'].fillna(df['monthly_charges'], inplace=True)
    
    if 'senior_citizen' in df.columns:
        df['senior_citizen'] = pd.to_numeric(df['senior_citizen'], errors='coerce').fillna(0).astype(int)
    
    # Drop rows with missing critical data
    critical_cols = ['customer_id', 'tenure', 'monthly_charges']
    critical_cols = [c for c in critical_cols if c in df.columns]
    df = df.dropna(subset=critical_cols)
    
    # Feature engineering
    if 'tenure' in df.columns:
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
    
    if 'monthly_charges' in df.columns:
        df['charges_category'] = pd.cut(df['monthly_charges'],
                                         bins=[0, 30, 60, 90, 150],
                                         labels=['Low', 'Medium', 'High', 'Very High'])
    
    if 'contract' in df.columns:
        contract_risk = {'Month-to-month': 1.0, 'One year': 0.5, 'Two year': 0.2}
        df['contract_risk'] = df['contract'].map(contract_risk).fillna(0.5)
    
    if 'payment_method' in df.columns:
        payment_risk = {
            'Electronic check': 1.0,
            'Mailed check': 0.7,
            'Bank transfer (automatic)': 0.3,
            'Credit card (automatic)': 0.3
        }
        df['payment_risk'] = df['payment_method'].map(payment_risk).fillna(0.5)
    
    if 'total_charges' in df.columns and 'tenure' in df.columns:
        df['avg_monthly_revenue'] = df['total_charges'] / (df['tenure'] + 1)
    else:
        df['avg_monthly_revenue'] = 0
    
    if 'partner' in df.columns and 'dependents' in df.columns:
        df['has_family'] = ((df['partner'] == 'Yes') | (df['dependents'] == 'Yes')).astype(int)
    else:
        df['has_family'] = 0
    
    if 'internet_service' in df.columns:
        df['has_internet'] = (df['internet_service'] != 'No').astype(int)
    else:
        df['has_internet'] = 0
    
    # Add placeholder event features
    df['total_events'] = 0
    df['payment_fail_rate'] = 0
    df['support_frequency'] = 0
    df['total_tickets'] = 0
    df['sentiment_score'] = 0
    
    # Encode categorical
    binary_cols = ['gender', 'partner', 'dependents', 'phone_service', 'paperless_billing']
    for col in binary_cols:
        df[col] = (df[col] == 'Yes').astype(int)
    
    categorical_cols = ['multiple_lines', 'internet_service', 'online_security',
                       'online_backup', 'device_protection', 'tech_support',
                       'streaming_tv', 'streaming_movies', 'contract',
                       'payment_method', 'tenure_group', 'charges_category']
    
    df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    
    print(f"✓ Processed {len(df_encoded):,} records with {len(df_encoded.columns)} features")
    return df_encoded

def process_with_spark(df):
    """Process data using Spark (for larger datasets)"""
    print("🚀 Processing data with Spark...")
    
    # Save to temporary CSV
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    try:
        # Call Spark processing script
        result = subprocess.run(
            ['python', '../src/process_spark.py', '--run'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            # Load processed data
            processed_df = pd.read_csv('data/processed/processed_churn_data.csv')
            print(f"✓ Processed {len(processed_df):,} records with Spark")
            return processed_df
        else:
            print(f"⚠ Spark processing failed: {result.stderr}")
            print("   Falling back to Pandas processing...")
            return process_with_pandas(df)
    except Exception as e:
        print(f"⚠ Spark processing error: {e}")
        print("   Falling back to Pandas processing...")
        return process_with_pandas(df)
    finally:
        # Clean up temp file
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def train_models_on_data(df_processed, save_models=True):
    """Train ML models on processed data"""
    print("🎯 Training ML models...")
    
    # Prepare features and target
    feature_cols = [c for c in df_processed.columns if c not in ['customer_id', 'churn', 'tenure_group']]
    X = df_processed[feature_cols]
    
    # Handle churn target (both 'Yes'/'No' and 0/1 encoding)
    if 'churn' in df_processed.columns:
        if df_processed['churn'].dtype == 'object':
            y = (df_processed['churn'] == 'Yes').astype(int)
        else:
            y = df_processed['churn'].astype(int)
    else:
        raise ValueError("Churn column not found in processed data")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Handle class imbalance
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_balanced)
    X_test_scaled = scaler.transform(X_test)
    
    # Train models
    models = {
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"   Training {name}...")
        model.fit(X_train_scaled, y_train_balanced)
        
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        results[name] = {
            'model': model,
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'confusion_matrix': confusion_matrix(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred)
        }
    
    # Save best model
    if save_models:
        best_model_name = max(results.keys(), key=lambda k: results[k]['roc_auc'])
        best_model = results[best_model_name]['model']
        
        models_dir = '../data/models'
        os.makedirs(models_dir, exist_ok=True)
        
        # Save with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{models_dir}/model_{timestamp}.pkl"
        scaler_path = f"{models_dir}/scaler_{timestamp}.pkl"
        feature_names_path = f"{models_dir}/feature_names_{timestamp}.pkl"
        
        joblib.dump(best_model, model_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(feature_cols, feature_names_path)
        
        # Also save as latest
        joblib.dump(best_model, f"{models_dir}/logistic_regression_model.pkl")
        joblib.dump(scaler, f"{models_dir}/scaler.pkl")
        joblib.dump(feature_cols, f"{models_dir}/feature_names.pkl")
        
        print(f"✓ Models saved to {models_dir}")
    
    return results, feature_cols

def generate_insights(df_processed, model_results):
    """Generate insights from processed data and model results"""
    print("💡 Generating insights...")
    
    insights = {
        'data_summary': {},
        'churn_analysis': {},
        'model_performance': {},
        'key_findings': []
    }
    
    # Data summary
    total_customers = len(df_processed)
    if 'churn' in df_processed.columns:
        # Handle both 'Yes'/'No' and 0/1 encoding
        if df_processed['churn'].dtype == 'object':
            churned = (df_processed['churn'] == 'Yes').sum()
        else:
            churned = (df_processed['churn'] == 1).sum()
    else:
        churned = 0
    churn_rate = churned / total_customers if total_customers > 0 else 0
    
    insights['data_summary'] = {
        'total_customers': total_customers,
        'churned': churned,
        'retained': total_customers - churned,
        'churn_rate': churn_rate
    }
    
    # Churn analysis
    if 'contract' in df_processed.columns and 'churn' in df_processed.columns:
        def calc_churn_rate(x):
            if len(x) == 0:
                return 0
            if x.dtype == 'object':
                return (x == 'Yes').sum() / len(x)
            else:
                return (x == 1).sum() / len(x)
        
        churn_by_contract = df_processed.groupby('contract')['churn'].apply(calc_churn_rate).to_dict()
        insights['churn_analysis']['by_contract'] = churn_by_contract
    
    if 'tenure' in df_processed.columns and 'churn' in df_processed.columns:
        if 'tenure_group' not in df_processed.columns:
            df_processed['tenure_group'] = pd.cut(
                df_processed['tenure'],
                bins=[0, 12, 24, 48, 72],
                labels=['0-1yr', '1-2yr', '2-4yr', '4yr+']
            )
        
        def calc_churn_rate(x):
            if len(x) == 0:
                return 0
            if x.dtype == 'object':
                return (x == 'Yes').sum() / len(x)
            else:
                return (x == 1).sum() / len(x)
        
        churn_by_tenure = df_processed.groupby('tenure_group')['churn'].apply(calc_churn_rate).to_dict()
        insights['churn_analysis']['by_tenure'] = churn_by_tenure
    
    # Model performance
    best_model = max(model_results.keys(), key=lambda k: model_results[k]['roc_auc'])
    insights['model_performance'] = {
        'best_model': best_model,
        'accuracy': model_results[best_model]['accuracy'],
        'roc_auc': model_results[best_model]['roc_auc'],
        'precision': model_results[best_model]['precision'],
        'recall': model_results[best_model]['recall']
    }
    
    # Key findings
    if churn_rate > 0.25:
        insights['key_findings'].append("⚠️ High churn rate detected (>25%) - Immediate action required")
    elif churn_rate > 0.15:
        insights['key_findings'].append("⚠️ Moderate churn rate (15-25%) - Proactive measures recommended")
    else:
        insights['key_findings'].append("✅ Low churn rate (<15%) - Customer base is stable")
    
    if insights['model_performance']['roc_auc'] > 0.8:
        insights['key_findings'].append("✅ Excellent model performance (ROC-AUC > 0.8)")
    elif insights['model_performance']['roc_auc'] > 0.7:
        insights['key_findings'].append("✓ Good model performance (ROC-AUC > 0.7)")
    else:
        insights['key_findings'].append("⚠️ Model performance could be improved (ROC-AUC < 0.7)")
    
    if 'by_contract' in insights['churn_analysis']:
        max_contract = max(insights['churn_analysis']['by_contract'].items(), key=lambda x: x[1])
        insights['key_findings'].append(
            f"📊 Highest churn in {max_contract[0]} contracts ({max_contract[1]:.1%})"
        )
    
    print("✓ Insights generated")
    return insights

def save_to_database(df_processed):
    """Save processed data to PostgreSQL"""
    print("💾 Saving to database...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Map columns back to database schema
        for _, row in df_processed.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO customers (
                        customer_id, gender, senior_citizen, partner, dependents,
                        tenure, phone_service, multiple_lines, internet_service,
                        online_security, online_backup, device_protection,
                        tech_support, streaming_tv, streaming_movies, contract,
                        paperless_billing, payment_method, monthly_charges,
                        total_charges, churn
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO UPDATE SET
                        churn = EXCLUDED.churn,
                        monthly_charges = EXCLUDED.monthly_charges,
                        total_charges = EXCLUDED.total_charges
                """, (
                    row.get('customer_id'),
                    'Yes' if row.get('gender') == 1 else 'No',
                    int(row.get('senior_citizen', 0)),
                    'Yes' if row.get('partner') == 1 else 'No',
                    'Yes' if row.get('dependents') == 1 else 'No',
                    int(row.get('tenure', 0)),
                    'Yes' if row.get('phone_service') == 1 else 'No',
                    row.get('multiple_lines', 'No'),
                    row.get('internet_service', 'No'),
                    row.get('online_security', 'No'),
                    row.get('online_backup', 'No'),
                    row.get('device_protection', 'No'),
                    row.get('tech_support', 'No'),
                    row.get('streaming_tv', 'No'),
                    row.get('streaming_movies', 'No'),
                    row.get('contract', 'Month-to-month'),
                    'Yes' if row.get('paperless_billing') == 1 else 'No',
                    row.get('payment_method', 'Electronic check'),
                    float(row.get('monthly_charges', 0)),
                    float(row.get('total_charges', 0)),
                    'Yes' if row.get('churn') == 1 else 'No'
                ))
            except Exception as e:
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Saved {len(df_processed)} records to database")
        return True
    except Exception as e:
        print(f"✗ Error saving to database: {e}")
        return False

