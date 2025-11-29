# ChurnGuard Analytics Platform
## Architecture Design Document

**Project:** CIS 641 Big Data Platform - Phase 2  
**Team:** ChurnGuard Analytics  
**Date:** November 2025  
**Version:** 1.0  

---

## 1. Executive Summary

### 1.1 Purpose

This document describes the technical architecture of the ChurnGuard Analytics Platform, a big data system designed to predict customer churn using heterogeneous databases, event streaming, and machine learning. The architecture supports:

- Real-time and batch data processing
- Multiple data types (structured, unstructured, time-series)
- Machine learning model training and inference
- Interactive dashboards and REST APIs for stakeholder consumption

### 1.2 Scope

This architecture covers:
- Infrastructure components (VirtualBox VM, Docker containers)
- Data storage layer (PostgreSQL, Apache Cassandra)
- Data ingestion pipelines (batch and streaming)
- Processing and analytics layer (ETL, feature engineering, NLP)
- Machine learning layer (model training, evaluation, deployment)
- Application layer (REST API, web dashboard)

### 1.3 Architecture Principles

**Modularity:** Components are loosely coupled and independently deployable  
**Scalability:** Horizontal scaling via containerization and distributed databases  
**Reliability:** Fault tolerance through database replication and service restart policies  
**Performance:** Optimized for both batch processing and real-time streaming  
**Maintainability:** Clear separation of concerns, comprehensive documentation, version control  

---

## 2. High-Level Architecture Overview

### 2.1 System Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────┬────────────────┬───────────────┬──────────────────┤
│   CRM/ERP   │   Support Logs │  Social Media │  Payment Systems │
│  (CSV/SQL)  │   (JSON/Text)  │   (API/JSON)  │     (Events)     │
└──────┬──────┴────────┬───────┴───────┬───────┴────────┬─────────┘
       │               │               │                │
       │               │               │                │
       ▼               ▼               ▼                ▼
┌────────────────────────────────────────────────────────────────┐
│                   INGESTION LAYER                               │
├──────────────┬───────────────────┬──────────────────────────────┤
│   Batch      │   Apache Kafka    │    REST API Gateway          │
│   Loader     │   (Streaming)     │    (Manual Upload)           │
│  (Python)    │   Port: 9092      │    Port: 8000                │
└──────┬───────┴─────────┬─────────┴─────────────┬────────────────┘
       │                 │                       │
       │                 │                       │
       ▼                 ▼                       ▼
┌────────────────────────────────────────────────────────────────┐
│                   STORAGE LAYER                                 │
├───────────────┬──────────────────┬──────────────────────────────┤
│  PostgreSQL   │  Apache Cassandra│   Local Filesystem           │
│  Port: 5432   │  Port: 9042      │   (Model Artifacts,          │
│  (Structured) │  (Time-Series,   │    Raw Files)                │
│  7,043 rows   │   Unstructured)  │                              │
└───────┬───────┴────────┬─────────┴──────────┬───────────────────┘
        │                │                    │
        │                │                    │
        ▼                ▼                    ▼
┌────────────────────────────────────────────────────────────────┐
│               PROCESSING & ANALYTICS LAYER                      │
├──────────────┬──────────────────┬──────────────────────────────┤
│   Pandas     │   NLP Pipeline   │   Feature Engineering        │
│  (ETL/ELT)   │  (TextBlob/NLTK) │   (Scikit-learn Pipeline)    │
│              │  (Sentiment)     │   (57 features)              │
└──────┬───────┴─────────┬────────┴─────────┬────────────────────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼
┌────────────────────────────────────────────────────────────────┐
│                  MACHINE LEARNING LAYER                         │
├──────────────┬──────────────────┬──────────────────────────────┤
│  Scikit-learn│    XGBoost       │   Model Storage              │
│  (Baseline)  │  (Production)    │   (Pickle/Joblib)            │
│  LogReg      │  80.3% Accuracy  │   Versioning                 │
└──────┬───────┴─────────┬────────┴─────────┬────────────────────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼
┌────────────────────────────────────────────────────────────────┐
│                 STREAMING ANALYTICS                             │
├─────────────────────────────────────────────────────────────────┤
│   Kafka Consumer → Real-time Feature Extraction → Scoring      │
│   (Python)          (Event aggregation)          (Inference)   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
├──────────────┬──────────────────┬──────────────────────────────┤
│  FastAPI     │   Streamlit      │    In-Memory Cache           │
│  Port: 8000  │   Port: 8501     │    (Python Dict)             │
│  (REST API)  │   (Dashboard)    │                              │
│  5 endpoints │   4 pages        │                              │
└──────┬───────┴─────────┬────────┴─────────┬────────────────────┘
       │                 │                  │
       │                 │                  │
       ▼                 ▼                  ▼
