# ChurnGuard Platform - Quick Start Guide

## 🚀 Starting Everything from Scratch

### Step 1: Start VM and Login
1. Open VirtualBox
2. Select "ChurnGuard-Platform" VM
3. Click "Start"
4. Login with your credentials

---

### Step 2: Navigate to Project
```bash
cd ~/churnguard-platform
source venv/bin/activate
```

**Verify:** You should see `(venv)` in your prompt

---

### Step 3: Start Docker Services
```bash
docker compose up -d
```

**Wait 30 seconds for services to initialize**

**Verify all services are running:**
```bash
docker compose ps
```

**Expected:** 8 containers running:
- postgres, cassandra, kafka, zookeeper
- namenode, datanode (HDFS)
- spark-master, spark-worker (Spark)

---

### Step 4: Test Database Connections
```bash
# Test PostgreSQL
python src/db_postgres.py --test

# Test Cassandra
python src/db_cassandra.py --test

# Test HDFS
python src/db_hdfs.py --test
```

**Expected:** All should show "✓ Connected"

---

## 📊 Running the Dashboard

### Option 1: Dashboard Only (Recommended for Demo)
```bash
cd ~/churnguard-platform/dashboard
streamlit run app.py
```

**Access in browser:** http://localhost:8501

**Dashboard Pages:**
- 🏠 Overview - Key metrics and business impact
- 🔍 Customer Lookup - Predict churn for individual customers
- ⚠️ High-Risk Customers - Find customers likely to churn
- 📈 Analytics - Data visualizations and trends
- 📤 Upload & Process - Upload new CSV files, process data, train models, and generate insights

---

### Option 2: API Server
```bash
cd ~/churnguard-platform
python src/api.py
```

**Access API docs:** http://localhost:8000/docs

**Test endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Predict single customer
curl http://localhost:8000/predict/7590-VHVEG

# Get statistics
curl http://localhost:8000/stats
```

---

## 🧪 Testing Individual Components

### Test Prediction Script
```bash
cd ~/churnguard-platform
python src/predict.py --customer 7590-VHVEG
```

**Expected:** Shows churn probability and risk level

---

### Test Kafka Streaming
**Terminal 1 - Start Consumer:**
```bash
cd ~/churnguard-platform
python src/kafka_consumer.py
```

**Terminal 2 - Start Producer:**
```bash
cd ~/churnguard-platform
python src/kafka_producer.py --continuous --interval 3
```

**Expected:** See events flowing from producer to consumer

**Stop both:** Press `Ctrl + C` in each terminal

---

### Verify Data in Databases
```bash
cd ~/churnguard-platform
python src/verify_data.py
```

**Expected:** Shows counts for all data:
- PostgreSQL: ~7,043 customers
- Cassandra: ~141 events, ~50 tickets

---

## 📓 Opening Jupyter Notebooks
```bash
cd ~/churnguard-platform
jupyter notebook --no-browser --ip=0.0.0.0 --port=8888
```

**Copy the token URL and paste in browser**

**Navigate to notebooks folder and open:**
- `01_eda.ipynb` - Exploratory Data Analysis
- `03_model_training.ipynb` - ML Model Training

**To stop Jupyter:** Press `Ctrl + C` twice in terminal

---

## 🔄 Reprocessing Data (if needed)

### Re-run Data Processing Pipeline

**Option 1: Using Spark (Distributed Processing)**
```bash
cd ~/churnguard-platform
python src/process_spark.py --run
```

**This:**
- Processes data using Spark cluster
- Saves to HDFS (Parquet format)
- Also saves local CSV for compatibility

**Option 2: Using Pandas (Traditional)**
```bash
cd ~/churnguard-platform
python src/process.py --run
```

**This regenerates:** `data/processed/processed_churn_data.csv`

---

### Re-ingest Data (if databases were reset)
```bash
# Load customer data into PostgreSQL
python src/ingest.py --batch data/raw/telco_churn.csv

# Upload dataset to HDFS
python src/ingest_hdfs.py --upload

# Load events into Cassandra
python src/ingest.py --events 100

# Load tickets into Cassandra
python src/ingest.py --tickets 50
```

---

## 🛑 Stopping Everything

### Stop Dashboard/API
- Press `Ctrl + C` in the terminal where it's running

### Stop Docker Services
```bash
cd ~/churnguard-platform
docker compose down
```

### Stop VM
- In VirtualBox: Right-click VM → Close → Power Off
- Or from inside VM: `sudo poweroff`

---

## 🐛 Troubleshooting

### Dashboard won't start
```bash
# Make sure you're in the dashboard directory
cd ~/churnguard-platform/dashboard

# Check if port 8501 is already in use
lsof -i :8501

# If something is using it, kill it:
kill -9 <PID>

# Restart dashboard
streamlit run app.py
```

### API won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill if needed
kill -9 <PID>

# Restart API
cd ~/churnguard-platform
python src/api.py
```

### Docker services won't start
```bash
# Check Docker status
docker --version
docker compose version

# Restart Docker services
docker compose down
docker compose up -d

# Check logs if issues persist
docker compose logs postgres
docker compose logs cassandra
docker compose logs kafka
```

### Database connection errors
```bash
# Wait 60 seconds (Cassandra takes time to start)
sleep 60

# Test again
python src/db_postgres.py --test
python src/db_cassandra.py --test

# Check Docker logs
docker compose logs cassandra
```

