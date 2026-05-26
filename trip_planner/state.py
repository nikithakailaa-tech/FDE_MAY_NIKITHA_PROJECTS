"""
State Schema for Multi-Agent Trip Planner
==========================================
This TypedDict defines the SHARED MEMORY (state) that flows through
every node in the LangGraph workflow. Every agent reads from and writes
to this state object — it's the single source of truth.
"""

from typing import TypedDict, Optional, List, Dict, Any


class TripState(TypedDict):
    # ── 1. Raw user inputs ─────────────────────────────────────────────────
    source:           str               # e.g. "Bangalore"
    destination:      str               # e.g. "Goa"
    travel_dates:     str               # e.g. "June 10-15 2025"
    num_days:         int               # e.g. 5
    budget:           float             # e.g. 30000  (in ₹)
    num_travelers:    int               # e.g. 2
    travel_type:      str               # "solo" | "couple" | "family" | "business"
    hotel_pref:       str               # "beach resort" | "budget" | "luxury" etc.
    food_pref:        str               # "seafood" | "veg" | "local" etc.
    transport_pref:   str               # "flight" | "train" | "bus" | "car"
    seat_pref:        str               # "window" | "aisle" | "1A" | "2A" | "3A" | etc.
    num_rooms:        int               # rooms to book (1 for couple/solo, split for friends)
    places_interest:  List[str]         # ["nightlife", "sightseeing", "beach"]
    luxury_or_budget: str               # "luxury" | "budget" | "mid-range"
    must_visit_places: str              # free-text: "Araku Valley, RK Beach" (from chatbot or form)

    # ── 2. Memory / past user profile ──────────────────────────────────────
    user_profile:     Dict[str, Any]    # retrieved from memory store
    past_trips:       List[Dict]        # previous trip history

    # ── 3. Agent outputs ───────────────────────────────────────────────────
    weather_data:     Dict[str, Any]    # from Weather Agent
    hotel_data:       Dict[str, Any]    # from Hotel Agent
    transport_data:   Dict[str, Any]    # from Transport Agent
    places_data:      Dict[str, Any]    # from Places Explorer Agent
    budget_summary:   Dict[str, Any]    # from Budget Agent
    itinerary:        Dict[str, Any]    # from Itinerary Agent (day-wise plan)

    # ── 4. Validation & control ────────────────────────────────────────────
    review_status:     str               # "pending" | "approved" | "needs_retry"
    review_issues:     List[str]         # list of problems found by Review Agent
    review_summary:    str               # LLM-written review paragraph
    review_highlights: List[str]         # positive aspects identified by LLM
    pdf_status:       str               # "pending" | "generated" | "failed"
    pdf_path:         str               # file path of generated PDF

    # ── 5. Guardrails & Evaluation ────────────────────────────────────────
    guardrail_warnings: List[str]       # non-fatal input warnings
    evaluation:         Dict[str, Any]  # quality scores from EvaluationAgent

    # ── 6. Orchestrator brain ──────────────────────────────────────────────
    orchestrator_decision: str          # current instruction from Orchestrator
    retry_count:      int               # how many retries have happened
    errors:           List[str]         # any errors collected during execution
    messages:         List[str]         # log of agent activities (audit trail)