┌────────────────────────────────────────────────────────────────┐
│                  END USERS & SYSTEMS                            │
├──────────────┬──────────────────┬──────────────────────────────┤
│   Customer   │    Marketing     │      Executive               │
│   Success    │    Automation    │      Dashboard               │
│   Teams      │    Systems       │      Reports                 │
└──────────────┴──────────────────┴──────────────────────────────┘

                    DEPLOYMENT ENVIRONMENT
        ┌───────────────────────────────────────────────┐
        │   Oracle VirtualBox VM (Ubuntu 22.04 LTS)     │
        │   Resources: 8GB RAM, 4 CPUs, 50GB Disk       │
        │   All components run in Docker containers     │
        └───────────────────────────────────────────────┘
```

### 2.2 Architecture Layers

**Layer 1: Data Sources**
- External systems providing customer data
- Multiple formats: CSV, SQL, JSON, XML, real-time events

**Layer 2: Ingestion**
- Batch loading via Python scripts
- Real-time streaming via Apache Kafka
- REST API for manual uploads

**Layer 3: Storage**
- PostgreSQL for structured relational data
- Cassandra for unstructured time-series data
- Filesystem for model artifacts and raw files

**Layer 4: Processing**
- ETL pipelines using Pandas
- NLP processing for sentiment analysis
- Feature engineering (57 features)

**Layer 5: Machine Learning**
- Model training (Logistic Regression, Random Forest, XGBoost)
- Model evaluation and selection
- Model storage and versioning

**Layer 6: Streaming Analytics**
- Real-time event consumption from Kafka
- On-the-fly feature extraction
- Real-time churn scoring

**Layer 7: Application**
- REST API (FastAPI) for programmatic access
- Web dashboard (Streamlit) for interactive exploration
- Caching for performance optimization

**Layer 8: End Users**
- Customer Success teams
- Marketing automation systems
- Executive stakeholders

---

## 3. Component Details

### 3.1 Infrastructure Layer

#### 3.1.1 Development Environment

**Oracle VirtualBox VM:**
- **Host OS:** Windows/Mac/Linux
- **Guest OS:** Ubuntu 22.04 LTS Server
- **Resources:**
  - RAM: 8GB
  - CPU: 4 cores
  - Disk: 50GB (dynamically allocated VDI)
- **Network:** NAT with port forwarding
- **Purpose:** Isolated, reproducible development environment

**Port Forwarding Configuration:**

| Service | Host Port | Guest Port | Protocol |
|---------|-----------|------------|----------|
| PostgreSQL | 5432 | 5432 | TCP |
| Cassandra | 9042 | 9042 | TCP |
| Kafka | 9092 | 9092 | TCP |
| FastAPI | 8000 | 8000 | TCP |
| Streamlit | 8501 | 8501 | TCP |
| SSH | 2222 | 22 | TCP |

#### 3.1.2 Containerization

**Docker Compose:**
- **Version:** Docker Compose V2 (plugin)
- **Purpose:** Orchestrate multi-container application
- **Configuration File:** `docker-compose.yml`
- **Services:** 4 containers (PostgreSQL, Cassandra, Kafka, Zookeeper)

**Container Details:**

| Container | Image | Exposed Ports | Volumes | Restart Policy |
|-----------|-------|---------------|---------|----------------|
| postgres | postgres:14 | 5432 | postgres_data | unless-stopped |
| cassandra | cassandra:4.1 | 9042 | cassandra_data | unless-stopped |
| kafka | confluentinc/cp-kafka:7.5.0 | 9092 | none | unless-stopped |
| zookeeper | confluentinc/cp-zookeeper:7.5.0 | 2181 | zookeeper_data | unless-stopped |

---

### 3.2 Data Storage Layer

#### 3.2.1 PostgreSQL (Structured Data)

**Version:** 14.x  
**Purpose:** Store structured customer profiles and relational data  
**Access:** psycopg2 Python driver  

**Schema Design:**

**Table: `customers`**

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| customer_id | VARCHAR(50) | Unique customer identifier | PRIMARY KEY |
| gender | VARCHAR(10) | Customer gender | |
| senior_citizen | INTEGER | Senior citizen flag (0/1) | |
| partner | VARCHAR(10) | Has partner (Yes/No) | |
| dependents | VARCHAR(10) | Has dependents (Yes/No) | |
| tenure | INTEGER | Months as customer | |
| phone_service | VARCHAR(10) | Has phone service | |
| multiple_lines | VARCHAR(20) | Multiple phone lines | |
| internet_service | VARCHAR(20) | Internet service type | |
| online_security | VARCHAR(20) | Online security service | |
| online_backup | VARCHAR(20) | Online backup service | |
| device_protection | VARCHAR(20) | Device protection | |
| tech_support | VARCHAR(20) | Tech support service | |
| streaming_tv | VARCHAR(20) | Streaming TV service | |
| streaming_movies | VARCHAR(20) | Streaming movies service | |
| contract | VARCHAR(20) | Contract type | |
| paperless_billing | VARCHAR(10) | Paperless billing (Yes/No) | |
| payment_method | VARCHAR(50) | Payment method | |
| monthly_charges | DECIMAL(10,2) | Monthly charges ($) | |
| total_charges | VARCHAR(20) | Total charges ($) | |
| churn | VARCHAR(10) | Churned (Yes/No) | |
| created_at | TIMESTAMP | Record creation time | DEFAULT NOW() |

**Indexes:**
- Primary key on `customer_id`
- Index on `churn` for filtering
- Index on `contract` for analytics queries

**Current Data Volume:**
- Rows: 7,043 customers
- Disk usage: ~2 MB
- Query performance: < 50ms for lookups

#### 3.2.2 Apache Cassandra (Unstructured/Time-Series Data)

**Version:** 4.1.x  
**Purpose:** Store time-series events and unstructured support data  
**Access:** cassandra-driver Python library  
**Replication Factor:** 1 (development), 3 (production)  

**Keyspace: `churn_keyspace`**

**Table: `customer_events`**

| Column | Type | Description | Key Type |
|--------|------|-------------|----------|
| customer_id | text | Customer identifier | PARTITION KEY |
| event_time | timestamp | Event timestamp | CLUSTERING KEY (DESC) |
| event_type | text | Event type (login, payment, etc.) | |
| event_data | text | Event details (JSON) | |

**Primary Key:** `(customer_id, event_time)`  
**Clustering Order:** DESC (newest events first)  

**Table: `support_tickets`**

| Column | Type | Description | Key Type |
|--------|------|-------------|----------|
| ticket_id | uuid | Unique ticket ID | PRIMARY KEY |
| customer_id | text | Customer identifier | |
| created_at | timestamp | Ticket creation time | |
| ticket_type | text | Type of issue | |
| description | text | Ticket description | |
| sentiment | text | Sentiment (positive/neutral/negative) | |
| status | text | Ticket status | |

**Current Data Volume:**
- customer_events: 141 events
- support_tickets: 50 tickets
- Disk usage: < 1 MB
- Write performance: ~10,000 writes/second (theoretical)

**Cassandra Design Rationale:**
- Wide-column structure optimized for time-series queries
- Partition by customer_id for efficient customer-level retrieval
- Clustering by event_time for chronological ordering
- No joins needed (denormalized design)
- Horizontal scalability for future growth

#### 3.2.3 File System Storage

**Purpose:** Store model artifacts, raw data files, and processed datasets  
**Location:** `/home/churn/churnguard-platform/data/`  

**Directory Structure:**
```
data/
├── raw/                          # Original source files
│   └── telco_churn.csv          # IBM dataset (955 KB)
│
├── processed/                    # Cleaned and feature-engineered data
│   ├── processed_churn_data.csv # ML-ready dataset (7043 rows × 59 cols)
│   ├── feature_list.txt         # List of 57 feature names
│   └── data_statistics.csv      # Descriptive statistics
│
└── models/                       # Trained ML models
    ├── logistic_regression_model.pkl  # Best model (80.3% accuracy)
    ├── scaler.pkl                     # StandardScaler for features
    ├── feature_names.pkl              # Feature names list
    └── model_metrics.txt              # Performance metrics
