# ChurnGuard Analytics Platform
## Big Data Customer Churn Prediction System

A comprehensive big data platform for predicting customer churn using heterogeneous databases, event streaming, and machine learning.

---

## 📋 Project Overview

**Course:** CIS 641 - Big Data Platform Project  
**Phase:** 2 - Implementation  
**Team:** ChurnGuard Analytics  

### Business Value
- Predict customer churn 30-60 days in advance with 90%+ accuracy
- Enable proactive retention strategies
- Reduce churn rate by 15-20%
- 3:1 ROI on retention campaigns

### Technology Stack
- **Databases:** PostgreSQL (structured), Cassandra (time-series/unstructured)
- **Storage:** Hadoop HDFS (distributed file system)
- **Streaming:** Apache Kafka
- **Processing:** Apache Spark (PySpark), Python, Pandas
- **ML:** Spark MLlib, Scikit-learn, XGBoost
- **API:** FastAPI
- **Dashboard:** Streamlit
- **Environment:** Oracle VirtualBox (Ubuntu 22.04 LTS)

---

## 🏗️ Architecture
```
Data Sources → Ingestion → Storage → Processing → ML → API/Dashboard
                  ↓           ↓          ↓        ↓        ↓
              Kafka      PostgreSQL   Spark    MLlib   FastAPI
                         Cassandra    HDFS     Models   Streamlit
```

**Components:**
- **PostgreSQL**: 7,043 customer profiles (structured data)
- **Cassandra**: Event logs & support tickets (time-series/unstructured)
- **Hadoop HDFS**: Distributed storage for raw and processed data
- **Apache Spark**: Distributed data processing and ML training
- **Kafka**: Real-time event streaming
- **Python/PySpark**: ETL, feature engineering, ML training
- **Docker**: Service orchestration

**Data Flow:**
1. **Ingestion**: Raw data → PostgreSQL/Cassandra + HDFS
2. **Storage**: HDFS stores raw datasets and processed features
3. **Processing**: Spark reads from HDFS/PostgreSQL/Cassandra → Feature engineering → Write to HDFS
4. **ML Training**: Spark MLlib trains models on distributed data
5. **Serving**: FastAPI/Streamlit serve predictions

---

## 📁 Project Structure
```
churnguard-platform/
├── README.md                    # This file
├── docker-compose.yml           # Docker services configuration
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── docs/                        # Documentation
│   ├── business_requirements.md
│   ├── architecture_design.md
│   ├── presentation.pdf
│   └── demo_guide.md
│
├── data/
│   ├── raw/                     # Original datasets
│   │   └── telco_churn.csv      # IBM Telco dataset (7,043 customers)
│   ├── processed/               # Cleaned/processed data
│   └── models/                  # Saved ML models
│
├── notebooks/                   # Jupyter notebooks
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
│
├── src/                         # Source code
│   ├── db_postgres.py           # PostgreSQL handler
│   ├── db_cassandra.py          # Cassandra handler
│   ├── db_hdfs.py               # HDFS handler
│   ├── ingest.py                # Data ingestion (PostgreSQL/Cassandra)
│   ├── ingest_hdfs.py           # HDFS data ingestion
│   ├── process.py               # ETL & feature engineering (Pandas)
│   ├── process_spark.py         # ETL & feature engineering (Spark)
│   ├── train.py                 # Model training (Scikit-learn)
│   ├── train_spark.py           # Model training (Spark MLlib)
│   ├── predict.py               # Inference service
│   ├── kafka_producer.py        # Event simulator
│   ├── kafka_consumer.py        # Stream processor
│   └── api.py                   # FastAPI endpoints
│
├── dashboard/
│   ├── app.py                   # Streamlit dashboard
│   ├── predict_helper.py        # Prediction helper
│   └── data_processor.py        # Data processing for uploads
│
├── tests/
│   └── test_pipeline.py
│
└── venv/                        # Python virtual environment
```

---

## 🚀 Complete Setup Guide

