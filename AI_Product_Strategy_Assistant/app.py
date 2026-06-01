import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Product Strategy Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .main-title {
        font-size: 2.2rem; font-weight: 800; text-align: center;
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle { text-align: center; color: #6b7280; font-size: 1rem; margin-top: 0; }
    .stTabs [data-baseweb="tab"] { font-size: 0.82rem; padding: 6px 10px; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
for key, default in [
    ("analysis_results", {}),
    ("data_context", None),
    ("df", None),
    ("summary", {}),
    ("chat_history", []),
    ("analysis_complete", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 Product Strategy AI")
    st.markdown("*9-Agent Multi-Agent Analysis System*")
    st.divider()

    st.subheader("⚙️ API Configuration")
    api_key   = st.text_input("API Key", value="learner043", type="password")
    base_url  = st.text_input("Base URL", value="https://keygateway.arshnivlabs.com")
    model_name = st.text_input("Model", value="gpt-4o-mini")

    st.divider()
    st.subheader("📁 Upload Data")
    uploaded_files = st.file_uploader(
        "CSV, PDF, or Text files",
        type=["csv", "pdf", "txt", "md"],
        accept_multiple_files=True,
        help="Sales CSVs · Market research PDFs · Competitor docs · Customer surveys",
    )
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) ready")
        for f in uploaded_files:
            icon = "📊" if f.name.endswith(".csv") else "📄"
            st.caption(f"{icon} {f.name}")

    st.divider()
    run_btn = st.button(
        "🚀 Run Full Analysis (9 Agents)",
        type="primary",
        disabled=not uploaded_files,
        use_container_width=True,
    )

    if st.session_state.analysis_complete:
        st.divider()
        st.subheader("📥 Export")
        from utils.pdf_generator import generate_pdf
        pdf_bytes = generate_pdf(st.session_state.analysis_results, st.session_state.summary)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"strategy_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.divider()
        st.subheader("🤖 Agent Status")
        all_agent_names = [
            ("👥", "Customer Feedback Agent"),
            ("📈", "Sales Analysis Agent"),
            ("🌍", "Market Research Agent"),
            ("🏆", "Competitor Analysis Agent"),
            ("🔍", "SWOT Analysis Agent"),
            ("⭐", "Feature Prioritization Agent"),
            ("💡", "Opportunity Analysis Agent"),
            ("🎯", "Strategy Recommendation Agent"),
            ("📋", "Executive Report Agent"),
        ]
        for icon, name in all_agent_names:
            done = name in st.session_state.analysis_results
            st.markdown(f"{'✅' if done else '⏳'} {icon} <small>{name}</small>", unsafe_allow_html=True)

        st.divider()
        if st.button("🔄 Reset & Start Over", use_container_width=True):
            for k in ["analysis_results", "data_context", "df", "summary",
                      "chat_history", "analysis_complete"]:
                st.session_state[k] = {} if k == "analysis_results" else (
                    [] if k == "chat_history" else (
                        False if k == "analysis_complete" else None))
            st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-title">🚀 AI-Powered Product Strategy Assistant</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">9-Agent AI System · Customer Insights · Sales · Market Research · '
    'Competitor Analysis · SWOT · Feature Priority · Opportunity Scoring · Strategy · Executive Report</p>',
    unsafe_allow_html=True,
)

# ── Run Analysis ──────────────────────────────────────────────────────────────
if run_btn and uploaded_files:
    from utils.data_processor import process_files
    from orchestrator import Orchestrator

    with st.spinner("📥 Processing uploaded files..."):
        data_context = process_files(uploaded_files)
        st.session_state.data_context = data_context
        st.session_state.df      = data_context.get("df")
        st.session_state.summary = data_context.get("summary", {})

    client       = OpenAI(api_key=api_key, base_url=base_url)
    orchestrator = Orchestrator(client, model_name)

    prog   = st.progress(0, text="Starting analysis...")
    status = st.empty()

    def on_progress(i, total, name):
        prog.progress(int(i / total * 100), text=f"🤖 Running {name}...")
        status.info(f"**Agent {i+1}/{total}:** {name} is analyzing your data...")

    results = orchestrator.run(st.session_state.data_context, progress_callback=on_progress)

    prog.progress(100, text="✅ All agents complete!")
    status.success(f"✅ All {len(results)} agents have completed their analysis!")

    st.session_state.analysis_results  = results
    st.session_state.analysis_complete = True
    st.rerun()

# ── Welcome Screen ────────────────────────────────────────────────────────────
if not st.session_state.analysis_complete:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
### 📁 Step 1: Upload Data
- Sales reports (CSV)
- Customer reviews (CSV/TXT)
- Market research (PDF)
- Competitor analysis (PDF)
- Feature requests (TXT)
- Survey responses (CSV/TXT)
        """)
    with c2:
        st.markdown("""
### 🤖 Step 2: 9 Agents Analyze
1. Customer Feedback Agent
2. Sales Analysis Agent
3. Market Research Agent
4. Competitor Analysis Agent
5. SWOT Analysis Agent
6. Feature Prioritization Agent
7. Opportunity Analysis Agent
8. Strategy Recommendation Agent
9. Executive Report Agent
        """)
    with c3:
        st.markdown("""
### 📊 Step 3: Get Insights
- 7 interactive charts
- 9 detailed reports
- Opportunity scores
- Strategic action plan
- AI chat assistant
- Downloadable PDF
        """)
    st.markdown("---")
    st.info("👆 Upload your data files in the sidebar, then click **🚀 Run Full Analysis** to begin.")
    st.markdown("**Quick start:** Upload the included `Sample Sales Data.csv` file to see the full system in action.")

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.analysis_complete:
    df      = st.session_state.df
    summary = st.session_state.summary
    results = st.session_state.analysis_results

    # KPI banner
    st.markdown("---")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("💰 Revenue",      f"${summary.get('total_revenue_usd', 0)/1e6:.2f}M")
    k2.metric("📈 Profit",       f"${summary.get('total_profit_usd', 0)/1e6:.2f}M",
              f"{summary.get('overall_profit_margin_pct', 0):.1f}% margin")
    k3.metric("📦 Units Sold",   f"{summary.get('total_units_sold', 0):,}")
    k4.metric("⭐ Avg Rating",   f"{summary.get('avg_customer_rating', 0):.1f}/5.0")
    k5.metric("↩️ Returns",      f"{summary.get('total_returns', 0):,}",
              f"{summary.get('return_rate_pct', 0):.1f}% rate")
    k6.metric("👥 New Customers",f"{summary.get('total_new_customers', 0):,}")
    st.markdown("---")

    tabs = st.tabs([
        "📊 Dashboard",
        "👥 Customer Insights",
        "📈 Sales Analysis",
        "🌍 Market Research",
        "🏆 Competitor Analysis",
        "🔍 SWOT",
        "⭐ Feature Priority",
        "💡 Opportunity Scores",
        "🎯 Strategy",
        "📋 Executive Report",
        "💬 Chat Assistant",
    ])

    # ── Tab 0: Dashboard ──────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("📊 Interactive Business Dashboard")
        if df is not None:
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                rev = df.groupby("Product_Name")["Revenue_USD"].sum().sort_values(ascending=False).reset_index()
                fig = px.bar(rev, x="Product_Name", y="Revenue_USD", title="Total Revenue by Product",
                             color="Revenue_USD", color_continuous_scale="Blues",
                             labels={"Revenue_USD": "Revenue (USD)", "Product_Name": "Product"})
                fig.update_layout(xaxis_tickangle=-35, showlegend=False, height=370)
                st.plotly_chart(fig, use_container_width=True)

            with r1c2:
                pm = df.groupby("Product_Name").agg(Rev=("Revenue_USD","sum"), Prof=("Profit_USD","sum")).reset_index()
                pm["Margin_%"] = (pm["Prof"] / pm["Rev"] * 100).round(1)
                fig2 = px.bar(pm.sort_values("Margin_%", ascending=False), x="Product_Name", y="Margin_%",
                              title="Profit Margin by Product (%)", color="Margin_%",
                              color_continuous_scale="Greens",
                              labels={"Margin_%": "Margin (%)", "Product_Name": "Product"})
                fig2.update_layout(xaxis_tickangle=-35, showlegend=False, height=370)
                st.plotly_chart(fig2, use_container_width=True)

            r2c1, r2c2 = st.columns(2)
            with r2c1:
                dfc = df.copy()
                dfc["Month"] = dfc["Date"].dt.to_period("M").astype(str)
                mon = dfc.groupby("Month").agg(Revenue=("Revenue_USD","sum"), Profit=("Profit_USD","sum")).reset_index()
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=mon["Month"], y=mon["Revenue"], mode="lines+markers",
                                          name="Revenue", line=dict(color="#4f46e5", width=3)))
                fig3.add_trace(go.Scatter(x=mon["Month"], y=mon["Profit"], mode="lines+markers",
                                          name="Profit", line=dict(color="#10b981", width=3)))
                fig3.update_layout(title="Monthly Revenue & Profit Trend", height=370, yaxis_title="USD")
                st.plotly_chart(fig3, use_container_width=True)

            with r2c2:
                cat = df.groupby("Category")["Revenue_USD"].sum().reset_index()
                fig4 = px.pie(cat, values="Revenue_USD", names="Category",
                              title="Revenue Share by Category",
                              color_discrete_sequence=px.colors.qualitative.Bold)
                fig4.update_layout(height=370)
                st.plotly_chart(fig4, use_container_width=True)

            r3c1, r3c2 = st.columns(2)
            with r3c1:
                rat = df.groupby("Product_Name")["Customer_Rating"].mean().reset_index()
                rat = rat.sort_values("Customer_Rating", ascending=False)
                fig5 = px.bar(rat, x="Product_Name", y="Customer_Rating",
                              title="Avg Customer Rating by Product",
                              color="Customer_Rating",
                              color_continuous_scale=["#ef4444","#f59e0b","#10b981"],
                              range_color=[3.5, 5.0],
                              labels={"Customer_Rating":"Avg Rating","Product_Name":"Product"})
                fig5.add_hline(y=4.0, line_dash="dash", line_color="gray", annotation_text="Target: 4.0")
                fig5.update_layout(xaxis_tickangle=-35, showlegend=False, height=370)
                st.plotly_chart(fig5, use_container_width=True)

            with r3c2:
                reg = df.groupby("Region").agg(Revenue=("Revenue_USD","sum"), Profit=("Profit_USD","sum")).reset_index()
                fig6 = px.bar(reg, x="Region", y=["Revenue","Profit"], title="Revenue vs Profit by Region",
                              barmode="group", labels={"value":"USD","variable":"Metric"},
                              color_discrete_map={"Revenue":"#4f46e5","Profit":"#10b981"})
                fig6.update_layout(height=370)
                st.plotly_chart(fig6, use_container_width=True)

            mkt = df.groupby("Product_Name").agg(Mkt=("Marketing_Spend_USD","sum"), Prof=("Profit_USD","sum")).reset_index()
            mkt["ROI_%"] = (mkt["Prof"] / mkt["Mkt"] * 100).round(1)
            fig7 = px.bar(mkt.sort_values("ROI_%", ascending=False), x="Product_Name", y="ROI_%",
                          title="Marketing ROI by Product (Profit / Marketing Spend %)",
                          color="ROI_%", color_continuous_scale="RdYlGn",
                          labels={"ROI_%":"ROI (%)","Product_Name":"Product"})
            fig7.update_layout(xaxis_tickangle=-35, showlegend=False)
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("Upload a CSV file to view the interactive dashboard.")

    # ── Agent Report Tabs ─────────────────────────────────────────────────────
    agent_tab_map = [
        ("👥", "Customer Feedback Agent",      tabs[1]),
        ("📈", "Sales Analysis Agent",          tabs[2]),
        ("🌍", "Market Research Agent",         tabs[3]),
        ("🏆", "Competitor Analysis Agent",     tabs[4]),
        ("🔍", "SWOT Analysis Agent",           tabs[5]),
        ("⭐", "Feature Prioritization Agent",  tabs[6]),
        ("💡", "Opportunity Analysis Agent",    tabs[7]),
        ("🎯", "Strategy Recommendation Agent", tabs[8]),
        ("📋", "Executive Report Agent",        tabs[9]),
    ]

    for icon, agent_name, tab in agent_tab_map:
        with tab:
            st.markdown(f"### {icon} {agent_name}")
            content = results.get(agent_name, "")
            if content:
                if content.startswith("⚠️"):
                    st.error(content)
                else:
                    st.markdown(content)
            else:
                st.info("Analysis not yet available for this agent.")

    # ── Tab 10: Chat ──────────────────────────────────────────────────────────
    with tabs[10]:
        st.subheader("💬 Chat with Your Product Strategy AI")
        st.caption(
            "Ask anything about your data, products, strategy, market opportunities, "
            "competitor positioning, or specific recommendations."
        )

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask about your product strategy, sales, market, competitors, or opportunities..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    from orchestrator import Orchestrator
                    orc = Orchestrator(client, model_name)
                    response = orc.chat(prompt, results, st.session_state.chat_history[:-1])
                st.markdown(response)

            st.session_state.chat_history.append({"role": "assistant", "content": response})

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()

        st.markdown("---")
        st.markdown("**💡 Suggested Questions:**")
        suggestions = [
            "Which product has the best overall opportunity score?",
            "What are the top 3 strategic priorities for next quarter?",
            "Which region should we expand into and with which product?",
            "What do competitors do better than us based on customer feedback?",
            "How should we reallocate our marketing budget?",
            "What are our biggest threats in the next 12 months?",
            "Which products are at risk and why?",
            "What are the quick win opportunities we can capture in 90 days?",
        ]
        c1, c2 = st.columns(2)
        for i, s in enumerate(suggestions):
            (c1 if i % 2 == 0 else c2).markdown(f"- *{s}*")