```

---

### 3.3 Data Ingestion Layer

#### 3.3.1 Batch Ingestion

**Component:** `src/ingest.py`  
**Purpose:** Load historical data from files into databases  
**Supported Formats:** CSV, JSON, XML  

**Batch Ingestion Flow:**
```
CSV File (Customers)
    ↓
pandas.read_csv()
    ↓
Data Validation
    ↓
psycopg2.executemany()
    ↓
PostgreSQL (customers table)
```

**Performance:**
- Throughput: 10,000+ rows/minute
- Error Handling: Skip invalid rows, log errors
- Idempotency: ON CONFLICT DO NOTHING (PostgreSQL)

**Example Usage:**
```bash
python src/ingest.py --batch data/raw/telco_churn.csv
python src/ingest.py --events 100
python src/ingest.py --tickets 50
```

#### 3.3.2 Streaming Ingestion

**Component:** Apache Kafka  
**Version:** 7.5.0 (Confluent Platform)  
**Zookeeper:** 7.5.0 (required for Kafka broker coordination)  

**Kafka Architecture:**
```
Producer (src/kafka_producer.py)
    ↓
Kafka Broker (localhost:9092)
    ↓ Topic: customer-events
Consumer (src/kafka_consumer.py)
    ↓
Cassandra (customer_events table)
```

**Kafka Topics:**

| Topic | Partitions | Replication Factor | Purpose |
|-------|------------|-------------------|---------|
| customer-events | 1 | 1 | Customer behavioral events |
| churn-predictions | 1 | 1 | Real-time predictions (future) |

**Event Schema (JSON):**
```json
{
  "customer_id": "7590-VHVEG",
  "event_type": "payment_failed",
  "timestamp": "2025-11-29T14:23:45",
  "event_data": {
    "risk_impact": 0.3,
    "source": "kafka_simulator",
    "details": "Payment declined"
  }
}
```

**Producer Configuration:**
- Serialization: JSON
- Acknowledgments: 1 (leader only)
- Retries: 3
- Batch size: 16384 bytes

**Consumer Configuration:**
- Group ID: churn-consumer-group
- Auto offset reset: earliest
- Enable auto commit: true
- Deserialization: JSON

**Performance:**
- Latency: < 5 seconds (producer → consumer → database)
- Throughput: 1,000+ events/second (tested)
- Fault tolerance: Consumer offset tracking for exactly-once processing

---

### 3.4 Processing & Analytics Layer

#### 3.4.1 ETL Pipeline

**Component:** `src/process.py`  
**Purpose:** Extract, Transform, Load data for ML model training  
**Execution:** On-demand or scheduled (cron job)  

**ETL Flow:**
```
Step 1: EXTRACT
    PostgreSQL (customers) → pandas DataFrame
    Cassandra (events) → pandas DataFrame
    Cassandra (tickets) → pandas DataFrame

