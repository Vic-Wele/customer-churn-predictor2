import psycopg2
from psycopg2 import sql
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

def get_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def init_schema():
    """Initialize database schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Drop table if exists
    cursor.execute("DROP TABLE IF EXISTS customers CASCADE;")
    
    # Create customers table
    create_table_query = """
    CREATE TABLE customers (
        customer_id VARCHAR(50) PRIMARY KEY,
        gender VARCHAR(10),
        senior_citizen INTEGER,
        partner VARCHAR(10),
        dependents VARCHAR(10),
        tenure INTEGER,
        phone_service VARCHAR(10),
        multiple_lines VARCHAR(20),
        internet_service VARCHAR(20),
        online_security VARCHAR(20),
        online_backup VARCHAR(20),
        device_protection VARCHAR(20),
        tech_support VARCHAR(20),
        streaming_tv VARCHAR(20),
        streaming_movies VARCHAR(20),
        contract VARCHAR(20),
        paperless_billing VARCHAR(10),
        payment_method VARCHAR(50),
        monthly_charges DECIMAL(10, 2),
        total_charges VARCHAR(20),
        churn VARCHAR(10),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    
    print("✓ PostgreSQL schema initialized successfully!")
    print("✓ Table 'customers' created")
    
    cursor.close()
    conn.close()

def test_connection():
    """Test database connection"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version[0][:50]}...")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='PostgreSQL Database Manager')
    parser.add_argument('--init', action='store_true', help='Initialize database schema')
    parser.add_argument('--test', action='store_true', help='Test database connection')
    
    args = parser.parse_args()
    
    if args.init:
        init_schema()
    elif args.test:
        test_connection()
    else:
        print("Usage: python src/db_postgres.py --init  (to initialize schema)")
        print("       python src/db_postgres.py --test  (to test connection)")
