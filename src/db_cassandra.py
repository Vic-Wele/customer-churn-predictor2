from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import sys
import time

CASSANDRA_CONFIG = {
    'contact_points': ['localhost'],
    'port': 9042
}

def get_session(keyspace=None):
    """Create Cassandra session"""
    try:
        cluster = Cluster(**CASSANDRA_CONFIG)
        if keyspace:
            session = cluster.connect(keyspace)
        else:
            session = cluster.connect()
        return cluster, session
    except Exception as e:
        print(f"Error connecting to Cassandra: {e}")
        print("Tip: Make sure Cassandra container is fully started (may take 60-90 seconds)")
        sys.exit(1)

def init_keyspace():
    """Initialize Cassandra keyspace and tables"""
    cluster, session = get_session()
    
    # Create keyspace
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS churn_keyspace
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
    """)
    
    print("✓ Keyspace 'churn_keyspace' created")
    
    # Switch to keyspace
    session.set_keyspace('churn_keyspace')
    
    # Drop tables if they exist
    session.execute("DROP TABLE IF EXISTS customer_events;")
    session.execute("DROP TABLE IF EXISTS support_tickets;")
    
    # Create customer_events table (time-series data)
    session.execute("""
        CREATE TABLE customer_events (
            customer_id text,
            event_time timestamp,
            event_type text,
            event_data text,
            PRIMARY KEY (customer_id, event_time)
        ) WITH CLUSTERING ORDER BY (event_time DESC);
    """)
    
    print("✓ Table 'customer_events' created")
    
    # Create support_tickets table (unstructured data)
    session.execute("""
        CREATE TABLE support_tickets (
            ticket_id uuid PRIMARY KEY,
            customer_id text,
            created_at timestamp,
            ticket_type text,
            description text,
            sentiment text,
            status text
        );
    """)
    
    print("✓ Table 'support_tickets' created")
    print("✓ Cassandra schema initialized successfully!")
    
    cluster.shutdown()

def test_connection():
    """Test Cassandra connection"""
    try:
        cluster, session = get_session()
        
        # Get cluster info
        result = session.execute("SELECT release_version FROM system.local")
        version = result.one()
        
        print(f"✓ Connected to Cassandra")
        print(f"  Version: {version.release_version}")
        
        cluster.shutdown()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if Cassandra is running: docker compose ps")
        print("2. Cassandra takes 60-90 seconds to fully start")
        print("3. Check logs: docker compose logs cassandra")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cassandra Database Manager')
    parser.add_argument('--init', action='store_true', help='Initialize keyspace and tables')
    parser.add_argument('--test', action='store_true', help='Test Cassandra connection')
    
    args = parser.parse_args()
    
    if args.init:
        init_keyspace()
    elif args.test:
        test_connection()
    else:
        print("Usage: python src/db_cassandra.py --init  (to initialize schema)")
        print("       python src/db_cassandra.py --test  (to test connection)")