Step 2: TRANSFORM
    2a. Data Cleaning
        - Handle missing values (imputation)
        - Type conversions (string → numeric)
        - Outlier detection and removal
    
    2b. Feature Engineering
        - Tenure grouping (0-1yr, 1-2yr, etc.)
        - Service counts (total_services)
        - Risk scores (contract_risk, payment_risk)
        - RFM-like metrics (avg_monthly_revenue)
        - Behavioral flags (has_family, has_internet)
    
    2c. Event Aggregation
        - total_events (count by customer)
        - payment_fail_rate
        - support_frequency
        - sentiment_score
    
    2d. Categorical Encoding
        - Binary encoding (Yes/No → 1/0)
        - One-hot encoding (contract, payment_method, etc.)
        - Drop first category (avoid multicollinearity)

Step 3: LOAD
    Save to: data/processed/processed_churn_data.csv
    Features: 57 columns (55 features + customer_id + churn)
```

**Feature Engineering Details:**

**Engineered Features (8 custom features):**

| Feature | Type | Description | Calculation |
|---------|------|-------------|-------------|
| tenure_group | Categorical | Customer tenure category | pd.cut(tenure, bins=[0,12,24,48,72]) |
| total_services | Numeric | Count of services subscribed | Sum of Yes in service columns |
| charges_category | Categorical | Monthly charges tier | pd.cut(monthly_charges, bins=[0,30,60,90,150]) |
| contract_risk | Numeric | Contract churn risk | Month-to-month:1.0, 1yr:0.5, 2yr:0.2 |
| payment_risk | Numeric | Payment method risk | E-check:1.0, Mail:0.7, Auto:0.3 |
| avg_monthly_revenue | Numeric | Average monthly $ | total_charges / (tenure + 1) |
| has_family | Binary | Partner or dependents | (partner==Yes) OR (dependents==Yes) |
| has_internet | Binary | Has internet service | internet_service != No |

**Aggregated Features from Cassandra (5 features):**

| Feature | Source | Calculation |
|---------|--------|-------------|
| total_events | customer_events | COUNT(*) GROUP BY customer_id |
| payment_fail_rate | customer_events | payment_failed / total_events |
| support_frequency | customer_events | support_call / total_events |
| total_tickets | support_tickets | COUNT(*) GROUP BY customer_id |
| sentiment_score | support_tickets | (positive - negative) / total_tickets |

**One-Hot Encoded Features (~44 features):**
- contract (2 dummy variables)
- payment_method (3 dummy variables)
- internet_service (2 dummy variables)
- multiple_lines, online_security, online_backup, etc. (2-3 dummy variables each)
- tenure_group (3 dummy variables)
- charges_category (3 dummy variables)

**Performance:**
- Execution time: ~1-2 seconds for 7,043 customers
- Memory usage: < 500 MB
- Output size: ~1.5 MB (processed CSV)

#### 3.4.2 NLP Pipeline

**Components:** TextBlob, NLTK  
**Purpose:** Extract sentiment and topics from unstructured support text  
**Processing Steps:**
```
Support Ticket Text
    ↓
