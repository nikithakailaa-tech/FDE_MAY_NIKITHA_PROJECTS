"""
PDF Generator Agent
===================
Creates a professional, beautifully formatted travel report PDF.

SECTIONS:
  Cover Page          — Destination photo-style header, trip summary
  Section 1           — Flights / Transport Details
  Section 2           — Hotel Details
  Section 3           — Weather Summary
  Section 4           — Day-wise Itinerary (1 page per day)
  Section 5           — Budget Report with breakdown table
  Section 6           — Packing Checklist
  Section 7           — Emergency Contacts

Library: ReportLab (Platypus + Canvas)
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from state import TripState
from config import OUTPUT_DIR


# ── Color Palette ──────────────────────────────────────────────────────────
BRAND_BLUE   = colors.HexColor("#1A3C5E")
BRAND_TEAL   = colors.HexColor("#0D9488")
BRAND_AMBER  = colors.HexColor("#F59E0B")
BRAND_LIGHT  = colors.HexColor("#F0F9FF")
BRAND_GREY   = colors.HexColor("#64748B")
WHITE        = colors.white
BLACK        = colors.black


# ── Custom Styles ──────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=28,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=6
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Helvetica", fontSize=14,
            textColor=colors.HexColor("#CBD5E1"), alignment=TA_CENTER, spaceAfter=4
        ),
        "section_header": ParagraphStyle(
            "section_header", fontName="Helvetica-Bold", fontSize=16,
            textColor=WHITE, backColor=BRAND_BLUE,
            spaceBefore=14, spaceAfter=8, leftIndent=8, leading=22
        ),
        "day_header": ParagraphStyle(
            "day_header", fontName="Helvetica-Bold", fontSize=13,
            textColor=WHITE, backColor=BRAND_TEAL,
            spaceBefore=10, spaceAfter=6, leftIndent=6, leading=20
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#1E293B"), spaceAfter=4, leading=15
        ),
        "body_small": ParagraphStyle(
            "body_small", fontName="Helvetica", fontSize=9,
            textColor=BRAND_GREY, spaceAfter=3, leading=13
        ),
        "bold": ParagraphStyle(
            "bold", fontName="Helvetica-Bold", fontSize=10,
            textColor=BRAND_BLUE, spaceAfter=4
        ),
        "tip": ParagraphStyle(
            "tip", fontName="Helvetica-Oblique", fontSize=9,
            textColor=colors.HexColor("#0369A1"), spaceAfter=3,
            leftIndent=12, leading=13
        ),
        "checklist": ParagraphStyle(
            "checklist", fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#1E293B"), spaceAfter=3,
            leftIndent=10, leading=14
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=8,
            textColor=BRAND_GREY, alignment=TA_CENTER
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="Helvetica", fontSize=12,
            textColor=colors.HexColor("#E2E8F0"), alignment=TA_CENTER, spaceAfter=6
        ),
    }
    return styles


# ── Helper: Colored block table ────────────────────────────────────────────

def _info_box(label: str, value: str, styles: dict) -> Table:
    data = [[Paragraph(f"<b>{label}</b>", styles["body"]),
             Paragraph(str(value), styles["body"])]]
    t = Table(data, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BRAND_LIGHT),
        ("BACKGROUND", (1, 0), (1, 0), WHITE),
        ("TEXTCOLOR",  (0, 0), (0, 0), BRAND_BLUE),
        ("BOX",        (0, 0), (-1, -1), 0.5, BRAND_GREY),
        ("INNERGRID",  (0, 0), (-1, -1), 0.25, BRAND_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return t


# ── Section builders ────────────────────────────────────────────────────────

def _build_cover(state: TripState, styles: dict, story: list):
    """Cover page with gradient-effect table."""
    # Cover background using table
    cover_data = [[
        Paragraph(f"  AI TRIP PLANNER  ", ParagraphStyle(
            "brand", fontName="Helvetica", fontSize=11,
            textColor=BRAND_AMBER, alignment=TA_CENTER
        )),
    ]]
    cover_table = Table(cover_data, colWidths=[175*mm], rowHeights=[12*mm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BLUE),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 8*mm))

    # Big destination title
    story.append(Paragraph(
        f"{state['source'].upper()}  ->  {state['destination'].upper()}",
        styles["title"]
    ))

    story.append(Paragraph(
        f"{state.get('travel_type', 'Trip').title()} Trip  •  {state.get('travel_dates', '')}  •  {state.get('num_days', '')} Days",
        ParagraphStyle("sub2", fontName="Helvetica", fontSize=13,
                       textColor=BRAND_BLUE, alignment=TA_CENTER, spaceAfter=8)
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_TEAL))
    story.append(Spacer(1, 6*mm))

    # Quick-facts grid
    qf_data = [
        ["Travelers", f"{state.get('num_travelers', 1)} ({state.get('travel_type', '')})"],
        ["Budget",    f"Rs.{state.get('budget', 0):,}"],
        ["Hotel",     state.get('hotel_pref', 'N/A')],
        ["Transport", state.get('transport_pref', 'N/A')],
        ["Food Pref", state.get('food_pref', 'N/A')],
        ["Generated", datetime.now().strftime("%d %b %Y, %I:%M %p")],
    ]
    t = Table(qf_data, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), BRAND_TEAL),
        ("BACKGROUND", (1, 0), (1, -1), BRAND_LIGHT),
        ("TEXTCOLOR",  (0, 0), (0, -1), WHITE),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
        ("BOX",        (0, 0), (-1, -1), 1, BRAND_BLUE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, BRAND_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    # Places of interest tags
    interests = state.get("places_interest", [])
    if interests:
        tags = "  |  ".join(["  " + p.title() + "  " for p in interests])
        story.append(Paragraph(f"Interests:  {tags}", styles["body"]))

    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_GREY))
    story.append(PageBreak())


def _build_transport_section(state: TripState, styles: dict, story: list):
    story.append(Paragraph("  Section 1: Transport & Travel", styles["section_header"]))
    story.append(Spacer(1, 3*mm))

    t_data = state.get("transport_data", {})
    story.append(_info_box("Mode", t_data.get("mode", "").upper(), styles))
    story.append(_info_box("Recommended", t_data.get("recommended", "N/A"), styles))
    story.append(Spacer(1, 3*mm))

    options = t_data.get("options", [])
    if options:
        story.append(Paragraph("<b>Available Options</b>", styles["bold"]))
        headers = list(options[0].keys())
        table_data = [headers] + [[str(o.get(k, "")) for k in headers] for o in options]
        col_w = 175 * mm / max(len(headers), 1)
        t = Table(table_data, colWidths=[col_w] * len(headers))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRAND_LIGHT, WHITE]),
            ("BOX",        (0, 0), (-1, -1), 0.5, BRAND_GREY),
            ("INNERGRID",  (0, 0), (-1, -1), 0.25, BRAND_GREY),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    tips = t_data.get("tips") or t_data.get("airport_tips") or []
    if tips:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("<b>Travel Tips</b>", styles["bold"]))
        for tip in tips:
            story.append(Paragraph(f"• {tip}", styles["tip"]))

    story.append(Spacer(1, 5*mm))


def _build_hotel_section(state: TripState, styles: dict, story: list):
    story.append(Paragraph("  Section 2: Hotel & Accommodation", styles["section_header"]))
    story.append(Spacer(1, 3*mm))

    h_data = state.get("hotel_data", {})
    story.append(_info_box("Tier",        h_data.get("tier", "").title(), styles))
    story.append(_info_box("Recommended", h_data.get("recommended", "N/A"), styles))
    story.append(_info_box("Note",        h_data.get("notes", ""), styles))
    story.append(Spacer(1, 3*mm))

    options = h_data.get("options", [])
    if options:
        story.append(Paragraph("<b>Hotel Options</b>", styles["bold"]))
        for h in options:
            stars = "★" * h.get("rating", 0)
            story.append(Paragraph(
                f"<b>{h['name']}</b>  {stars}  — {h.get('location', '')}",
                styles["bold"]
            ))
            story.append(Paragraph(
                f"Price: Rs.{h.get('price_night', 0):,}/night  |  "
                f"Total ({state.get('num_days')} nights): Rs.{h.get('total_cost', 0):,}  |  "
                f"TripAdvisor: {h.get('tripadvisor', 'N/A')}",
                styles["body_small"]
            ))
            amenities = ", ".join(h.get("amenities", []))
            story.append(Paragraph(f"Amenities: {amenities}", styles["body_small"]))
            story.append(Paragraph(f"Highlight: {h.get('highlights', '')}", styles["tip"]))
            story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 5*mm))


def _build_weather_section(state: TripState, styles: dict, story: list):
    story.append(Paragraph("  Weather Forecast", styles["section_header"]))
    story.append(Spacer(1, 3*mm))

    w = state.get("weather_data", {})
    temp = w.get("temperature", {})
    story.append(_info_box("Summary",       w.get("summary", "N/A"), styles))
    story.append(_info_box("Temperature",
                           f"{temp.get('min', '?')}–{temp.get('max', '?')}{temp.get('unit', '°C')}",
                           styles))
    story.append(_info_box("Humidity",      w.get("humidity", "N/A"), styles))
    story.append(_info_box("Rainfall Risk", w.get("rainfall_risk", "N/A").upper(), styles))
    story.append(_info_box("UV Index",      str(w.get("uv_index", "N/A")), styles))
    story.append(_info_box("Best Time",     w.get("best_time", "N/A"), styles))

    tips = w.get("packing_tips", [])
    if tips:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("<b>Weather-based Packing Tips</b>", styles["bold"]))
        for tip in tips:
            story.append(Paragraph(f"• {tip}", styles["tip"]))

    story.append(Spacer(1, 5*mm))


def _build_itinerary_section(state: TripState, styles: dict, story: list):
    story.append(Paragraph("  Section 3: Day-wise Itinerary", styles["section_header"]))
    story.append(Spacer(1, 3*mm))

    itin = state.get("itinerary", {})
    story.append(Paragraph(itin.get("summary", ""), styles["body"]))
    story.append(Spacer(1, 4*mm))

    for day in itin.get("days", []):
        # Day header
        story.append(Paragraph(
            f"  Day {day.get('day')} — {day.get('theme', '')}",
            styles["day_header"]
        ))

        # Activities table
        activities = day.get("activities", [])
        if activities:
            act_data = [["Time", "Activity", "Location", "Duration", "Cost"]]
            for act in activities:
                act_data.append([
                    act.get("time", ""),
                    act.get("activity", ""),
                    act.get("location", ""),
                    act.get("duration", ""),
                    act.get("cost", ""),
                ])
            t = Table(act_data, colWidths=[22*mm, 60*mm, 38*mm, 26*mm, 29*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), BRAND_TEAL),
                ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
                ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [BRAND_LIGHT, WHITE]),
                ("BOX",           (0, 0), (-1, -1), 0.5, BRAND_GREY),
                ("INNERGRID",     (0, 0), (-1, -1), 0.25, BRAND_GREY),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                ("WORDWRAP",      (0, 0), (-1, -1), True),
            ]))
            story.append(t)

        # Tips from activities
        tips = [a.get("tip") for a in activities if a.get("tip")]
        if tips:
            story.append(Spacer(1, 2*mm))
            for tip in tips[:3]:
                story.append(Paragraph(f"Tip: {tip}", styles["tip"]))

        # Meals
        meals = day.get("meals", {})
        if meals:
            story.append(Spacer(1, 2*mm))
            meals_str = (f"Breakfast: {meals.get('breakfast', 'N/A')}  |  "
                         f"Lunch: {meals.get('lunch', 'N/A')}  |  "
                         f"Dinner: {meals.get('dinner', 'N/A')}")
            story.append(Paragraph(f"Meals — {meals_str}", styles["body_small"]))

        story.append(Paragraph(f"Estimated daily spend: {day.get('daily_budget', 'N/A')}", styles["bold"]))
        story.append(Spacer(1, 4*mm))


def _build_budget_section(state: TripState, styles: dict, story: list):
    story.append(Paragraph("  Section 4: Budget Report", styles["section_header"]))
    story.append(Spacer(1, 3*mm))

    bs = state.get("budget_summary", {})
    breakdown = bs.get("breakdown", {})

    # Summary boxes
    status = "YES" if bs.get("within_budget") else "NO — OVER BUDGET"
    story.append(_info_box("Total Budget",    f"Rs.{bs.get('total_budget', 0):,}", styles))
    story.append(_info_box("Estimated Cost",  f"Rs.{bs.get('estimated_total', 0):,}", styles))
    story.append(_info_box("Remaining",       f"Rs.{bs.get('remaining', 0):,}", styles))
    story.append(_info_box("Per Person",      f"Rs.{bs.get('per_person_cost', 0):,}", styles))
    story.append(_info_box("Within Budget?",  status, styles))
    story.append(Spacer(1, 3*mm))

    # Pie-chart style breakdown table
    story.append(Paragraph("<b>Cost Breakdown</b>", styles["bold"]))
    total = bs.get("estimated_total", 1)
    bk_data = [["Category", "Amount", "% of Total"]]
    for cat, amt in breakdown.items():
        pct = (amt / total * 100) if total else 0
        bk_data.append([cat.replace("_", " ").title(),
                        f"Rs.{amt:,.0f}",
                        f"{pct:.1f}%"])
    bk_data.append(["TOTAL", f"Rs.{total:,.0f}", "100%"])

    t = Table(bk_data, colWidths=[75*mm, 55*mm, 45*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BRAND_AMBER),
        ("TEXTCOLOR",     (0, 0), (-1, 0), BLACK),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND",    (0, -1), (-1, -1), BRAND_BLUE),
        ("TEXTCOLOR",     (0, -1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -2), [BRAND_LIGHT, WHITE]),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, BRAND_BLUE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, BRAND_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(t)

    tips = bs.get("optimisation_tips", [])
    if tips:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("<b>Optimisation Tips</b>", styles["bold"]))
        for tip in tips:
            story.append(Paragraph(f"• {tip}", styles["tip"]))

    story.append(Spacer(1, 5*mm))


def _build_packing_section(state: TripState, styles: dict, story: list):
    story.append(Paragraph("  Section 5: Packing Checklist", styles["section_header"]))
    story.append(Spacer(1, 3*mm))

    items = state.get("itinerary", {}).get("packing_checklist", [])
    if not items:
        items = ["Passport/ID", "Travel insurance", "Phone charger",
                 "Sunscreen", "Light clothes", "Medications"]

    # 2-column layout
    half  = len(items) // 2 + len(items) % 2
    col1  = items[:half]
    col2  = items[half:]

    rows = []
    for i in range(half):
        left  = f"[ ]  {col1[i]}" if i < len(col1) else ""
        right = f"[ ]  {col2[i]}" if i < len(col2) else ""
        rows.append([Paragraph(left, styles["checklist"]),
                     Paragraph(right, styles["checklist"])])

    t = Table(rows, colWidths=[87*mm, 88*mm])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_LIGHT, WHITE]),
        ("BOX",  (0, 0), (-1, -1), 0.5, BRAND_GREY),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BRAND_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 5*mm))


def _build_emergency_section(state: TripState, styles: dict, story: list):
    story.append(Paragraph("  Section 6: Emergency Contacts", styles["section_header"]))
    story.append(Spacer(1, 3*mm))

    contacts = state.get("itinerary", {}).get("emergency_contacts", {})
    default  = {
        "Police": "100", "Ambulance": "108",
        "Tourist Helpline": "1800-111-363", "Fire": "101"
    }
    contacts = contacts or default

    rows = [[Paragraph(f"<b>{k}</b>", styles["bold"]),
             Paragraph(str(v), styles["body"])]
            for k, v in contacts.items()]

    t = Table(rows, colWidths=[80*mm, 95*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), BRAND_LIGHT),
        ("ROWBACKGROUNDS",(1, 0), (1, -1), [WHITE, colors.HexColor("#FFF7ED")]),
        ("BOX",           (0, 0), (-1, -1), 1, BRAND_BLUE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, BRAND_GREY),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("FONTSIZE",      (0, 0), (-1, -1), 11),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        "This report was generated by the AI Multi-Agent Trip Planner. "
        "Always verify bookings and check official travel advisories before departure.",
        styles["footer"]
    ))


# ── Page header/footer callback ────────────────────────────────────────────

class _PageDecorator:
    """Adds header and footer to every page."""
    def __init__(self, dest: str, travel_dates: str):
        self.dest   = dest
        self.dates  = travel_dates

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        # Header bar
        canvas.setFillColor(BRAND_BLUE)
        canvas.rect(0, h - 20*mm, w, 20*mm, fill=True, stroke=False)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(15*mm, h - 12*mm, f"AI Trip Planner — {self.dest}")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(w - 15*mm, h - 12*mm, self.dates)

        # Footer bar
        canvas.setFillColor(BRAND_TEAL)
        canvas.rect(0, 0, w, 10*mm, fill=True, stroke=False)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(w / 2, 3.5*mm,
                                 f"Page {doc.page}  |  Generated by AI Multi-Agent Trip Planner  |  {datetime.now().strftime('%d %b %Y')}")
        canvas.restoreState()


# ── LangGraph Node ─────────────────────────────────────────────────────────

def pdf_generator_agent(state: TripState) -> TripState:
    """
    LangGraph Node — PDF Generator Agent
    ----------------------------------------
    Called ONLY after Orchestrator approves the trip plan.
    Generates a professional multi-section PDF report.
    """
    print("\n[PDFAgent] 📄  Generating professional trip report PDF...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dest     = state.get("destination", "Trip").replace(" ", "_")
    filename = f"{OUTPUT_DIR}/TripPlan_{dest}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    try:
        decorator = _PageDecorator(
            state.get("destination", ""),
            state.get("travel_dates", "")
        )

        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=15*mm, leftMargin=15*mm,
            topMargin=25*mm,   bottomMargin=18*mm,
        )

        styles = _build_styles()
        story  = []

        # Cover
        _build_cover(state, styles, story)

        # Section 1 — Transport
        _build_transport_section(state, styles, story)
        story.append(PageBreak())

        # Section 2 — Hotels
        _build_hotel_section(state, styles, story)
        story.append(PageBreak())

        # Weather
        _build_weather_section(state, styles, story)

        # Section 3 — Itinerary
        story.append(PageBreak())
        _build_itinerary_section(state, styles, story)

        # Section 4 — Budget
        story.append(PageBreak())
        _build_budget_section(state, styles, story)

        # Section 5 — Packing
        _build_packing_section(state, styles, story)

        # Section 6 — Emergency
        _build_emergency_section(state, styles, story)

        doc.build(story, onFirstPage=decorator, onLaterPages=decorator)

        state["pdf_status"] = "generated"
        state["pdf_path"]   = filename
        msg = f"PDF generated: {filename}"
        state["messages"].append(f"[PDFAgent] {msg}")
        print(f"[PDFAgent] ✅ {msg}")

    except Exception as e:
        err = f"PDF generation failed: {e}"
        state["pdf_status"] = "failed"
        state["errors"].append(err)
        state["messages"].append(f"[PDFAgent] ERROR: {err}")
        print(f"[PDFAgent] ❌ {err}")
        raise

    return state
