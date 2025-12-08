"""
Spark ML-based Model Training for ChurnGuard Platform
Uses PySpark MLlib for distributed machine learning
"""
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import (
    VectorAssembler, StandardScaler, StringIndexer,
    OneHotEncoder, Imputer
)
from pyspark.ml.classification import (
    LogisticRegression, RandomForestClassifier, GBTClassifier
)
from pyspark.ml.evaluation import (
    BinaryClassificationEvaluator, MulticlassClassificationEvaluator
)
from pyspark.sql.functions import col, when, lit
import argparse
from datetime import datetime
import os

# HDFS paths
HDFS_NAMENODE = "hdfs://namenode:9000"
HDFS_PROCESSED_PATH = f"{HDFS_NAMENODE}/churnguard/data/processed"
HDFS_MODELS_PATH = f"{HDFS_NAMENODE}/churnguard/models"

def create_spark_session():
    """Create Spark session for ML training"""
    print("🚀 Creating Spark session for ML training...")
    
    spark = SparkSession.builder \
        .appName("ChurnGuard-ML-Training") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "2g") \
        .config("spark.executor.cores", "2") \
        .config("spark.driver.memory", "1g") \
        .config("spark.sql.adaptive.enabled", "true") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("✓ Spark session created")
    return spark

def load_processed_data(spark, from_hdfs=True):
    """Load processed data from HDFS or local"""
    print("📊 Loading processed data...")
    
    if from_hdfs:
        try:
            # Load from HDFS (Parquet format)
            df = spark.read.parquet(f"{HDFS_PROCESSED_PATH}/processed_churn_data")
            print(f"✓ Loaded {df.count():,} records from HDFS")
            return df
        except Exception as e:
            print(f"⚠ HDFS load failed: {e}")
            print("   Falling back to local CSV...")
            from_hdfs = False
    
    if not from_hdfs:
        # Load from local CSV
        df = spark.read.csv(
            "data/processed/processed_churn_data.csv",
            header=True,
            inferSchema=True
        )
        print(f"✓ Loaded {df.count():,} records from local CSV")
        return df

def prepare_features(df):
    """Prepare features for ML training"""
    print("\n🔧 Preparing features for ML...")
    
    # Get feature columns (exclude customer_id and churn)
    feature_cols = [c for c in df.columns if c not in ['customer_id', 'churn']]
    
    # Ensure all feature columns are numeric
    for col_name in feature_cols:
        df = df.withColumn(col_name, col(col_name).cast("double"))
    
    # Handle any null values
    imputer = Imputer(
        inputCols=feature_cols,
        outputCols=[f"{c}_imputed" for c in feature_cols]
    )
    df = imputer.fit(df).transform(df)
    
    # Assemble features into vector
    assembler = VectorAssembler(
        inputCols=[f"{c}_imputed" for c in feature_cols],
        outputCol="features"
    )
    df = assembler.transform(df)
    
    # Index churn label (Yes=1, No=0)
    indexer = StringIndexer(inputCol="churn", outputCol="label")
    df = indexer.fit(df).transform(df)
    
    # Select only needed columns
    df = df.select("customer_id", "features", "label")
    
    print(f"✓ Features prepared: {len(feature_cols)} features")
    return df, feature_cols

def train_models_spark(df):
    """Train multiple ML models using Spark MLlib"""
    print("\n🎯 Training ML models with Spark MLlib...")
    print("=" * 60)
    
    # Split data
    train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
    print(f"Train set: {train_df.count():,} samples")
    print(f"Test set: {test_df.count():,} samples")
    
    # Scale features
    scaler = StandardScaler(
        inputCol="features",
        outputCol="scaled_features",
        withStd=True,
        withMean=True
    )
    scaler_model = scaler.fit(train_df)
    train_df = scaler_model.transform(train_df)
    test_df = scaler_model.transform(test_df)
    
    # Models to train
    models = {
        "Logistic Regression": LogisticRegression(
            featuresCol="scaled_features",
            labelCol="label",
            maxIter=100
        ),
        "Random Forest": RandomForestClassifier(
            featuresCol="scaled_features",
            labelCol="label",
            numTrees=100,
            seed=42
        ),
        "Gradient Boosting": GBTClassifier(
            featuresCol="scaled_features",
            labelCol="label",
            maxIter=50,
            seed=42
        )
    }
    
    results = {}
    evaluator_auc = BinaryClassificationEvaluator(
        labelCol="label",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC"
    )
    evaluator_acc = MulticlassClassificationEvaluator(
        labelCol="label",
        predictionCol="prediction",
        metricName="accuracy"
    )
    
    for name, model in models.items():
        print(f"\n📈 Training {name}...")
        start_time = datetime.now()
        
        # Train model
        trained_model = model.fit(train_df)
        
        # Make predictions
        predictions = trained_model.transform(test_df)
        
        # Evaluate
        auc = evaluator_auc.evaluate(predictions)
        accuracy = evaluator_acc.evaluate(predictions)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        results[name] = {
            'model': trained_model,
            'scaler': scaler_model,
            'auc': auc,
            'accuracy': accuracy,
            'duration': duration
        }
        
        print(f"   ✓ Trained in {duration:.2f} seconds")
        print(f"   Accuracy: {accuracy:.4f} | ROC-AUC: {auc:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ All models trained successfully!")
    
    return results, scaler_model

