import psycopg2
from cassandra.cluster import Cluster
from datetime import datetime

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

def verify_postgres():
    """Check PostgreSQL data"""
    print("=" * 60)
    print("POSTGRESQL - Structured Data")
    print("=" * 60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Count customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    print(f"✓ Total customers: {count:,}")
    
    # Count churned vs not churned
    cursor.execute("SELECT churn, COUNT(*) FROM customers GROUP BY churn")
    for row in cursor.fetchall():
        print(f"  - Churn={row[0]}: {row[1]:,} customers")
    
    # Sample customer
    cursor.execute("SELECT customer_id, gender, tenure, contract, monthly_charges, churn FROM customers LIMIT 1")
    sample = cursor.fetchone()
    print(f"\n📋 Sample Customer:")
    print(f"  ID: {sample[0]}")
    print(f"  Gender: {sample[1]}, Tenure: {sample[2]} months")
    print(f"  Contract: {sample[3]}, Monthly: ${sample[4]}")
    print(f"  Churned: {sample[5]}")
    
    cursor.close()
    conn.close()

def verify_cassandra():
    """Check Cassandra data"""
    print("\n" + "=" * 60)
    print("CASSANDRA - Time-Series & Unstructured Data")
    print("=" * 60)
    
    cluster = Cluster(**CASSANDRA_CONFIG)
    session = cluster.connect('churn_keyspace')
    
    # Count events
    result = session.execute("SELECT COUNT(*) FROM customer_events")
    event_count = result.one()[0]
    print(f"✓ Total customer events: {event_count:,}")
    
    # Sample events by type (manual aggregation)
    event_types = {}
    result = session.execute("SELECT event_type FROM customer_events")
    for row in result:
        event_types[row.event_type] = event_types.get(row.event_type, 0) + 1
    
    if event_types:
        print(f"\n📊 Event Types:")
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {event_type:20s}: {count:,} events")
    
    # Recent events
    result = session.execute("SELECT customer_id, event_time, event_type FROM customer_events LIMIT 5")
    print(f"\n🕐 Sample Events (5 random):")
    for row in result:
        time_str = row.event_time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {time_str} | {row.customer_id[:12]}... | {row.event_type}")
    
    # Count support tickets
    result = session.execute("SELECT COUNT(*) FROM support_tickets")
    ticket_count = result.one()[0]
    print(f"\n✓ Total support tickets: {ticket_count:,}")
    
    # Ticket types (manual aggregation)
    ticket_types = {}
    result = session.execute("SELECT ticket_type FROM support_tickets")
    for row in result:
        ticket_types[row.ticket_type] = ticket_types.get(row.ticket_type, 0) + 1
    
    if ticket_types:
        print(f"\n🎫 Ticket Types:")
        for ticket_type, count in sorted(ticket_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {ticket_type:20s}: {count:,} tickets")
    
    cluster.shutdown()

def main():
    print("\n" + "🔍 DATA VERIFICATION REPORT".center(60))
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        verify_postgres()
    except Exception as e:
        print(f"✗ PostgreSQL verification failed: {e}")
    
    try:
        verify_cassandra()
    except Exception as e:
        print(f"✗ Cassandra verification failed: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Verification Complete")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