Text Preprocessing
    - Lowercasing
    - Remove special characters
    - Tokenization
    ↓
Sentiment Analysis (TextBlob)
    - Polarity score: -1 to +1
    - Classification: negative, neutral, positive
    ↓
Feature Extraction
    - sentiment_score per customer
    - negative_ticket_count
    - positive_ticket_count
```

**Example:**
```python
from textblob import TextBlob

text = "Very frustrated with slow internet service"
blob = TextBlob(text)
polarity = blob.sentiment.polarity  # -0.7 (negative)
sentiment = 'negative' if polarity < -0.1 else 'positive' if polarity > 0.1 else 'neutral'
```

**Future Enhancements:**
- Topic modeling (LDA) to identify common complaint themes
- Named Entity Recognition (NER) to extract product names, issue types
- BERT-based sentiment for better accuracy

---

### 3.5 Machine Learning Layer

#### 3.5.1 Model Training Pipeline

**Component:** `notebooks/03_model_training.ipynb`, `src/train.py`  
**Framework:** Scikit-learn, XGBoost  
**Execution Environment:** Jupyter Notebook (development), Python script (production)  

**Training Pipeline Flow:**
```
Step 1: Load Processed Data
    data/processed/processed_churn_data.csv
        ↓
    7,043 rows × 59 columns

Step 2: Train/Test Split
    Stratified split (80/20)
        ↓
    Train: 5,634 samples
    Test: 1,409 samples

Step 3: Handle Class Imbalance
    SMOTE (Synthetic Minority Over-sampling)
        ↓
    Balanced training set: ~11,000 samples (50/50 split)

Step 4: Feature Scaling
    StandardScaler (mean=0, std=1)
        ↓
    Fit on training data, transform both train and test

Step 5: Model Training
    Train 3 models in parallel:
        - Logistic Regression
        - Random Forest (100 trees)
        - XGBoost (100 trees)
    
    Hyperparameters:
        - LogReg: max_iter=1000, random_state=42
        - RandomForest: n_estimators=100, random_state=42
        - XGBoost: n_estimators=100, eval_metric='logloss'

Step 6: Model Evaluation
    Test set predictions
        ↓
    Metrics: Accuracy, Precision, Recall, F1, ROC-AUC
        ↓
    Select best model (highest ROC-AUC)

