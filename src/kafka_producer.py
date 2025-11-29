from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime
import argparse
import sys

KAFKA_CONFIG = {
    'bootstrap_servers': ['localhost:9092'],
    'value_serializer': lambda v: json.dumps(v).encode('utf-8')
}

# Event types and their characteristics
EVENT_TYPES = {
    'login': {'frequency': 0.3, 'risk_impact': 0.0},
    'payment_success': {'frequency': 0.15, 'risk_impact': -0.1},
    'payment_failed': {'frequency': 0.05, 'risk_impact': 0.3},
    'support_call': {'frequency': 0.1, 'risk_impact': 0.2},
    'service_complaint': {'frequency': 0.05, 'risk_impact': 0.4},
    'feature_usage': {'frequency': 0.2, 'risk_impact': -0.05},
    'service_downgrade': {'frequency': 0.03, 'risk_impact': 0.5},
    'contract_renewal': {'frequency': 0.07, 'risk_impact': -0.3},
    'bill_inquiry': {'frequency': 0.05, 'risk_impact': 0.1}
}

def get_customer_ids(limit=50):
    """Fetch customer IDs from PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='churn_db',
            user='churn_user',
            password='churn_pass'
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT customer_id FROM customers LIMIT {limit}")
        customer_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return customer_ids
    except Exception as e:
        print(f"Error fetching customer IDs: {e}")
        return []

def create_event(customer_id, event_type=None):
    """Create a customer event"""
    if not event_type:
        # Randomly select event type based on frequency
        event_type = random.choices(
            list(EVENT_TYPES.keys()),
            weights=[EVENT_TYPES[et]['frequency'] for et in EVENT_TYPES.keys()]
        )[0]
    
    event = {
        'customer_id': customer_id,
        'event_type': event_type,
        'timestamp': datetime.now().isoformat(),
        'event_data': {
            'risk_impact': EVENT_TYPES[event_type]['risk_impact'],
            'source': 'kafka_simulator',
            'details': f'Customer {customer_id} triggered {event_type}'
        }
    }
    return event

def produce_continuous(producer, customer_ids, interval=2):
    """Continuously produce events"""
    print(f"📡 Starting continuous event production (interval: {interval}s)")
    print(f"   Simulating events for {len(customer_ids)} customers")
    print("   Press Ctrl+C to stop\n")
    
    event_count = 0
    try:
        while True:
            customer_id = random.choice(customer_ids)
            event = create_event(customer_id)
            
            producer.send('customer-events', value=event)
            event_count += 1
            
            print(f"[{event_count}] {datetime.now().strftime('%H:%M:%S')} | "
                  f"Customer: {customer_id[:8]}... | "
                  f"Event: {event['event_type']}")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n✓ Stopped. Total events produced: {event_count}")

def produce_single(producer, customer_id, event_type):
    """Produce a single event"""
    event = create_event(customer_id, event_type)
    producer.send('customer-events', value=event)
    producer.flush()
    
    print(f"✓ Event sent:")
    print(f"  Customer: {customer_id}")
    print(f"  Type: {event_type}")
    print(f"  Timestamp: {event['timestamp']}")
    print(f"  Risk Impact: {event['event_data']['risk_impact']}")

def produce_batch(producer, customer_ids, num_events):
    """Produce a batch of random events"""
    print(f"📦 Producing {num_events} random events...")
    
    for i in range(num_events):
        customer_id = random.choice(customer_ids)
        event = create_event(customer_id)
        producer.send('customer-events', value=event)
        
        if (i + 1) % 10 == 0:
            print(f"  Sent {i + 1}/{num_events} events...")
    
    producer.flush()
    print(f"✓ Batch complete. {num_events} events sent to Kafka")

def test_connection():
    """Test Kafka connection"""
    try:
        producer = KafkaProducer(**KAFKA_CONFIG)
        print("✓ Connected to Kafka broker at localhost:9092")
        producer.close()
        return True
    except Exception as e:
        print(f"✗ Kafka connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if Kafka is running: docker compose ps kafka")
        print("2. Check Kafka logs: docker compose logs kafka")
        print("3. Verify port 9092 is accessible")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Kafka Event Producer')
    parser.add_argument('--test', action='store_true', help='Test Kafka connection')
    parser.add_argument('--continuous', action='store_true', help='Produce events continuously')
    parser.add_argument('--interval', type=int, default=2, help='Interval between events (seconds)')
    parser.add_argument('--batch', type=int, help='Produce N random events')
    parser.add_argument('--event', type=str, help='Event type for single event')
    parser.add_argument('--customer', type=str, help='Customer ID for single event')
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
        sys.exit(0)
    
    # Get customer IDs
    print("Fetching customer IDs from PostgreSQL...")
    customer_ids = get_customer_ids(100)
    
    if not customer_ids:
        print("✗ No customer IDs found. Please run data ingestion first.")
        sys.exit(1)
    
    print(f"✓ Loaded {len(customer_ids)} customer IDs\n")
    
    # Create Kafka producer
    try:
        producer = KafkaProducer(**KAFKA_CONFIG)
        print("✓ Connected to Kafka\n")
    except Exception as e:
        print(f"✗ Failed to connect to Kafka: {e}")
        sys.exit(1)
    
    # Execute based on arguments
    if args.continuous:
        produce_continuous(producer, customer_ids, args.interval)
    elif args.batch:
        produce_batch(producer, customer_ids, args.batch)
    elif args.event and args.customer:
        if args.event not in EVENT_TYPES:
            print(f"✗ Invalid event type. Choose from: {list(EVENT_TYPES.keys())}")
            sys.exit(1)
        produce_single(producer, args.customer, args.event)
    else:
        print("Usage examples:")
        print("  python src/kafka_producer.py --test")
        print("  python src/kafka_producer.py --continuous --interval 2")
        print("  python src/kafka_producer.py --batch 50")
        print("  python src/kafka_producer.py --event payment_failed --customer 7590-VHVEG")
        print(f"\nAvailable event types: {list(EVENT_TYPES.keys())}")
    
    producer.close()
