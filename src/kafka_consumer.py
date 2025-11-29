from kafka import KafkaConsumer
import json
from datetime import datetime
from cassandra.cluster import Cluster
import argparse
import sys

KAFKA_CONFIG = {
    'bootstrap_servers': ['localhost:9092'],
    'auto_offset_reset': 'earliest',
    'enable_auto_commit': True,
    'group_id': 'churn-consumer-group',
    'value_deserializer': lambda x: json.loads(x.decode('utf-8'))
}

CASSANDRA_CONFIG = {
    'contact_points': ['localhost'],
    'port': 9042
}

def get_cassandra_session():
    """Create Cassandra session"""
    try:
        cluster = Cluster(**CASSANDRA_CONFIG)
        session = cluster.connect('churn_keyspace')
        return cluster, session
    except Exception as e:
        print(f"Error connecting to Cassandra: {e}")
        return None, None

def process_event(event, session):
    """Process and store event in Cassandra"""
    try:
        customer_id = event['customer_id']
        event_type = event['event_type']
        timestamp = datetime.fromisoformat(event['timestamp'])
        event_data = json.dumps(event['event_data'])
        
        # Insert into Cassandra
        session.execute("""
            INSERT INTO customer_events (customer_id, event_time, event_type, event_data)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, timestamp, event_type, event_data))
        
        return True
    except Exception as e:
        print(f"  ✗ Error processing event: {e}")
        return False

def consume_events(store_in_cassandra=True, display_only=False):
    """Consume events from Kafka"""
    print("🔄 Starting Kafka consumer...")
    print(f"   Topic: customer-events")
    print(f"   Group: churn-consumer-group")
    
    # Setup Cassandra if storing
    cluster = None
    session = None
    if store_in_cassandra:
        cluster, session = get_cassandra_session()
        if not session:
            print("✗ Failed to connect to Cassandra. Events will only be displayed.")
            store_in_cassandra = False
        else:
            print("✓ Connected to Cassandra")
    
    print("\n📡 Listening for events (Press Ctrl+C to stop)...\n")
    
    # Create consumer
    try:
        consumer = KafkaConsumer('customer-events', **KAFKA_CONFIG)
    except Exception as e:
        print(f"✗ Failed to create Kafka consumer: {e}")
        sys.exit(1)
    
    event_count = 0
    stored_count = 0
    
    try:
        for message in consumer:
            event = message.value
            event_count += 1
            
            # Display event
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{event_count}] {timestamp} | Customer: {event['customer_id'][:12]}... | "
                  f"Type: {event['event_type']:20s} | "
                  f"Risk: {event['event_data'].get('risk_impact', 0):+.2f}")
            
            # Store in Cassandra
            if store_in_cassandra:
                if process_event(event, session):
                    stored_count += 1
            
    except KeyboardInterrupt:
        print(f"\n✓ Stopped consuming")
        print(f"  Total events received: {event_count}")
        if store_in_cassandra:
            print(f"  Events stored in Cassandra: {stored_count}")
    finally:
        consumer.close()
        if cluster:
            cluster.shutdown()

def test_connection():
    """Test Kafka consumer connection"""
    try:
        consumer = KafkaConsumer(
            'customer-events',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='latest',
            consumer_timeout_ms=5000
        )
        print("✓ Kafka consumer connection successful")
        
        # Check if topic exists
        topics = consumer.topics()
        if 'customer-events' in topics:
            print("✓ Topic 'customer-events' exists")
        else:
            print("⚠ Topic 'customer-events' not found (will be created on first message)")
        
        consumer.close()
        return True
    except Exception as e:
        print(f"✗ Kafka consumer connection failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kafka Event Consumer')
    parser.add_argument('--test', action='store_true', help='Test Kafka consumer connection')
    parser.add_argument('--no-store', action='store_true', help='Display events only, do not store in Cassandra')
    parser.add_argument('--display-only', action='store_true', help='Same as --no-store')
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
    else:
        store = not (args.no_store or args.display_only)
        consume_events(store_in_cassandra=store)