Step 7: Model Persistence
    Save best model, scaler, feature names
        ↓
    data/models/*.pkl files
```

**Model Comparison Results:**

| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Training Time |
|-------|----------|-----------|--------|----------|---------|---------------|
| **Logistic Regression** | **80.3%** | **78.1%** | **75.4%** | **0.77** | **0.85** | **0.5s** |
| Random Forest | 79.8% | 76.5% | 74.2% | 0.75 | 0.83 | 12.3s |
| XGBoost | 80.1% | 77.3% | 75.0% | 0.76 | 0.84 | 3.2s |

**Winner:** Logistic Regression (selected for simplicity and interpretability)

**Model Artifacts:**

| File | Size | Purpose |
|------|------|---------|
| logistic_regression_model.pkl | ~5 KB | Trained model object |
| scaler.pkl | ~3 KB | StandardScaler fitted on training data |
| feature_names.pkl | ~2 KB | List of 57 feature names in correct order |
| model_metrics.txt | ~1 KB | Performance metrics and metadata |

#### 3.5.2 Model Inference

**Component:** `src/predict.py`  
**Purpose:** Make predictions on new customers  
**Input:** Customer ID or customer data dictionary  
**Output:** Churn probability (0-1), risk level (LOW/MEDIUM/HIGH)  

**Inference Flow:**
```
Customer ID
    ↓
Query PostgreSQL for customer data
    ↓
Preprocess customer (same as training)
    - Feature engineering
    - Categorical encoding
    - Align with 57 training features
    ↓
Scale features (using saved scaler)
    ↓
Model prediction
    - Probability: model.predict_proba()
    - Binary: model.predict()
    ↓
Risk classification
    - HIGH: probability > 70%
    - MEDIUM: 40% < probability ≤ 70%
    - LOW: probability ≤ 40%
    ↓
Return result
```

**Performance:**
- Latency: < 200ms per prediction
- Batch throughput: 100+ predictions/second
- Memory: < 100 MB

**Example Usage:**
```bash
python src/predict.py --customer 7590-VHVEG
```

**Output:**
```
🔮 Making prediction for customer: 7590-VHVEG
✓ Customer data retrieved
✓ Data preprocessed (57 features)

📊 PREDICTION RESULTS
Customer ID: 7590-VHVEG
Churn Prediction: WILL CHURN
Churn Probability: 82.3%
Risk Level: HIGH
```

---

### 3.6 Streaming Analytics Layer

**Component:** `src/kafka_consumer.py`  
**Purpose:** Process real-time events and update churn predictions  

**Real-Time Processing Flow:**
```
Kafka Topic: customer-events
    ↓
Consumer polls for new messages
    ↓
Deserialize JSON event
    ↓
Store event in Cassandra (customer_events table)
    ↓
(Optional) Trigger re-prediction if significant event
    - payment_failed
    - support_complaint
    - service_downgrade
    ↓
Update customer risk score
```

**Event Processing Performance:**
- Throughput: 1,000+ events/second
- Latency: < 5 seconds (end-to-end)
- Fault tolerance: Consumer offset management

**Future Enhancement:**
- Real-time feature extraction from event stream
- Incremental model updates (online learning)
- Alert notifications (email, Slack) for HIGH risk customers

---

### 3.7 Application Layer

#### 3.7.1 REST API (FastAPI)

**Component:** `src/api.py`  
**Framework:** FastAPI 0.104.1  
**Server:** Uvicorn (ASGI server)  
**Port:** 8000  
**Documentation:** Auto-generated OpenAPI (Swagger UI)  

**API Endpoints:**

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | / | API root | None | Welcome message, endpoint list |
| GET | /health | Health check | None | {status, timestamp, model_loaded} |
| GET | /predict/{customer_id} | Single prediction | customer_id (path param) | {customer_id, prediction, churn_probability, risk_level, timestamp} |
| POST | /predict/batch | Batch prediction | {customer_ids: ["id1", "id2"]} | [{...}, {...}] |
| GET | /customers/high-risk | High-risk customers | limit (query param) | [{customer_id, churn_probability, ...}] |
| GET | /stats | Database statistics | None | {total_customers, churned, churn_rate, ...} |

**API Features:**
- CORS enabled (allow all origins for development)
- JSON request/response format
- Error handling with HTTP status codes
- Request validation via Pydantic models
- Auto-generated documentation at `/docs`

**Example API Call:**
```bash
curl -X GET "http://localhost:8000/predict/7590-VHVEG"
```

**Response:**
```json
{
  "customer_id": "7590-VHVEG",
  "prediction": 1,
  "churn_probability": 0.823,
  "risk_level": "HIGH",
  "timestamp": "2025-11-29T14:30:00"
}
```

**Performance:**
- Latency (p50): < 200ms
- Latency (p95): < 500ms
- Throughput: 50+ requests/second (single instance)

#### 3.7.2 Web Dashboard (Streamlit)

**Component:** `dashboard/app.py`  
**Framework:** Streamlit 1.29.0  
**Visualization:** Plotly Express  
**Port:** 8501  

**Dashboard Architecture:**
