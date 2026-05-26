"""Generate PRESENTATION.pdf and ARCHITECTURE.pdf"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable, PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

os.makedirs("output", exist_ok=True)

# ── Shared styles ──────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

TITLE    = S('ti', fontSize=26, fontName='Helvetica-Bold',
             textColor=colors.HexColor('#1e293b'), alignment=TA_CENTER, spaceAfter=8)
SUB      = S('su', fontSize=12, fontName='Helvetica',
             textColor=colors.HexColor('#64748b'), alignment=TA_CENTER, spaceAfter=4)
SECNUM   = S('sn', fontSize=9,  fontName='Helvetica-Bold',
             textColor=colors.HexColor('#6366f1'), spaceBefore=20, spaceAfter=2)
SECTITLE = S('st', fontSize=17, fontName='Helvetica-Bold',
             textColor=colors.HexColor('#1e293b'), spaceAfter=4)
SECDESC  = S('sd', fontSize=11, fontName='Helvetica',
             textColor=colors.HexColor('#64748b'), spaceAfter=10, leading=16)
STITLE   = S('stt', fontSize=12, fontName='Helvetica-Bold',
             textColor=colors.HexColor('#1e293b'), spaceAfter=2, leftIndent=10)
SBODY    = S('sb', fontSize=10.5, fontName='Helvetica',
             textColor=colors.HexColor('#475569'), spaceAfter=8, leading=15, leftIndent=10)
ANAME    = S('an', fontSize=12, fontName='Helvetica-Bold',
             textColor=colors.HexColor('#1e293b'), spaceAfter=1)
AFILE    = S('af', fontSize=9,  fontName='Helvetica',
             textColor=colors.HexColor('#94a3b8'), spaceAfter=2)
ADESC    = S('ad', fontSize=10.5, fontName='Helvetica',
             textColor=colors.HexColor('#475569'), spaceAfter=10, leading=15)
FOOTER   = S('ft', fontSize=9,  fontName='Helvetica',
             textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)

C_HEAD   = colors.HexColor('#1e293b')
C_ROW1   = colors.HexColor('#f8fafc')
C_GRID   = colors.HexColor('#e2e8f0')
C_ACC    = colors.HexColor('#6366f1')

def table(data, widths):
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([
        ('BACKGROUND',     (0,0), (-1,0),  C_HEAD),
        ('TEXTCOLOR',      (0,0), (-1,0),  colors.white),
        ('FONTNAME',       (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [C_ROW1, colors.white]),
        ('GRID',           (0,0), (-1,-1), 0.4, C_GRID),
        ('VALIGN',         (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',     (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 5),
        ('LEFTPADDING',    (0,0), (-1,-1), 7),
    ]))
    return t

def hr():
    return HRFlowable(width='100%', thickness=1, color=C_GRID, spaceAfter=4, spaceBefore=4)


# ══════════════════════════════════════════════════════════════════════
#  PRESENTATION.pdf
# ══════════════════════════════════════════════════════════════════════
doc = SimpleDocTemplate('output/PRESENTATION.pdf', pagesize=A4,
      leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
story = []

# Cover
story += [
    Spacer(1, 1.2*cm),
    Paragraph('AI Trip Planner', TITLE),
    Paragraph('Multi-Agent System built with LangGraph, Flask, and Live APIs', SUB),
    Paragraph('OpenAI GPT-4o-mini  |  OpenRouter Llama 3.3-70B  |  Serper  |  OpenWeatherMap', SUB),
    Spacer(1, 0.4*cm), hr(),
]

# Section 1 — What it does
story += [
    Paragraph('SECTION 1', SECNUM),
    Paragraph('What Does This App Do?', SECTITLE),
    Paragraph(
        'A user types where they want to go and their budget. The system automatically runs '
        'multiple AI agents in the background — fetching live weather, finding hotels, '
        'searching transport, discovering attractions — and produces a complete day-by-day '
        'trip plan with a downloadable PDF report. No manual research needed.', SECDESC),
]
for num, title, desc in [
    ('1', 'User fills the form or chats with Trippy (AI chatbot)',
         'Enters source, destination, dates, budget, travelers, hotel & transport preferences.'),
    ('2', 'System validates and collects live data',
         '4 agents fetch real weather, transport, hotel listings, and tourist attractions from live APIs.'),
    ('3', 'AI writes a complete day-by-day itinerary',
         'GPT-4o-mini uses all real data to generate a weather-aware, budget-aware trip plan.'),
    ('4', 'Plan is reviewed, scored, and saved as PDF',
         'Another AI reviews quality. A third AI scores 0-100. PDF auto-generated and downloadable.'),
]:
    story.append(Paragraph(f'Step {num}  -  {title}', STITLE))
    story.append(Paragraph(desc, SBODY))
story.append(hr())

# Section 2 — Folder structure
story += [
    Paragraph('SECTION 2', SECNUM),
    Paragraph('Folder Structure', SECTITLE),
    Paragraph('Every file has one clear job. The project is organized so each layer is separate.', SECDESC),
    table([
        ['File', 'What it does'],
        ['app.py',               'Flask web server — defines all HTTP endpoints, runs the workflow'],
        ['workflow.py',          'Defines the LangGraph graph — connects all 11 agents in order'],
        ['state.py',             'TripState TypedDict — shared data container all agents read/write'],
        ['guardrails.py',        'Input validation — runs BEFORE the workflow starts'],
        ['config.py',            'API keys and settings (loaded from .env)'],
        ['requirements.txt',     'Python packages needed to run the app'],
        ['.env',                 'Your private API keys — never share this file'],
        ['start.py',             'Launch script — sets UTF-8 encoding then starts Flask'],
        ['architecture.html/pdf','Visual architecture flow diagram'],
        ['PRESENTATION.html/pdf','This document'],
        ['agents/ (11 files)',   'One file per agent — each agent does ONE job'],
        ['templates/index.html', 'The web UI — form, results dashboard, chatbot'],
        ['memory/',              'Stores user_memory.json — past trips and preferences'],
        ['output/',              'Generated PDF files saved here'],
    ], [4.5*cm, 12*cm]),
    hr(),
]

# Section 3 — How to run
story += [
    Paragraph('SECTION 3', SECNUM),
    Paragraph('How to Run the App', SECTITLE),
    Paragraph('Follow these steps in order. Steps 1-4 are one-time setup.', SECDESC),
]
for num, title, desc in [
    ('1', 'Install Python 3.11+',          'Download from python.org.  Verify: python --version'),
    ('2', 'Install all dependencies',       'In the trip_planner/ folder run:  pip install -r requirements.txt'),
    ('3', 'Configure API keys',             'Fill in .env file:  OPENAI_API_KEY, SERPER_API_KEY, OPENWEATHER_API_KEY, OPENROUTER_API_KEY'),
    ('4', 'Start the server',               'Run:  python -X utf8 start.py    Then open  http://localhost:8000'),
    ('5', 'Plan a trip',                    'Fill the form or click the chat bubble to talk to Trippy. Click Plan My Trip. Wait 30-60 sec.'),
    ('6', 'Download PDF',                   'Click Download PDF button after the plan is generated.'),
]:
    story.append(Paragraph(f'Step {num}  -  {title}', STITLE))
    story.append(Paragraph(desc, SBODY))
story.append(hr())

# Section 4 — All agents
story += [
    Paragraph('SECTION 4', SECNUM),
    Paragraph('All 11 Agents Explained', SECTITLE),
    Paragraph('Each agent is in its own file under agents/. Each does one job and writes its result to TripState.', SECDESC),
]
agents = [
    ('Orchestrator',     'agents/orchestrator.py',     'Rule-Based Logic',
     'The brain of the system. NOT an AI — pure Python if/else. Runs at 3 decision checkpoints: '
     'validate input, check data conflicts, approve final plan. Routes the workflow forward or stops it.'),
    ('Memory Agent',     'agents/memory_agent.py',     'Local JSON File',
     'Reads and writes user_memory.json. On start: loads past preferences. After plan approved: '
     'saves this trip so future trips remember the user preferences.'),
    ('Weather Agent',    'agents/weather_agent.py',    'OpenWeatherMap API',
     'Gets real daily forecast, min/max temperature, and rainfall risk level for the destination. '
     'Triggers weather warning popup if heavy rain or temperature >= 38C.'),
    ('Transport Agent',  'agents/transport_agent.py',  'Serper (Google) API',
     'Searches real flights, trains, or buses. Finds the nearest departure hub city using geocoding. '
     'Sets no_tickets_available flag if no options found.'),
    ('Hotel Agent',      'agents/hotel_agent.py',      'Serper (Google) API',
     'Finds real hotels matching user preference (beach resort, heritage, business etc.) '
     'and budget tier. Calculates total cost based on rooms and nights.'),
    ('Places Agent',     'agents/places_agent.py',     'Serper (Google) API',
     'Fetches real tourist spots, restaurants, and nightlife. Also finds nearby day-trip '
     'destinations within 3 hours. Switches to indoor-only results if heavy rain expected.'),
    ('Budget Agent',     'agents/budget_agent.py',     'Rule-Based Math (No LLM)',
     'Adds up all costs. If over budget: tries cheaper hotel tier first, then cheaper transport. '
     'Sets budget_exceeded flag and shows popup in UI if still over limit.'),
    ('Itinerary Agent',  'agents/itinerary_agent.py',  'OpenAI GPT-4o-mini',
     'Uses GPT-4o-mini to write the full day-by-day plan using REAL places. Includes must-visit '
     'places and schedules nearby day trips every 2 days. Validates output for hallucinated place names.'),
    ('Review Agent',     'agents/review_agent.py',     'OpenRouter Llama 3.3-70B',
     'Sends the full trip plan to Llama 3.3 as a travel consultant. Returns a review paragraph, '
     'list of issues, list of highlights, and verdict: approved or needs_retry.'),
    ('Evaluation Agent', 'agents/evaluation_agent.py', 'OpenRouter Llama 3.3-70B',
     'Scores the plan out of 100 across 5 areas: Budget Fit (25), Completeness (25), Weather '
     'Alignment (20), Data Quality (15), Transport Logic (15). Returns grade A/B/C/D.'),
    ('PDF Generator',    'agents/pdf_agent.py',        'ReportLab (Local)',
     'Generates a multi-page PDF: cover page, budget table, day-wise itinerary, hotel and '
     'transport details, weather summary, packing checklist, emergency contacts.'),
]
for name, file, api, desc in agents:
    story.append(Paragraph(name, ANAME))
    story.append(Paragraph(f'{file}   |   {api}', AFILE))
    story.append(Paragraph(desc, ADESC))
story.append(hr())

# Section 5 — Design decisions
story += [
    Paragraph('SECTION 5', SECNUM),
    Paragraph('Key Design Decisions', SECTITLE),
]
for q, a in [
    ('Why LangGraph?',
     'Gives a visual, inspectable graph. Each agent only reads/writes TripState — they do not '
     'call each other. This makes each agent independently testable and replaceable.'),
    ('Why 3 checkpoints instead of 1?',
     'Gate 1 stops bad input before any API calls (saves cost). Gate 2 catches conflicts before '
     'the expensive LLM call. Gate 3 verifies LLM output before writing to disk.'),
    ('Why rule-based Budget Agent?',
     'Budget math must be exact and deterministic. Simple math is always correct, always fast, '
     'and free. LLMs are only used where natural language generation adds real value.'),
    ('Why two different LLMs?',
     'GPT-4o-mini is best for structured generation (itinerary). Llama 3.3 via OpenRouter is '
     'free-tier accessible and good for review and evaluation. If one fails, the other is fallback.'),
    ('Why TripState?',
     'Instead of passing 30 arguments between agents, one shared dictionary holds everything. '
     'Every agent reads what it needs and writes its result back. Standard multi-agent pattern.'),
]:
    story.append(Paragraph(f'Q: {q}', STITLE))
    story.append(Paragraph(f'A: {a}', SBODY))
story.append(hr())

# Section 6 — Tech stack
story += [
    Paragraph('SECTION 6', SECNUM),
    Paragraph('Technology Stack', SECTITLE),
    table([
        ['Layer', 'Technology', 'Purpose'],
        ['Web Server',           'Flask (Python)',         'HTTP requests, serves UI, routes to workflow'],
        ['Workflow Engine',      'LangGraph',              'Agent graph, state management, conditional routing'],
        ['LLM Interface',        'LangChain',              'Standardized way to call OpenAI and OpenRouter'],
        ['Primary LLM',          'OpenAI GPT-4o-mini',    'Itinerary generation'],
        ['Fallback LLM',         'OpenRouter Llama 3.3',  'Review, evaluation, chatbot (free tier available)'],
        ['Places/Hotels/Transport','Serper API',           'Google Search API — real results for any city'],
        ['Weather',              'OpenWeatherMap',         'Real-time forecast, temperature, rainfall'],
        ['PDF Generation',       'ReportLab',              'Creates PDFs locally, no external service needed'],
        ['Frontend',             'HTML / CSS / JS',        'Web UI with date picker, no heavy framework'],
        ['Memory',               'JSON file',              'Saves user history between sessions'],
    ], [4*cm, 5*cm, 7.5*cm]),
    Spacer(1, 0.6*cm),
    Paragraph('AI Trip Planner  |  Multi-Agent System  |  11 Agents  |  LangGraph + Flask', FOOTER),
]

doc.build(story)
print('PRESENTATION.pdf created -> output/PRESENTATION.pdf')


# ══════════════════════════════════════════════════════════════════════
#  ARCHITECTURE.pdf
# ══════════════════════════════════════════════════════════════════════
doc2 = SimpleDocTemplate('output/ARCHITECTURE.pdf', pagesize=A4,
       leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
story2 = []

STEP  = S('sp', fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e293b'), spaceAfter=2, leftIndent=8)
NOTE  = S('nt', fontSize=10.5, fontName='Helvetica', textColor=colors.HexColor('#475569'), spaceAfter=10, leading=15, leftIndent=8)
GATE  = S('gt', fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#ea580c'), spaceAfter=2, leftIndent=8)
GOPT  = S('go', fontSize=10.5, fontName='Helvetica', textColor=colors.HexColor('#475569'), spaceAfter=10, leftIndent=8)

story2 += [
    Spacer(1, 0.8*cm),
    Paragraph('AI Trip Planner — How It Works', TITLE),
    Paragraph('Step-by-Step Flow  |  11 Agents  |  3 Decision Gates  |  LangGraph + Flask', SUB),
    Spacer(1, 0.3*cm), hr(),
]

steps = [
    # (type, number/label, title, description)
    ('step', '1', 'User Fills the Trip Form',
     'Enters: Source, Destination, Dates, Budget, No. of Travelers, Hotel & Transport preferences, Interests, Must-Visit Places.'),
    ('step', '1b', 'OR — Chats with Trippy (AI Chatbot)',
     'User describes the trip in natural language. Trippy collects all details through conversation and auto-fills the form using GPT-4o-mini.'),
    ('step', '2', 'Input Validation (Guardrails)',
     'Checks: Destination filled? Budget >= Rs.500? Days >= 2? Source != Destination? No harmful input?\nFAIL -> shows error instantly.  PASS -> workflow starts.'),
    ('gate', 'GATE 1', 'Are all required fields present in state?',
     'YES -> Continue to Memory Agent      |      NO -> Stop. Show error to user.'),
    ('step', '3', 'Memory Agent — Load User History',
     'Checks if this user has planned trips before. If yes, loads saved preferences (e.g. "prefers seafood", "likes beach hotels") to personalize this trip.'),
    ('step', '4', '4 Data Agents Collect Real Information',
     'Weather Agent     -> OpenWeatherMap -> daily forecast, temperature, rainfall risk\n'
     'Transport Agent   -> Serper API     -> flights/trains/buses, prices, departure hub\n'
     'Hotel Agent       -> Serper API     -> hotels matching preference and budget tier\n'
     'Places Agent      -> Serper API     -> attractions, restaurants, nearby day trips'),
    ('step', '5', 'Budget Agent — Calculate and Auto-Optimize',
     'Total = transport + hotel x nights x rooms + food x days x travelers + activities + 10% misc.\n'
     'Over budget? -> Tries cheaper hotel tier. Still over? -> Tries cheaper transport. Shows popup if still over.'),
    ('gate', 'GATE 2', 'Any conflicts in the collected data?',
     'NO conflicts -> Build the itinerary      |      Conflict found (rain+outdoor / hotel too pricey) -> Flag and continue'),
    ('step', '6', 'Itinerary Agent — AI Writes the Day-by-Day Plan',
     'GPT-4o-mini receives all real data and writes a complete time-blocked itinerary.\n'
     'Includes must-visit places. Schedules nearby day trips every 2 days.\n'
     'Validates output — rejects hallucinated wrong-city place names.'),
    ('step', '7', 'Review Agent — AI Reads Plan as a Travel Expert',
     'Llama 3.3 checks: Does plan match budget? Weather? User preferences?\n'
     'Returns: review paragraph + issues list + highlights list + verdict (Approved / Needs Retry).'),
    ('step', '8', 'Evaluation Agent — AI Scores the Plan 0 to 100',
     'Budget Fit (25 pts) + Completeness (25 pts) + Weather Alignment (20 pts) + Data Quality (15 pts) + Transport Logic (15 pts)\n'
     'Grade:  A = 90+     B = 75+     C = 60+     D = below 60'),
    ('gate', 'GATE 3', 'Is the generated plan good enough?',
     'APPROVED -> Save to memory + Generate PDF      |      ISSUES FOUND -> Retry pipeline (max 3 times)'),
    ('step', '9', 'Memory Agent — Save This Trip',
     'Saves completed trip and preferences to memory/user_memory.json.\n'
     'Next time this user plans a trip, their preferences are remembered automatically.'),
    ('step', '10', 'PDF Generator — Create Downloadable Trip Report',
     'Generates full PDF using ReportLab: cover page, budget table, day-wise itinerary,\n'
     'hotel & transport details, weather summary, packing checklist, emergency contacts.'),
    ('step', '11', 'Results Shown on the Web Dashboard',
     'User sees: Hotels, Transport, Places, Day-wise Itinerary, Budget Breakdown, Score Card.\n'
     'Smart popups: Weather warning, Budget exceeded, No tickets available. Download PDF button.'),
]

arrow_style = S('arr', fontSize=11, textColor=colors.HexColor('#94a3b8'),
                alignment=TA_CENTER, spaceAfter=0, spaceBefore=0)

for item in steps:
    kind = item[0]
    if kind == 'step':
        _, num, title, desc = item
        story2.append(Paragraph(f'STEP {num}  —  {title}', STEP))
        story2.append(Paragraph(desc, NOTE))
    else:
        _, label, question, options = item
        story2.append(Paragraph(f'[ {label} ]  {question}', GATE))
        story2.append(Paragraph(options, GOPT))
    story2.append(Paragraph('|', arrow_style))

story2 += [
    hr(),
    Spacer(1, 0.3*cm),
    Paragraph('SUMMARY', SECNUM),
    Paragraph('Quick Reference', SECTITLE),
    table([
        ['Component',       'Technology',           'Job'],
        ['Web Server',      'Flask',                'Receive form, run workflow, return JSON'],
        ['Workflow Engine',  'LangGraph',            'Connect all agents, handle routing decisions'],
        ['Decision Gates',   'Python if/else',       '3 checkpoints that stop or redirect the flow'],
        ['Data Collection',  'Serper + OpenWeatherMap', '4 agents fetch real live data in parallel'],
        ['Cost Calculation', 'Rule-Based Math',      'Budget agent calculates and auto-optimizes'],
        ['Plan Writing',     'GPT-4o-mini',          'Itinerary agent writes the day-by-day plan'],
        ['Quality Check',    'Llama 3.3-70B',        'Review agent checks plan, Evaluation agent scores it'],
        ['Memory',           'JSON file',            'Saves user preferences across sessions'],
        ['PDF Report',       'ReportLab',            'Generates the downloadable trip document'],
    ], [4*cm, 5.5*cm, 7*cm]),
    Spacer(1, 0.6*cm),
    Paragraph('AI Trip Planner  |  11 Agents  |  3 Decision Gates  |  LangGraph + Flask', FOOTER),
]

doc2.build(story2)
print('ARCHITECTURE.pdf created -> output/ARCHITECTURE.pdf')
print('Done!')
