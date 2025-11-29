import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
from predict_helper import ChurnPredictor
import numpy as np

# Page config
st.set_page_config(
    page_title="ChurnGuard Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .high-risk {
        color: #d62728;
        font-weight: bold;
    }
    .medium-risk {
        color: #ff7f0e;
        font-weight: bold;
    }
    .low-risk {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

# Initialize predictor
@st.cache_resource
def load_predictor():
    return ChurnPredictor()

@st.cache_data
@st.cache_resource
def load_predictor():
    """Load predictor with correct paths"""
    import os
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_path, 'data/models/logistic_regression_model.pkl')
    scaler_path = os.path.join(base_path, 'data/models/scaler.pkl')
    feature_names_path = os.path.join(base_path, 'data/models/feature_names.pkl')
    
    return ChurnPredictor(
        model_path=model_path,
        scaler_path=scaler_path,
        feature_names_path=feature_names_path
    )

@st.cache_data
def get_stats():
    """Get database statistics"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customers WHERE churn = 'Yes'")
    churned = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return {
        'total': total,
        'churned': churned,
        'retained': total - churned,
        'churn_rate': churned / total if total > 0 else 0
    }

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">📊 ChurnGuard Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Predictive Customer Churn Analysis Platform")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🎛️ Navigation")
    page = st.sidebar.radio("Select Page", [
        "🏠 Overview",
        "🔍 Customer Lookup",
        "⚠️ High-Risk Customers",
        "📈 Analytics"
    ])
    
    st.sidebar.markdown("---")
    st.sidebar.info("**ChurnGuard Analytics**\n\nPredicting customer churn with machine learning")
    
    # Load data
    try:
        predictor = load_predictor()
        stats = get_stats()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()
    
    # Page routing
    if page == "🏠 Overview":
        show_overview(stats)
    elif page == "🔍 Customer Lookup":
        show_customer_lookup(predictor)
    elif page == "⚠️ High-Risk Customers":
        show_high_risk_customers(predictor)
    elif page == "📈 Analytics":
        show_analytics()

def show_overview(stats):
    """Overview page with key metrics"""
    st.header("📊 Platform Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Customers",
            value=f"{stats['total']:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Churned Customers",
            value=f"{stats['churned']:,}",
            delta=f"{stats['churn_rate']:.1%}",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="Retained Customers",
            value=f"{stats['retained']:,}",
            delta=f"{(1-stats['churn_rate']):.1%}",
            delta_color="normal"
        )
    
    with col4:
        at_risk = int(stats['total'] * 0.15)  # Estimate
        st.metric(
            label="Estimated At-Risk",
            value=f"{at_risk:,}",
            delta="15% of total"
        )
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Churn Distribution")
        fig = go.Figure(data=[go.Pie(
            labels=['Retained', 'Churned'],
            values=[stats['retained'], stats['churned']],
            hole=0.4,
            marker_colors=['#2ca02c', '#d62728']
        )])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💼 Business Impact")
        
        # Calculate impact metrics
        avg_revenue = 64.76  # Average monthly charges from dataset
        annual_revenue_loss = stats['churned'] * avg_revenue * 12
        
        st.markdown(f"""
        **Current Churn Impact:**
        - Monthly Revenue Loss: **${stats['churned'] * avg_revenue:,.2f}**
        - Annual Revenue Loss: **${annual_revenue_loss:,.2f}**
        - Customers Lost: **{stats['churned']:,}**
        
        **Potential Savings (15% reduction):**
        - Customers Saved: **{int(stats['churned'] * 0.15):,}**
        - Revenue Saved: **${annual_revenue_loss * 0.15:,.2f}/year**
        """)
    
    st.markdown("---")
    
    # Platform capabilities
    st.subheader("🚀 Platform Capabilities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📡 Real-Time Streaming**
        - Kafka event processing
        - Live churn scoring
        - Instant alerts
        """)
    
    with col2:
        st.markdown("""
        **🤖 Machine Learning**
        - 80%+ accuracy
        - 57 engineered features
        - XGBoost & Logistic Regression
        """)
    
    with col3:
        st.markdown("""
        **💾 Big Data Storage**
        - PostgreSQL: Structured data
        - Cassandra: Time-series events
        - 7,000+ customer profiles
        """)