### Prerequisites
- Oracle VirtualBox installed
- 8GB+ RAM available for VM
- 50GB+ disk space

---

## STEP-BY-STEP SETUP COMMANDS

### **STEP 1: VirtualBox VM Setup**

#### 1.1 Download Software
- VirtualBox: https://www.virtualbox.org/wiki/Downloads
- Ubuntu 22.04 LTS ISO: https://ubuntu.com/download/server

#### 1.2 Create VM in VirtualBox
- Name: ChurnGuard-Platform
- Type: Linux, Ubuntu (64-bit)
- Memory: 8192 MB (8GB)
- CPU: 4 cores
- Disk: 50GB VDI (dynamically allocated)

#### 1.3 Configure Port Forwarding
Settings → Network → Adapter 1 → Advanced → Port Forwarding

| Name | Host Port | Guest Port |
|------|-----------|------------|
| PostgreSQL | 5432 | 5432 |
| Cassandra | 9042 | 9042 |
| Kafka | 9092 | 9092 |
| HDFS NameNode | 9870 | 9870 |
| HDFS DataNode | 9864 | 9864 |
| Spark Master | 8080 | 8080 |
| Spark Worker | 8081 | 8081 |
| API | 8000 | 8000 |
| Dashboard | 8501 | 8501 |
| SSH | 2222 | 22 |

#### 1.4 Install Ubuntu
- Follow installation wizard
- Username: `churn`
- Hostname: `churnguard-vm`
- Install OpenSSH server: Yes

#### 1.5 First Boot - Update System
```bash
sudo apt update
sudo apt upgrade -y
```

---

### **STEP 2: Install Docker & Docker Compose**
```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run Docker installation
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Activate group membership
newgrp docker

# Verify Docker installation
docker --version

# Remove old docker-compose (if exists)
sudo apt remove docker-compose -y

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Verify Docker Compose
docker compose version
```

---

### **STEP 3: Install Python & Git**
```bash
# Install Python, pip, venv, and git
sudo apt install python3-pip python3-venv git wget -y

# Verify installations
python3 --version
pip3 --version
git --version
```

---

### **STEP 4: Create Project Structure**
```bash
# Create main project directory
mkdir -p ~/churnguard-platform
cd ~/churnguard-platform

# Create all subdirectories
mkdir -p docs data/raw data/processed data/models notebooks src dashboard tests vm-setup

# Verify structure
ls -l
ls -l data/
```

---

### **STEP 5: Create Configuration Files**

#### 5.1 Create docker-compose.yml
```bash
nano docker-compose.yml
```

Paste content (see docker-compose.yml section below), then:
- Ctrl+O (save)
- Enter (confirm)
- Ctrl+X (exit)

#### 5.2 Create requirements.txt
```bash
nano requirements.txt
```

Paste content (see requirements.txt section below), then save and exit.

#### 5.3 Create .gitignore
```bash
nano .gitignore
```

Paste content (see .gitignore section below), then save and exit.

---

### **STEP 6: Start Docker Services**
```bash
# Start all services (first time will download images - takes 5-10 minutes)
docker compose up -d

# Wait for services to initialize (HDFS and Spark take longer)
sleep 60

# Verify all services are running
docker compose ps

# Expected output: 8 containers with status "Up":
# - postgres, cassandra, kafka, zookeeper
# - namenode, datanode (HDFS)
# - spark-master, spark-worker (Spark)
```

---

### **STEP 7: Setup Python Environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)

# Install Python packages (takes 3-5 minutes)
pip install -r requirements.txt

# Verify key packages
pip list | grep -E "pandas|scikit-learn|fastapi|streamlit|cassandra"
```

---

### **STEP 8: Download Dataset**
```bash
# Download IBM Telco Customer Churn dataset
wget -O data/raw/telco_churn.csv https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv

