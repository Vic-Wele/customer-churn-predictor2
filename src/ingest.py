import pandas as pd
import psycopg2
from cassandra.cluster import Cluster
import json
import sys
import argparse
from datetime import datetime
import uuid

# Database configs
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

CASSANDRA_CONFIG = {
    'contact_points': ['localhost'],
    'port': 9042
}

def ingest_batch_to_postgres(csv_file):
    """Load CSV data into PostgreSQL"""
    print(f"Loading data from {csv_file}...")
    
    # Read CSV
    df = pd.read_csv(csv_file)
    print(f"✓ Loaded {len(df)} rows from CSV")
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Insert data
    inserted = 0
    for _, row in df.iterrows():
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
                ON CONFLICT (customer_id) DO NOTHING
            """, (
                row['customerID'], row['gender'], row['SeniorCitizen'],
                row['Partner'], row['Dependents'], row['tenure'],
                row['PhoneService'], row['MultipleLines'], row['InternetService'],
                row['OnlineSecurity'], row['OnlineBackup'], row['DeviceProtection'],
                row['TechSupport'], row['StreamingTV'], row['StreamingMovies'],
                row['Contract'], row['PaperlessBilling'], row['PaymentMethod'],
                row['MonthlyCharges'], row['TotalCharges'], row['Churn']
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting row: {e}")
            continue
    
    conn.commit()
    print(f"✓ Inserted {inserted} customers into PostgreSQL")
    
    cursor.close()
    conn.close()

def ingest_sample_events_to_cassandra(num_events=100):
    """Generate and insert sample customer events into Cassandra"""
    print(f"Generating {num_events} sample events...")
    
    cluster = Cluster(**CASSANDRA_CONFIG)
    session = cluster.connect('churn_keyspace')
    
    # Sample event types
    event_types = ['login', 'payment_success', 'payment_failed', 'support_call', 
                   'feature_usage', 'service_upgrade', 'service_downgrade']
    
    # Get some customer IDs from PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id FROM customers LIMIT 50")
    customer_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    if not customer_ids:
        print("✗ No customers found in PostgreSQL. Run batch ingestion first.")
        return
    
    # Insert sample events
    import random
    from datetime import timedelta
    
    inserted = 0
    for i in range(num_events):
        customer_id = random.choice(customer_ids)
        event_type = random.choice(event_types)
        event_time = datetime.now() - timedelta(days=random.randint(0, 90))
        event_data = json.dumps({'detail': f'Sample {event_type} event'})
        
        session.execute("""
            INSERT INTO customer_events (customer_id, event_time, event_type, event_data)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, event_time, event_type, event_data))
        inserted += 1
    
    print(f"✓ Inserted {inserted} events into Cassandra")
    cluster.shutdown()

def ingest_sample_tickets_to_cassandra(num_tickets=50):
    """Generate and insert sample support tickets into Cassandra"""
    print(f"Generating {num_tickets} sample support tickets...")
    
    cluster = Cluster(**CASSANDRA_CONFIG)
    session = cluster.connect('churn_keyspace')
    
    # Sample ticket data
    ticket_types = ['billing_issue', 'technical_support', 'service_complaint', 'account_inquiry']
    sentiments = ['positive', 'neutral', 'negative']
    statuses = ['open', 'in_progress', 'resolved', 'closed']
    descriptions = [
        "Unable to access my account",
        "Billing charge incorrect",
        "Internet service very slow",
        "Need help setting up device",
        "Want to upgrade my plan"
    ]
    
    # Get customer IDs
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id FROM customers LIMIT 50")
    customer_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    if not customer_ids:
        print("✗ No customers found in PostgreSQL. Run batch ingestion first.")
        return
    
    import random
    from datetime import timedelta
    
    inserted = 0
    for i in range(num_tickets):
        ticket_id = uuid.uuid4()
        customer_id = random.choice(customer_ids)
        created_at = datetime.now() - timedelta(days=random.randint(0, 180))
        ticket_type = random.choice(ticket_types)
        description = random.choice(descriptions)
        sentiment = random.choice(sentiments)
        status = random.choice(statuses)
        
        session.execute("""
            INSERT INTO support_tickets (ticket_id, customer_id, created_at, ticket_type, description, sentiment, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (ticket_id, customer_id, created_at, ticket_type, description, sentiment, status))
        inserted += 1
    
    print(f"✓ Inserted {inserted} support tickets into Cassandra")
    cluster.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Data Ingestion Tool')
    parser.add_argument('--batch', type=str, help='Load CSV file into PostgreSQL')
    parser.add_argument('--events', type=int, default=100, help='Generate sample events in Cassandra')
    parser.add_argument('--tickets', type=int, default=50, help='Generate sample tickets in Cassandra')
    
    args = parser.parse_args()
    
    if args.batch:
        ingest_batch_to_postgres(args.batch)
    elif args.events:
        ingest_sample_events_to_cassandra(args.events)
    elif args.tickets:
        ingest_sample_tickets_to_cassandra(args.tickets)
    else:
        print("Usage examples:")
        print("  python src/ingest.py --batch data/raw/telco_churn.csv")
        print("  python src/ingest.py --events 100")
        print("  python src/ingest.py --tickets 50")
