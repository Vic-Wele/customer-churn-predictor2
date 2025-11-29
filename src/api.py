from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from datetime import datetime
import sys
sys.path.append('.')
from src.predict import ChurnPredictor

# Initialize FastAPI
app = FastAPI(
    title="ChurnGuard Analytics API",
    description="Customer Churn Prediction REST API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

# Initialize predictor (global)
predictor = ChurnPredictor()

# Pydantic models
class PredictionResponse(BaseModel):
    customer_id: str
    prediction: int
    churn_probability: float
    risk_level: str
    timestamp: str

class CustomerInfo(BaseModel):
    customer_id: str
    tenure: int
    contract: str
    monthly_charges: float
    churn_probability: Optional[float] = None
    risk_level: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model_loaded: bool

# Routes
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "ChurnGuard Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict/{customer_id}",
            "batch_predict": "/predict/batch",
            "high_risk": "/customers/high-risk",
            "stats": "/stats"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": predictor.model is not None
    }

@app.get("/predict/{customer_id}", response_model=PredictionResponse, tags=["Prediction"])
async def predict_customer(customer_id: str):
    """Predict churn for a single customer"""
    try:
        result = predictor.predict(customer_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", response_model=List[PredictionResponse], tags=["Prediction"])
async def predict_batch(customer_ids: List[str]):
    """Predict churn for multiple customers"""
    try:
        results = predictor.predict_batch(customer_ids)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customers/high-risk", response_model=List[CustomerInfo], tags=["Customers"])
async def get_high_risk_customers(limit: int = 10):
    """Get list of high-risk customers (>70% churn probability)"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get random sample of customers for demo
        cursor.execute(f"""
            SELECT customer_id, tenure, contract, monthly_charges
            FROM customers
            ORDER BY RANDOM()
            LIMIT {limit * 3}
        """)
        
        customers = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Predict for each and filter high-risk
        high_risk = []
        for customer in customers:
            customer_id = customer[0]
            result = predictor.predict(customer_id)
            
            if result and result['churn_probability'] > 0.7:
                high_risk.append({
                    'customer_id': customer_id,
                    'tenure': customer[1],
                    'contract': customer[2],
                    'monthly_charges': float(customer[3]),
                    'churn_probability': result['churn_probability'],
                    'risk_level': result['risk_level']
                })
                
                if len(high_risk) >= limit:
                    break
        
        return high_risk
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """Get database statistics"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Total customers
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]
        
        # Churn distribution
        cursor.execute("SELECT churn, COUNT(*) FROM customers GROUP BY churn")
        churn_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.close()
        conn.close()
        
        return {
            "total_customers": total_customers,
            "churned": churn_dist.get('Yes', 0),
            "not_churned": churn_dist.get('No', 0),
            "churn_rate": churn_dist.get('Yes', 0) / total_customers if total_customers > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
if __name__ == "__main__":
    import uvicorn
    print(" Starting ChurnGuard Analytics API...")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