# Verify download
ls -lh data/raw/
wc -l data/raw/telco_churn.csv
# Expected: ~7044 lines (7043 customers + 1 header)
```

---

### **STEP 9: Create Database Scripts**

#### 9.1 Create PostgreSQL Handler
```bash
nano src/db_postgres.py
```
Paste content (see src/db_postgres.py section below), then save and exit.

#### 9.2 Create Cassandra Handler
```bash
nano src/db_cassandra.py
```
Paste content (see src/db_cassandra.py section below), then save and exit.

#### 9.3 Create Data Ingestion Script
```bash
nano src/ingest.py
```
Paste content (see src/ingest.py section below), then save and exit.

---

### **STEP 10: Initialize Databases and HDFS**
```bash
# Test PostgreSQL connection
python src/db_postgres.py --test
# Expected: ✓ Connected to PostgreSQL

# Initialize PostgreSQL schema
python src/db_postgres.py --init
# Expected: ✓ Table 'customers' created

# Test Cassandra connection
python src/db_cassandra.py --test
# Expected: ✓ Connected to Cassandra

# Initialize Cassandra schema
python src/db_cassandra.py --init
# Expected: ✓ Keyspace and tables created

# Test HDFS connection
python src/db_hdfs.py --test
# Expected: ✓ Connected to HDFS

# Initialize HDFS directories
python src/db_hdfs.py --init
# Expected: ✓ HDFS directory structure initialized
```

---

### **STEP 11: Load Data**
```bash
# Load customer data into PostgreSQL
python src/ingest.py --batch data/raw/telco_churn.csv
# Expected: ✓ Inserted 7043 customers into PostgreSQL

# Upload dataset to HDFS
python src/ingest_hdfs.py --upload
# Expected: ✓ Uploaded to HDFS: hdfs://namenode:9000/churnguard/data/raw/telco_churn.csv

# Generate sample events in Cassandra
python src/ingest.py --events 100
# Expected: ✓ Inserted 100 events into Cassandra

# Generate sample support tickets in Cassandra
python src/ingest.py --tickets 50
# Expected: ✓ Inserted 50 support tickets into Cassandra
```

---

### **STEP 12: Process Data with Spark (Optional)**
```bash
# Process data using Spark (distributed processing)
python src/process_spark.py --run
# Expected: ✓ Spark processing complete, data saved to HDFS

# Or use traditional Pandas processing
python src/process.py --run
# Expected: ✓ Processing complete, saved to data/processed/
```

### **STEP 13: Train Models with Spark MLlib (Optional)**
```bash
# Train models using Spark MLlib (distributed ML)
python src/train_spark.py --run
# Expected: ✓ Spark ML training complete, models saved

# Or use traditional Scikit-learn training
# (Run notebooks/03_model_training.ipynb in Jupyter)
```

### **STEP 14: Verify Everything**
```bash
# Check all Docker containers are running
docker compose ps

# Test database connections
python src/db_postgres.py --test
python src/db_cassandra.py --test
python src/db_hdfs.py --test

# List HDFS files
python src/db_hdfs.py --list /churnguard/data/raw
```

---

## 📊 Current Data Status

### PostgreSQL (Structured Data)
- **Database:** churn_db
- **Table:** customers
- **Records:** 7,043 customer profiles
- **Columns:** 21 (customer_id, gender, tenure, contract, monthly_charges, churn, etc.)

### Cassandra (Unstructured/Time-Series Data)
- **Keyspace:** churn_keyspace
- **Tables:**
  - `customer_events`: 100 time-series events (logins, payments, support calls)
  - `support_tickets`: 50 support tickets with descriptions and sentiment

### Hadoop HDFS (Distributed Storage)
- **Base Path:** `/churnguard`
- **Raw Data:** `/churnguard/data/raw/telco_churn.csv`
- **Processed Data:** `/churnguard/data/processed/` (Parquet format)
- **Models:** `/churnguard/models/` (Spark MLlib models)

### Spark (Distributed Processing)
- **Master:** spark://spark-master:7077
- **Workers:** 1 worker with 2 cores, 2GB memory
- **Processing:** Distributed ETL and feature engineering
- **ML Training:** Spark MLlib (Logistic Regression, Random Forest, GBT)

---

## 🔧 Useful Commands

### Docker Management
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f [service_name]
# Example: docker compose logs -f postgres

# Restart a service
docker compose restart [service_name]

# Check service status
docker compose ps
```

