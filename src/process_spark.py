"""
Spark-based Data Processing Pipeline for ChurnGuard Platform
Uses PySpark for distributed data processing instead of Pandas
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, isnan, isnull, count, sum as spark_sum,
    avg, max as spark_max, min as spark_min,
    regexp_replace, trim, lower, split, size,
    collect_list, explode, lit, concat_ws
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, TimestampType
)
from pyspark.ml.feature import (
    StringIndexer, OneHotEncoder, VectorAssembler,
    StandardScaler, Imputer
)
from pyspark.ml import Pipeline
import psycopg2
from cassandra.cluster import Cluster
from datetime import datetime
import argparse
import sys

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

# HDFS paths
HDFS_NAMENODE = "hdfs://namenode:9000"
HDFS_RAW_PATH = f"{HDFS_NAMENODE}/churnguard/data/raw"
HDFS_PROCESSED_PATH = f"{HDFS_NAMENODE}/churnguard/data/processed"

def create_spark_session():
    """Create Spark session with HDFS support"""
    print("🚀 Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName("ChurnGuard-Processing") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "2g") \
        .config("spark.executor.cores", "2") \
        .config("spark.driver.memory", "1g") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("✓ Spark session created")
    return spark

def load_structured_data_spark(spark):
    """Load customer data from PostgreSQL using Spark JDBC"""
    print("📊 Loading structured data from PostgreSQL via Spark...")
    
    try:
        # Read from PostgreSQL using JDBC
        df = spark.read \
            .format("jdbc") \
            .option("url", f"jdbc:postgresql://localhost:5432/{DB_CONFIG['database']}") \
            .option("dbtable", "customers") \
            .option("user", DB_CONFIG['user']) \
            .option("password", DB_CONFIG['password']) \
            .option("driver", "org.postgresql.Driver") \
            .load()
        
        print(f"✓ Loaded {df.count():,} customer records")
        return df
        
    except Exception as e:
        print(f"⚠ JDBC connection failed, trying alternative method: {e}")
        # Fallback: Load from CSV if JDBC fails
        print("   Loading from local CSV instead...")
        df = spark.read.csv(
            "data/raw/telco_churn.csv",
            header=True,
            inferSchema=True
        )
        print(f"✓ Loaded {df.count():,} customer records from CSV")
        return df

def load_from_hdfs(spark, hdfs_path):
    """Load data from HDFS"""
    print(f"📥 Loading data from HDFS: {hdfs_path}")
    
    try:
        df = spark.read.csv(
            hdfs_path,
            header=True,
            inferSchema=True
        )
        print(f"✓ Loaded {df.count():,} records from HDFS")
        return df
    except Exception as e:
        print(f"✗ Error loading from HDFS: {e}")
        return None

def save_to_hdfs(df, hdfs_path, format="parquet"):
    """Save DataFrame to HDFS"""
    print(f"💾 Saving to HDFS: {hdfs_path}")
    
    try:
        if format == "parquet":
            df.write.mode("overwrite").parquet(hdfs_path)
        elif format == "csv":
            df.write.mode("overwrite").option("header", "true").csv(hdfs_path)
        else:
            df.write.mode("overwrite").format(format).save(hdfs_path)
        
        print(f"✓ Saved to HDFS ({format} format)")
        return True
    except Exception as e:
        print(f"✗ Error saving to HDFS: {e}")
        return False

def clean_data_spark(df):
    """Clean and prepare structured data using Spark"""
    print("\n🧹 Cleaning data with Spark...")
    
    original_count = df.count()
    
    # Handle TotalCharges - convert to numeric (some are empty strings)
    df = df.withColumn(
        "total_charges",
        when(col("total_charges") == "", None)
        .otherwise(col("total_charges").cast("double"))
    )
    
    # Fill missing TotalCharges with MonthlyCharges (for new customers)
    df = df.withColumn(
        "total_charges",
        when(col("total_charges").isNull(), col("monthly_charges"))
        .otherwise(col("total_charges"))
    )
    
    # Convert binary columns
    df = df.withColumn("senior_citizen", col("senior_citizen").cast("int"))
    
    # Drop rows with any remaining nulls in critical columns
    critical_cols = ["customer_id", "tenure", "monthly_charges", "churn"]
    df = df.dropna(subset=critical_cols)
    
    final_count = df.count()
    print(f"✓ Cleaned data: {final_count:,} records (removed {original_count - final_count} rows)")
    return df

def engineer_features_spark(df):
    """Create features from structured data using Spark"""
    print("\n⚙️ Engineering features with Spark...")
    
    # Tenure categories
    df = df.withColumn(
        "tenure_group",
        when(col("tenure") <= 12, "0-1yr")
        .when(col("tenure") <= 24, "1-2yr")
        .when(col("tenure") <= 48, "2-4yr")
        .otherwise("4yr+")
    )
    
    # Service counts
    service_cols = [
        'phone_service', 'multiple_lines', 'internet_service',
        'online_security', 'online_backup', 'device_protection',
        'tech_support', 'streaming_tv', 'streaming_movies'
    ]
    
    # Calculate total services by summing individual service indicators
    total_services_expr = lit(0)
    for c in service_cols:
        if c in df.columns:
            total_services_expr = total_services_expr + when(col(c) == "Yes", 1).otherwise(0)
    
    df = df.withColumn("total_services", total_services_expr)
    
    # Monthly charges category
    df = df.withColumn(
        "charges_category",
        when(col("monthly_charges") <= 30, "Low")
        .when(col("monthly_charges") <= 60, "Medium")
        .when(col("monthly_charges") <= 90, "High")
        .otherwise("Very High")
    )
    
    # Contract risk score
    df = df.withColumn(
        "contract_risk",
        when(col("contract") == "Month-to-month", 1.0)
        .when(col("contract") == "One year", 0.5)
        .when(col("contract") == "Two year", 0.2)
        .otherwise(0.5)
    )
    
    # Payment method risk
    df = df.withColumn(
        "payment_risk",
        when(col("payment_method") == "Electronic check", 1.0)
        .when(col("payment_method") == "Mailed check", 0.7)
        .otherwise(0.3)
    )
    
    # Average monthly revenue
    df = df.withColumn(
        "avg_monthly_revenue",
        col("total_charges") / (col("tenure") + 1)
    )
    
    # Has dependents or partner
    df = df.withColumn(
        "has_family",
        when((col("partner") == "Yes") | (col("dependents") == "Yes"), 1)
        .otherwise(0)
    )
    
    # Internet service indicator
    df = df.withColumn(
        "has_internet",
        when(col("internet_service") != "No", 1)
        .otherwise(0)
    )
    
    print("✓ Created 8 new features")
    return df

def load_event_features_spark(spark):
    """Load and aggregate event data from Cassandra using Spark"""
    print("\n📡 Loading event features from Cassandra...")
    
    try:
        # Read from Cassandra using Spark Cassandra connector
        # Note: This requires cassandra-connector dependency
        # For now, we'll use a simpler approach: read via Python and convert
        
        cluster = Cluster(**CASSANDRA_CONFIG)
        session = cluster.connect('churn_keyspace')
        
        result = session.execute("SELECT customer_id, event_type, event_data FROM customer_events")
        
        events_data = []
        for row in result:
            events_data.append({
                'customer_id': row.customer_id,
                'event_type': row.event_type,
                'event_data': row.event_data
            })
        
        cluster.shutdown()
        
        if not events_data:
            print("⚠ No events found in Cassandra")
            return None
        
        # Convert to Spark DataFrame
        events_df = spark.createDataFrame(events_data)
        
        # Aggregate by customer
        event_features = events_df.groupBy("customer_id").agg(
            count("event_type").alias("total_events")
        )
        
        # Count specific event types
        event_type_counts = events_df.groupBy("customer_id", "event_type").count()
        event_type_pivot = event_type_counts.groupBy("customer_id").pivot("event_type").sum("count")
        
        event_features = event_features.join(event_type_pivot, on="customer_id", how="left")
        event_features = event_features.fillna(0)
        
        # Calculate risk indicators
        if "payment_failed" in event_features.columns:
            event_features = event_features.withColumn(
                "payment_fail_rate",
                col("payment_failed") / (col("total_events") + 1)
            )
        else:
            event_features = event_features.withColumn("payment_fail_rate", lit(0.0))
        
        if "support_call" in event_features.columns:
            event_features = event_features.withColumn(
                "support_frequency",
                col("support_call") / (col("total_events") + 1)
            )
        else:
            event_features = event_features.withColumn("support_frequency", lit(0.0))
        
        print(f"✓ Extracted event features for {event_features.count():,} customers")
        return event_features
        
    except Exception as e:
        print(f"⚠ Error loading events: {e}")
        print("   Creating empty event features...")
        return None

def load_ticket_features_spark(spark):
    """Load and aggregate support ticket data from Cassandra"""
    print("\n🎫 Loading ticket features from Cassandra...")
    
    try:
        cluster = Cluster(**CASSANDRA_CONFIG)
        session = cluster.connect('churn_keyspace')
        
        result = session.execute("SELECT customer_id, ticket_type, sentiment FROM support_tickets")
        
        tickets_data = []
        for row in result:
            tickets_data.append({
                'customer_id': row.customer_id,
                'ticket_type': row.ticket_type,
                'sentiment': row.sentiment
            })
        
        cluster.shutdown()
        
        if not tickets_data:
            print("⚠ No tickets found in Cassandra")
            return None
        
        tickets_df = spark.createDataFrame(tickets_data)
        
        # Aggregate by customer
        ticket_features = tickets_df.groupBy("customer_id").agg(
            count("ticket_type").alias("total_tickets")
        )
        
        # Sentiment counts
        sentiment_counts = tickets_df.groupBy("customer_id", "sentiment").count()
        sentiment_pivot = sentiment_counts.groupBy("customer_id").pivot("sentiment").sum("count")
        
        ticket_features = ticket_features.join(sentiment_pivot, on="customer_id", how="left")
        ticket_features = ticket_features.fillna(0)
        
        # Calculate sentiment score
        if "negative" in ticket_features.columns and "positive" in ticket_features.columns:
            ticket_features = ticket_features.withColumn(
                "sentiment_score",
                (col("positive") - col("negative")) / (col("total_tickets") + 1)
            )
        else:
            ticket_features = ticket_features.withColumn("sentiment_score", lit(0.0))
        
        print(f"✓ Extracted ticket features for {ticket_features.count():,} customers")
        return ticket_features
        
    except Exception as e:
        print(f"⚠ Error loading tickets: {e}")
        print("   Creating empty ticket features...")
        return None

def merge_features_spark(df, event_features, ticket_features):
    """Merge all features together using Spark"""
    print("\n🔗 Merging all features with Spark...")
    
    original_count = df.count()
    
    # Merge event features
    if event_features is not None:
        df = df.join(event_features, on="customer_id", how="left")
        # Fill customers with no events
        event_cols = [c for c in event_features.columns if c != "customer_id"]
        for col_name in event_cols:
            df = df.withColumn(col_name, when(col(col_name).isNull(), 0).otherwise(col(col_name)))
    else:
        df = df.withColumn("total_events", lit(0))
        df = df.withColumn("payment_fail_rate", lit(0.0))
        df = df.withColumn("support_frequency", lit(0.0))
    
    # Merge ticket features
    if ticket_features is not None:
        df = df.join(ticket_features, on="customer_id", how="left")
        ticket_cols = [c for c in ticket_features.columns if c != "customer_id"]
        for col_name in ticket_cols:
            df = df.withColumn(col_name, when(col(col_name).isNull(), 0).otherwise(col(col_name)))
    else:
        df = df.withColumn("total_tickets", lit(0))
        df = df.withColumn("sentiment_score", lit(0.0))
    
    final_count = df.count()
    print(f"✓ Merged features: {final_count:,} records")
    return df

def encode_categorical_spark(df):
    """Encode categorical variables using Spark ML"""
    print("\n🔢 Encoding categorical variables with Spark ML...")
    
    # Binary encoding for Yes/No columns
    binary_cols = ['gender', 'partner', 'dependents', 'phone_service', 'paperless_billing', 'churn']
    
    for col_name in binary_cols:
        if col_name in df.columns:
            df = df.withColumn(
                col_name,
                when(col(col_name) == "Yes", 1).otherwise(0)
            )
    
    # For one-hot encoding, we'll use StringIndexer + OneHotEncoder for key columns
    # For simplicity, we'll do manual encoding for now
    categorical_cols = [
        'multiple_lines', 'internet_service', 'online_security',
        'online_backup', 'device_protection', 'tech_support',
        'streaming_tv', 'streaming_movies', 'contract',
        'payment_method', 'tenure_group', 'charges_category'
    ]
    
    # Get distinct values for each categorical column and create one-hot columns
    for cat_col in categorical_cols:
        if cat_col in df.columns:
            distinct_values = [row[cat_col] for row in df.select(cat_col).distinct().collect() if row[cat_col] is not None]
            for val in distinct_values[1:]:  # Skip first to avoid multicollinearity
                col_name = f"{cat_col}_{val}".replace(" ", "_").replace("-", "_")
                df = df.withColumn(
                    col_name,
                    when(col(cat_col) == val, 1).otherwise(0)
                )
    
    feature_count = len([c for c in df.columns if c not in ['customer_id', 'churn']])
    print(f"✓ Encoded categorical variables")
    print(f"  Total features: {feature_count}")
    
    return df

def process_pipeline_spark():
    """Run the complete Spark-based processing pipeline"""
    print("=" * 60)
    print("🚀 STARTING SPARK DATA PROCESSING PIPELINE")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Step 1: Load structured data
        df = load_structured_data_spark(spark)
        
        # Step 2: Clean data
        df = clean_data_spark(df)
        
        # Step 3: Engineer basic features
        df = engineer_features_spark(df)
        
        # Step 4: Load event features
        event_features = load_event_features_spark(spark)
        
        # Step 5: Load ticket features
        ticket_features = load_ticket_features_spark(spark)
        
        # Step 6: Merge all features
        df = merge_features_spark(df, event_features, ticket_features)
        
        # Step 7: Encode categorical variables
        df = encode_categorical_spark(df)
        
        # Step 8: Save to HDFS (Parquet format for efficiency)
        hdfs_output_path = f"{HDFS_PROCESSED_PATH}/processed_churn_data"
        save_to_hdfs(df, hdfs_output_path, format="parquet")
        
        # Also save to local CSV for compatibility
        local_output_path = "data/processed/processed_churn_data.csv"
        df.coalesce(1).write.mode("overwrite").option("header", "true").csv(local_output_path)
        print(f"✓ Saved to local: {local_output_path}")
        
        # Print statistics
        row_count = df.count()
        col_count = len(df.columns)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print(f"✅ SPARK PROCESSING COMPLETE!")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Final dataset: {row_count:,} rows × {col_count:,} columns")
        print(f"   Saved to HDFS: {hdfs_output_path}")
        print("=" * 60)
        
    finally:
        spark.stop()
        print("✓ Spark session stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spark Data Processing Pipeline')
    parser.add_argument('--run', action='store_true', help='Run the Spark processing pipeline')
    
    args = parser.parse_args()
    
    if args.run:
        process_pipeline_spark()
    else:
        print("Usage: python src/process_spark.py --run")
        print("\nNote: Make sure Spark and HDFS services are running:")
        print("  docker compose up -d spark-master spark-worker namenode datanode")