def show_customer_lookup(predictor):
    """Customer lookup and prediction page"""
    st.header("🔍 Customer Churn Prediction")
    
    st.markdown("Enter a customer ID to get churn prediction and risk analysis.")
    
    # Input
    customer_id = st.text_input("Customer ID", value="7590-VHVEG", placeholder="e.g., 7590-VHVEG")
    
    if st.button("🔮 Predict Churn", type="primary"):
        with st.spinner("Analyzing customer data..."):
            try:
                result = predictor.predict(customer_id)
                
                if result:
                    st.success("✅ Prediction Complete!")
                    
                    # Results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Churn Probability", f"{result['churn_probability']:.1%}")
                    
                    with col2:
                        risk_color = "high-risk" if result['risk_level'] == "HIGH" else "medium-risk" if result['risk_level'] == "MEDIUM" else "low-risk"
                        st.markdown(f"**Risk Level:** <span class='{risk_color}'>{result['risk_level']}</span>", unsafe_allow_html=True)
                    
                    with col3:
                        prediction_text = "WILL CHURN ⚠️" if result['prediction'] == 1 else "WILL NOT CHURN ✅"
                        st.markdown(f"**Prediction:** {prediction_text}")
                    
                    # Risk gauge
                    st.subheader("📊 Churn Risk Gauge")
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=result['churn_probability'] * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Churn Probability (%)"},
                        delta={'reference': 50},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 40], 'color': "#2ca02c"},
                                {'range': [40, 70], 'color': "#ff7f0e"},
                                {'range': [70, 100], 'color': "#d62728"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 70
                            }
                        }
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Recommendations
                    st.subheader("💡 Recommended Actions")
                    if result['risk_level'] == "HIGH":
                        st.error("""
                        **Immediate Action Required:**
                        - Contact customer within 24 hours
                        - Offer retention incentives (discount, upgrade)
                        - Schedule account review meeting
                        - Assign to retention specialist
                        """)
                    elif result['risk_level'] == "MEDIUM":
                        st.warning("""
                        **Proactive Engagement Recommended:**
                        - Send personalized email campaign
                        - Offer service optimization consultation
                        - Monitor account activity closely
                        - Consider loyalty program enrollment
                        """)
                    else:
                        st.success("""
                        **Customer in Good Standing:**
                        - Continue regular engagement
                        - Consider upsell opportunities
                        - Maintain service quality
                        - Periodic satisfaction surveys
                        """)
                
                else:
                    st.error(f"Customer ID '{customer_id}' not found in database.")
            
            except Exception as e:
                st.error(f"Error making prediction: {e}")

def show_high_risk_customers(predictor):
    """High-risk customers page"""
    st.header("⚠️ High-Risk Customers")
    
    st.markdown("Customers with >70% churn probability requiring immediate attention.")
    
    num_customers = st.slider("Number of customers to scan", 10, 100, 50)
    
    if st.button("🔍 Find High-Risk Customers", type="primary"):
        with st.spinner(f"Scanning {num_customers} customers..."):
            try:
                # Get random customers
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute(f"SELECT customer_id FROM customers ORDER BY RANDOM() LIMIT {num_customers}")
                customer_ids = [row[0] for row in cursor.fetchall()]
                cursor.close()
                conn.close()
                
                # Predict for each
                high_risk = []
                progress_bar = st.progress(0)
                
                for i, cid in enumerate(customer_ids):
                    result = predictor.predict(cid)
                    if result and result['churn_probability'] > 0.7:
                        high_risk.append(result)
                    progress_bar.progress((i + 1) / len(customer_ids))
                
                progress_bar.empty()
                
                if high_risk:
                    st.success(f"✅ Found {len(high_risk)} high-risk customers")
                    
                    # Display as table
                    df_risk = pd.DataFrame(high_risk)
                    df_risk['churn_probability'] = df_risk['churn_probability'].apply(lambda x: f"{x:.1%}")
                    
                    st.dataframe(
                        df_risk[['customer_id', 'churn_probability', 'risk_level']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Download button
                    csv = df_risk.to_csv(index=False)
                    st.download_button(
                        label="📥 Download High-Risk List (CSV)",
                        data=csv,
                        file_name="high_risk_customers.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"No high-risk customers found in sample of {num_customers}. Try increasing the sample size.")
            
            except Exception as e:
                st.error(f"Error")

def show_analytics():
    """Analytics page with data visualizations"""
    st.header("📈 Customer Analytics")
    
    try:
        # Load customer data directly
        conn = psycopg2.connect(**DB_CONFIG)
        query = "SELECT * FROM customers LIMIT 1000"
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Churn by contract type
        st.subheader("📊 Churn Rate by Contract Type")
        churn_by_contract = df.groupby('contract')['churn'].apply(lambda x: (x == 'Yes').sum() / len(x) * 100).reset_index()
        churn_by_contract.columns = ['Contract', 'Churn Rate (%)']
        
        fig = px.bar(churn_by_contract, x='Contract', y='Churn Rate (%)', 
                     color='Churn Rate (%)', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        # Churn by tenure
        st.subheader("📊 Churn Rate by Tenure")
        df['tenure_group'] = pd.cut(df['tenure'], bins=[0, 12, 24, 48, 72], labels=['0-1yr', '1-2yr', '2-4yr', '4yr+'])
        churn_by_tenure = df.groupby('tenure_group')['churn'].apply(lambda x: (x == 'Yes').sum() / len(x) * 100).reset_index()
        churn_by_tenure.columns = ['Tenure Group', 'Churn Rate (%)']
        
        fig = px.line(churn_by_tenure, x='Tenure Group', y='Churn Rate (%)', markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly charges distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Monthly Charges Distribution")
            fig = px.histogram(df, x='monthly_charges', color='churn', 
                             barmode='overlay', nbins=30,
                             color_discrete_map={'Yes': '#d62728', 'No': '#2ca02c'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📞 Payment Method vs Churn")
            churn_by_payment = df.groupby('payment_method')['churn'].apply(lambda x: (x == 'Yes').sum() / len(x) * 100).reset_index()
            churn_by_payment.columns = ['Payment Method', 'Churn Rate (%)']
            
            fig = px.bar(churn_by_payment, x='Payment Method', y='Churn Rate (%)', 
                        color='Churn Rate (%)', color_continuous_scale='Oranges')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