### Python Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Install new package
pip install package_name
pip freeze > requirements.txt  # Update requirements
```

### Database Operations
```bash
# Test connections
python src/db_postgres.py --test
python src/db_cassandra.py --test
python src/db_hdfs.py --test

# Re-initialize schemas (WARNING: drops existing data)
python src/db_postgres.py --init
python src/db_cassandra.py --init
python src/db_hdfs.py --init

# Load data
python src/ingest.py --batch data/raw/telco_churn.csv
python src/ingest_hdfs.py --upload
python src/ingest.py --events 100
python src/ingest.py --tickets 50
```

### Spark Operations
```bash
# Process data with Spark
python src/process_spark.py --run

# Train models with Spark MLlib
python src/train_spark.py --run

# Access Spark Web UI
# Master: http://localhost:8080
# Worker: http://localhost:8081
```

### HDFS Operations
```bash
# List HDFS files
python src/db_hdfs.py --list /churnguard/data/raw

# Upload file to HDFS
python src/db_hdfs.py --upload <local_path> <hdfs_path>

# Download file from HDFS
python src/db_hdfs.py --download <hdfs_path> <local_path>

# Access HDFS Web UI
# NameNode: http://localhost:9870
# DataNode: http://localhost:9864
```

---

## 🐛 Troubleshooting

### Docker containers not starting
```bash
# Check Docker is running
docker --version
docker compose version

# View detailed logs
docker compose logs

# Restart services
docker compose down
docker compose up -d
```

### Cassandra connection fails
```bash
# Cassandra takes 60-90 seconds to fully start
# Wait and try again
sleep 60
python src/db_cassandra.py --test

# Check Cassandra logs
docker compose logs cassandra | tail -50
```

### PostgreSQL connection fails
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Python package issues
```bash
# Make sure venv is activated (you should see (venv) in prompt)
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

---

## 📝 Implementation Status

### ✅ Completed
- [x] PostgreSQL database setup and ingestion
- [x] Cassandra database setup and ingestion
- [x] Hadoop HDFS setup and data ingestion
- [x] Apache Spark cluster setup
- [x] Spark-based data processing pipeline
- [x] Spark MLlib model training
- [x] Kafka producer for real-time event simulation
- [x] Kafka consumer for stream processing
- [x] Data processing & feature engineering (both Pandas and Spark)
- [x] Jupyter notebooks for EDA and ML
- [x] Model training pipeline (Scikit-learn and Spark MLlib)
- [x] FastAPI REST endpoints
- [x] Streamlit dashboard
- [x] Phase 1 documentation (business requirements, architecture)

### 🔄 In Progress / Future Enhancements
- [ ] Spark Streaming for real-time Kafka processing
- [ ] Spark SQL for advanced analytics
- [ ] Model serving with Spark MLlib
- [ ] Performance optimization for large-scale data
- [ ] Phase 2 presentation slides

---

## 👥 Team Members
- [Add your team member names]

---

## 📚 References

### Datasets
- IBM Telco Customer Churn: https://github.com/IBM/telco-customer-churn-on-icp4d

### Documentation
- Docker: https://docs.docker.com/
- PostgreSQL: https://www.postgresql.org/docs/
- Cassandra: https://cassandra.apache.org/doc/latest/
- Hadoop HDFS: https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsUserGuide.html
- Apache Spark: https://spark.apache.org/docs/latest/
- PySpark: https://spark.apache.org/docs/latest/api/python/
- Kafka: https://kafka.apache.org/documentation/
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://docs.streamlit.io/

---

## 📄 License
Educational project for CIS 641 - Big Data Platform