### Model not found errors
```bash
# Verify model files exist
ls -lh data/models/

# Should see:
# - logistic_regression_model.pkl
# - scaler.pkl
# - feature_names.pkl
# - model_metrics.txt

# If missing, retrain:
# Open Jupyter and run 03_model_training.ipynb
```

---

## 📋 Pre-Demo Checklist

**15 minutes before demo:**

- [ ] Start VM
- [ ] Start Docker services: `docker compose up -d`
- [ ] Wait 30 seconds
- [ ] Verify services: `docker compose ps`
- [ ] Start dashboard: `cd dashboard && streamlit run app.py`
- [ ] Test customer lookup with ID: `7590-VHVEG`
- [ ] Check all 4 dashboard pages work
- [ ] Have backup: Screenshot dashboard in case of issues
- [ ] Optional: Have Jupyter notebooks ready in background tabs

**Browser tabs to have open:**
1. Dashboard: http://localhost:8501
2. API docs (optional): http://localhost:8000/docs
3. Jupyter (optional): http://localhost:8888

---

## 🎯 Quick Demo Script (5 minutes)

### Part 1: Overview (1 min)
"This is ChurnGuard Analytics - a big data platform for predicting customer churn."

**Show:** Dashboard overview page
- Point out: 7,043 customers, churn rate, business impact

### Part 2: Live Prediction (2 min)
"Let me demonstrate a real-time churn prediction."

**Steps:**
1. Click "Customer Lookup"
2. Enter: `7590-VHVEG`
3. Click "Predict Churn"
4. Point out: Churn probability, risk gauge, recommendations

### Part 3: Analytics (1 min)
"The platform provides comprehensive analytics."

**Show:** Analytics page
- Scroll through 4 visualizations
- Explain: "We can see churn patterns by contract type, tenure, etc."

### Part 4: Architecture (1 min)
"Under the hood, this platform uses:"
- PostgreSQL for structured customer data
- Cassandra for time-series events
- Kafka for real-time streaming
- Machine learning with 80%+ accuracy

**Show:** Terminal with `docker compose ps` to show all services

---

## 📁 Important File Locations
```
churnguard-platform/
├── data/
│   ├── models/              # Trained ML models
│   ├── processed/           # Processed datasets
│   └── raw/                 # Original CSV
│
├── notebooks/               # Jupyter notebooks
│   ├── 01_eda.ipynb
│   └── 03_model_training.ipynb
│
├── src/                     # All Python scripts
│   ├── api.py              # FastAPI server
│   ├── predict.py          # Prediction service
│   ├── process.py          # Data processing (Pandas)
│   ├── process_spark.py    # Data processing (Spark)
│   ├── train_spark.py      # ML training (Spark MLlib)
│   ├── db_hdfs.py          # HDFS handler
│   ├── ingest_hdfs.py      # HDFS ingestion
│   ├── kafka_producer.py   # Event producer
│   └── kafka_consumer.py   # Event consumer
│
├── dashboard/              # Streamlit dashboard
│   └── app.py
│
├── docs/                   # Documentation
│
├── docker-compose.yml      # Docker services config
├── requirements.txt        # Python dependencies
└── README.md              # Main documentation
```

## 🌐 Web UIs

**Access these in your browser:**
- **HDFS NameNode UI:** http://localhost:9870
- **HDFS DataNode UI:** http://localhost:9864
- **Spark Master UI:** http://localhost:8080
- **Spark Worker UI:** http://localhost:8081
- **Dashboard:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

---

## 🔗 Useful Commands Reference

### Docker
```bash
docker compose up -d          # Start all services
docker compose down           # Stop all services
docker compose ps             # Check service status
docker compose logs <service> # View logs
docker compose restart <service> # Restart a service
```

### Python Environment
```bash
source venv/bin/activate     # Activate virtual environment
deactivate                   # Deactivate virtual environment
pip list                     # List installed packages
```

### Database
```bash
python src/db_postgres.py --test   # Test PostgreSQL
python src/db_cassandra.py --test  # Test Cassandra
python src/db_hdfs.py --test       # Test HDFS
python src/verify_data.py          # Check all data
```

### Spark & HDFS
```bash
# Process data with Spark
python src/process_spark.py --run

# Train models with Spark MLlib
python src/train_spark.py --run

# Upload data to HDFS
python src/ingest_hdfs.py --upload

# List HDFS files
python src/db_hdfs.py --list /churnguard/data/raw
```

### Prediction
```bash
python src/predict.py --customer <ID>  # Single prediction
python src/predict.py --batch <ID1> <ID2> # Batch prediction
```

---

## 🆘 Emergency Commands

### If everything is broken:
```bash
# Nuclear option - restart everything
cd ~/churnguard-platform
docker compose down
docker compose up -d
sleep 60
source venv/bin/activate
cd dashboard
streamlit run app.py
```

### If VM is slow:
```bash
# Check resources
free -h              # Memory usage
df -h                # Disk usage
docker stats         # Docker container resources
```

### If you need to start fresh:
```bash
# WARNING: This deletes all data!
docker compose down -v  # Remove volumes
docker compose up -d    # Restart fresh
# Then re-run all ingestion scripts
```

---

## 📧 Support

**Before demo day:**
- Test everything at least once
- Take screenshots as backup
- Have this guide open in a tab
- Know where your model files are

**During demo:**
- If live demo fails, show screenshots
- Explain architecture from memory
- Show code in text editor as backup

---

**Created:** November 2025  
**Platform Version:** 1.0  
**Status:** Production Ready ✅