def save_models_spark(results, scaler_model, feature_cols):
    """Save trained models to HDFS and local"""
    print("\n💾 Saving models...")
    
    # Find best model (by AUC)
    best_model_name = max(results.keys(), key=lambda k: results[k]['auc'])
    best_model = results[best_model_name]['model']
    
    print(f"Best model: {best_model_name} (AUC: {results[best_model_name]['auc']:.4f})")
    
    # Save to local filesystem
    local_models_dir = "data/models"
    os.makedirs(local_models_dir, exist_ok=True)
    
    # Save best model
    best_model_path = f"{local_models_dir}/spark_{best_model_name.lower().replace(' ', '_')}_model"
    best_model.write().overwrite().save(best_model_path)
    print(f"✓ Saved best model to: {best_model_path}")
    
    # Save scaler
    scaler_path = f"{local_models_dir}/spark_scaler"
    scaler_model.write().overwrite().save(scaler_path)
    print(f"✓ Saved scaler to: {scaler_path}")
    
    # Save feature list
    with open(f"{local_models_dir}/spark_feature_names.txt", "w") as f:
        for col_name in feature_cols:
            f.write(f"{col_name}\n")
    print(f"✓ Saved feature list")
    
    # Save metrics
    with open(f"{local_models_dir}/spark_model_metrics.txt", "w") as f:
        f.write("Spark MLlib Model Training Results\n")
        f.write("=" * 60 + "\n\n")
        for name, result in results.items():
            f.write(f"{name}:\n")
            f.write(f"  Accuracy: {result['accuracy']:.4f}\n")
            f.write(f"  ROC-AUC: {result['auc']:.4f}\n")
            f.write(f"  Training Time: {result['duration']:.2f}s\n\n")
        f.write(f"Best Model: {best_model_name}\n")
    print(f"✓ Saved metrics")
    
    # Try to save to HDFS
    try:
        hdfs_model_path = f"{HDFS_MODELS_PATH}/spark_{best_model_name.lower().replace(' ', '_')}_model"
        best_model.write().overwrite().save(hdfs_model_path)
        print(f"✓ Saved model to HDFS: {hdfs_model_path}")
    except Exception as e:
        print(f"⚠ Could not save to HDFS: {e}")

def train_pipeline_spark():
    """Run the complete Spark ML training pipeline"""
    print("=" * 60)
    print("🚀 STARTING SPARK ML TRAINING PIPELINE")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Step 1: Load processed data
        df = load_processed_data(spark, from_hdfs=True)
        
        # Step 2: Prepare features
        df, feature_cols = prepare_features(df)
        
        # Step 3: Train models
        results, scaler_model = train_models_spark(df)
        
        # Step 4: Save models
        save_models_spark(results, scaler_model, feature_cols)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print(f"✅ SPARK ML TRAINING COMPLETE!")
        print(f"   Total Duration: {duration:.2f} seconds")
        print("=" * 60)
        
    finally:
        spark.stop()
        print("✓ Spark session stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Spark ML Training Pipeline')
    parser.add_argument('--run', action='store_true', help='Run the Spark ML training pipeline')
    
    args = parser.parse_args()
    
    if args.run:
        train_pipeline_spark()
    else:
        print("Usage: python src/train_spark.py --run")
        print("\nNote: Make sure Spark and HDFS services are running:")
        print("  docker compose up -d spark-master spark-worker namenode datanode")
        print("\nAlso ensure processed data exists:")
        print("  python src/process_spark.py --run")

