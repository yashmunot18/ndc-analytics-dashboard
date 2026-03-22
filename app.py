import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="NDC Executive Dashboard", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .css-1d391kg { padding-top: 1rem; }
    h1, h2, h3 { color: #1e293b; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 NDC Diagnostics | Performance Dashboard")
st.write("Upload your `Final_Cleaned_NDC_Data.csv` to generate the interactive analytics.")

# ==========================================
# 2. DATA INGESTION
# ==========================================
uploaded_file = st.file_uploader("Upload Cleaned CSV", type=['csv'])

if uploaded_file:
    with st.spinner("Loading analytics engine..."):
        df = pd.read_csv(uploaded_file)
        
        # Ensure correct data types
        df['Net'] = pd.to_numeric(df['Net'], errors='coerce').fillna(0)
        df['RegnDateTime'] = pd.to_datetime(df['RegnDateTime'], errors='coerce')
        df['Date'] = df['RegnDateTime'].dt.date
        
    st.markdown("---")

    # ==========================================
    # 3. GLOBAL FILTERS (SIDEBAR)
    # ==========================================
    st.sidebar.header("Filter Analytics")
    
    # Center Filter
    centers = ['All Centers'] + sorted(df['Name'].dropna().unique().tolist())
    selected_center = st.sidebar.selectbox("Location", centers)
    
    # Category Filter
    categories = ['All Categories'] + sorted(df['Final_Category'].dropna().unique().tolist())
    selected_category = st.sidebar.selectbox("Revenue Source", categories)

    # Apply Filters
    filtered_df = df.copy()
    if selected_center != 'All Centers':
        filtered_df = filtered_df[filtered_df['Name'] == selected_center]
    if selected_category != 'All Categories':
        filtered_df = filtered_df[filtered_df['Final_Category'] == selected_category]

    # ==========================================
    # 4. KPI CARDS
    # ==========================================
    total_rev = filtered_df['Net'].sum()
    total_vol = len(filtered_df)
    yield_per_ref = total_rev / total_vol if total_vol > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"₹ {total_rev:,.0f}")
    c2.metric("Total Referral Volume", f"{total_vol:,}")
    c3.metric("Blended Yield / Referral", f"₹ {yield_per_ref:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 5. CHARTS ROW 1
    # ==========================================
    col_chart1, col_chart2 = st.columns([1, 2])
    
    with col_chart1:
        st.subheader("Revenue by Category")
        cat_df = filtered_df.groupby('Final_Category')['Net'].sum().reset_index()
        fig_pie = px.pie(cat_df, values='Net', names='Final_Category', hole=0.55, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0), showlegend=True, legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("Revenue Trend (Daily)")
        trend_df = filtered_df.groupby('Date')['Net'].sum().reset_index().sort_values('Date')
        fig_trend = px.area(trend_df, x='Date', y='Net', 
                           color_discrete_sequence=['#6366f1'])
        fig_trend.update_layout(xaxis_title="", yaxis_title="Revenue (₹)", margin=dict(t=20))
        st.plotly_chart(fig_trend, use_container_width=True)

    # ==========================================
    # 6. CHARTS ROW 2
    # ==========================================
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        st.subheader("Top 10 Referrers (Revenue)")
        ref_df = filtered_df.groupby('Final_Referrer_Name')['Net'].sum().reset_index().sort_values('Net', ascending=False).head(10)
        fig_ref = px.bar(ref_df, x='Net', y='Final_Referrer_Name', orientation='h', text_auto='.2s',
                         color_discrete_sequence=['#0ea5e9'])
        fig_ref.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_ref, use_container_width=True)

    with col_chart4:
        st.subheader("Test Mix: Top 10 Services Performed")
        # Explode the comma-separated tests to get an accurate count
        tests_series = filtered_df['TestNames'].dropna().astype(str).str.split(',').explode().str.strip().str.upper()
        tests_df = tests_series.value_counts().reset_index().head(10)
        tests_df.columns = ['TestName', 'Volume']
        
        fig_test = px.bar(tests_df, x='Volume', y='TestName', orientation='h', text_auto=True,
                          color_discrete_sequence=['#10b981'])
        fig_test.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_test, use_container_width=True)

    # ==========================================
    # 7. LEADERBOARD TABLE
    # ==========================================
    st.markdown("---")
    st.subheader("🏆 Referrer Leaderboard")
    
    table_df = filtered_df.groupby(['Final_Referrer_Name', 'Final_Category']).agg(
        Volume=('Net', 'count'),
        TotalRevenue=('Net', 'sum')
    ).reset_index()
    
    table_df['Yield (₹/Ref)'] = (table_df['TotalRevenue'] / table_df['Volume']).round(0)
    table_df = table_df.sort_values('TotalRevenue', ascending=False).reset_index(drop=True)
    
    # Currency Formatting
    display_df = table_df.copy()
    display_df['TotalRevenue'] = display_df['TotalRevenue'].apply(lambda x: f"₹ {x:,.0f}")
    display_df['Yield (₹/Ref)'] = display_df['Yield (₹/Ref)'].apply(lambda x: f"₹ {x:,.0f}")
    
    st.dataframe(display_df, use_container_width=True, height=400)

else:
    st.info("Awaiting file upload. Please drop your Cleaned CSV in the box above.")