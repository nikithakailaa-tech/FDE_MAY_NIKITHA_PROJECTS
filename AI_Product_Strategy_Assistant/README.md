# AI-Powered Product Strategy Assistant

**🚀 Live Application:** [https://fde-may-nikitha-projects-4.onrender.com/](https://fde-may-nikitha-projects-4.onrender.com/)

A multi-agent AI system that helps Product Managers analyze business data, generate strategic insights, and make data-driven decisions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                        │
│  Upload · Dashboard · 9 Agent Reports · Chat · PDF Export   │
└─────────────────────────┬───────────────────────────────────┘
                           │
┌─────────────────────────▼───────────────────────────────────┐
│                    ORCHESTRATOR                              │
│         Sequential multi-agent pipeline with                 │
│         shared context passing between agents               │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬────────┘
   │      │      │      │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
[Agent1][Agent2][Agent3][Agent4][Agent5][Agent6][Agent7][Agent8][Agent9]
```

## 9 AI Agents

| # | Agent | Responsibility |
|---|-------|---------------|
| 1 | **Customer Feedback Agent** | Sentiment analysis, pain points, satisfaction ranking |
| 2 | **Sales Analysis Agent** | Revenue, margin, ROI, regional & monthly trends |
| 3 | **Market Research Agent** | Market sizing, segment analysis, demand trends |
| 4 | **Competitor Analysis Agent** | Competitive positioning, feature gaps, threats |
| 5 | **SWOT Analysis Agent** | Strengths, weaknesses, opportunities, threats |
| 6 | **Feature Prioritization Agent** | RICE scoring, product investment matrix, roadmap |
| 7 | **Opportunity Analysis Agent** | Numeric opportunity scoring, ranked opportunities |
| 8 | **Strategy Recommendation Agent** | Action plan, KPIs, risk mitigation, investments |
| 9 | **Executive Report Agent** | Board-ready summary, scorecard, 12-month outlook |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Model** | GPT-4o Mini (via custom gateway) |
| **Frontend** | Streamlit |
| **Visualization** | Plotly |
| **Data Processing** | Pandas |
| **PDF Generation** | fpdf2 |
| **Document Parsing** | PyPDF2 |
| **Agent Framework** | Custom multi-agent orchestrator |

## Supported Data Formats

- **CSV** — Sales data, customer reviews, survey responses, analytics
- **PDF** — Market research, competitor reports, strategy documents
- **TXT / MD** — Feature requests, product briefs, research notes

## Expected Outputs

- ✅ Customer Insights Report
- ✅ Sales Performance Analysis
- ✅ Market Research Summary
- ✅ Competitor Analysis Report
- ✅ SWOT Analysis
- ✅ Feature Prioritization (RICE Scoring)
- ✅ Product Opportunity Assessment (with numeric scores)
- ✅ Strategic Action Plan
- ✅ Product Roadmap Suggestions
- ✅ Executive Summary
- ✅ Downloadable PDF Report
- ✅ Interactive Dashboards (7 Plotly charts)
- ✅ Natural Language Chat Assistant

## Setup & Run Locally

```bash
# 1. Clone / download the project
cd A3

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`

## Deploy on Render

1. Push code to a GitHub repository
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` and deploys

## Deploy on Railway

```bash
railway login
railway init
railway up
```

## Project Structure

```
A3/
├── app.py                        # Main Streamlit application
├── orchestrator.py               # Multi-agent coordinator
├── requirements.txt              # Python dependencies
├── render.yaml                   # Render deployment config
├── Procfile                      # Railway / Heroku config
├── README.md                     # This file
├── agents/
│   ├── base.py                   # BaseAgent class
│   ├── customer_feedback.py      # Agent 1
│   ├── sales_analysis.py         # Agent 2
│   ├── market_research.py        # Agent 3
│   ├── competitor_analysis.py    # Agent 4
│   ├── swot.py                   # Agent 5
│   ├── feature_prioritization.py # Agent 6
│   ├── opportunity_analysis.py   # Agent 7
│   ├── strategy.py               # Agent 8
│   └── executive_report.py       # Agent 9
└── utils/
    ├── data_processor.py         # File parsing + stat formatting
    └── pdf_generator.py          # PDF report generation
```

## Evaluation Criteria Coverage

| Criteria | Weight | Status |
|----------|--------|--------|
| Successful Deployment | 30% | ✅ Render/Railway ready |
| Quality of AI Insights | 35% | ✅ 9 specialized agents with deep prompts |
| Multi-Agent Design & UX | 35% | ✅ 9 agents, 11 tabs, chat, PDF, dashboards |

## Bonus Features Implemented

- ✅ Advanced Multi-Agent Collaboration (sequential with full context passing)
- ✅ Product Opportunity Scoring (numeric RICE-based scoring)
- ✅ Roadmap Generation (30/60/90-day in Feature Prioritization Agent)
- ✅ Interactive Dashboards (7 Plotly charts)
- ✅ Executive Report Generation (board-ready PDF)
