"""
Orchestrator Agent (Supervisor Agent)
======================================
THIS IS THE MOST IMPORTANT AGENT IN THE SYSTEM.

Without the Orchestrator:
  → Agents are just independent functions.

With the Orchestrator:
  → The system becomes true Agentic AI.

RESPONSIBILITIES:
  1. Understand user goal & context (completeness check)
  2. Decide which agents need to run
  3. Detect conflicts (hotel > budget, rain + outdoor plans, etc.)
  4. Trigger retries for failed or conflicting agents
  5. Give final approval before PDF generation
  6. Route to memory update after approval

HOW IT WORKS IN LANGGRAPH:
  The orchestrator is a conditional edge function.
  After every major agent runs, LangGraph calls the orchestrator's
  routing function to decide what to do NEXT.

  This creates the "brain" that ties all agents together.
"""

from state import TripState
from config import MAX_RETRIES


# ════════════════════════════════════════════════════════════════════
# STEP 1 — Validate & understand user input
# ════════════════════════════════════════════════════════════════════

def orchestrator_validate_input(state: TripState) -> TripState:
    """
    LangGraph Node — Orchestrator: Input Validation
    -------------------------------------------------
    First thing the Orchestrator does.
    Checks if all required fields are present.
    Sets orchestrator_decision based on what it finds.
    """
    print("\n[Orchestrator] 🎯 STEP 1 — Analysing user request...")

    missing = []
    required_fields = [
        ("source",          "Source location"),
        ("destination",     "Destination"),
        ("travel_dates",    "Travel dates"),
        ("budget",          "Budget"),
        ("num_travelers",   "Number of travelers"),
        ("travel_type",     "Travel type"),
    ]

    for field, label in required_fields:
        val = state.get(field)
        if not val:
            missing.append(label)

    if missing:
        state["orchestrator_decision"] = "incomplete_input"
        state["errors"].append(f"Missing required fields: {', '.join(missing)}")
        print(f"[Orchestrator] ⚠  Missing fields: {missing}")
    else:
        state["orchestrator_decision"] = "proceed_to_memory"
        print(f"[Orchestrator] ✅ All required inputs present. "
              f"Planning trip: {state['source']} → {state['destination']} "
              f"({state['num_days']} days, Rs.{state['budget']:,})")

    state["messages"].append(
        f"[Orchestrator] Input check: {state['orchestrator_decision']}"
    )
    return state


# ════════════════════════════════════════════════════════════════════
# STEP 2 — Post-execution conflict resolution
# ════════════════════════════════════════════════════════════════════

def orchestrator_resolve_conflicts(state: TripState) -> TripState:
    """
    LangGraph Node — Orchestrator: Conflict Resolution
    ---------------------------------------------------
    Runs AFTER all data agents have completed.
    Checks for conflicts and decides whether any agent needs a retry.

    CONFLICT RULES:
      Hotel > budget       → flag for Budget Agent re-optimisation
      Heavy rain + outdoor → flag for Places Agent to go indoor
      Flight unavailable   → transport_data should have alternatives
      Budget exceeded      → add note, Orchestrator will approve if
                              overage is < 10% (reasonable buffer)
    """
    print("\n[Orchestrator] 🎯 STEP 3 — Checking for conflicts...")

    conflicts       = []
    retry_agents    = []
    budget_summary  = state.get("budget_summary", {})
    hotel_data      = state.get("hotel_data", {})
    weather_data    = state.get("weather_data", {})
    places_data     = state.get("places_data", {})
    transport_data  = state.get("transport_data", {})
    total_budget    = state.get("budget", 0)

    # ── Conflict 1: Hotel exceeds budget share ─────────────────────────
    hotel_options = hotel_data.get("options", [])
    if hotel_options:
        cheapest_hotel = min(h.get("total_cost", float("inf")) for h in hotel_options)
        hotel_budget   = total_budget * 0.45      # 45% max threshold
        if cheapest_hotel > hotel_budget:
            conflicts.append(
                f"Cheapest hotel (Rs.{cheapest_hotel:,}) > hotel budget threshold (Rs.{hotel_budget:,.0f})"
            )
            retry_agents.append("hotel")

    # ── Conflict 2: Heavy rain + outdoor activities ────────────────────
    rainfall_risk = weather_data.get("rainfall_risk", "low")
    is_indoor     = places_data.get("indoor_only", False)
    if rainfall_risk == "high" and not is_indoor:
        conflicts.append("Heavy rain expected but itinerary has outdoor activities")
        retry_agents.append("places")

    # ── Conflict 3: Budget exceeded by > 10% ──────────────────────────
    if not budget_summary.get("within_budget", True):
        estimated = budget_summary.get("estimated_total", 0)
        overage_pct = ((estimated - total_budget) / total_budget * 100) if total_budget else 0
        if overage_pct > 10:
            conflicts.append(
                f"Budget exceeded by {overage_pct:.1f}% — needs optimisation"
            )
            retry_agents.append("budget_rebalance")
        else:
            # Minor overage — acceptable, just log it
            conflicts.append(
                f"Minor budget overage ({overage_pct:.1f}%) — within acceptable range"
            )

    # ── Conflict 4: No transport options ──────────────────────────────
    if not transport_data.get("options"):
        conflicts.append("No transport options found — needs retry")
        retry_agents.append("transport")

    # ── Decision ──────────────────────────────────────────────────────
    if retry_agents:
        state["orchestrator_decision"] = f"retry:{','.join(retry_agents)}"
        for c in conflicts:
            print(f"[Orchestrator] ⚠  Conflict: {c}")
    else:
        state["orchestrator_decision"] = "run_itinerary_agent"
        if conflicts:
            for c in conflicts:
                print(f"[Orchestrator] ℹ  Note: {c}")
        else:
            print("[Orchestrator] ✅ No conflicts found. Proceeding to itinerary generation.")

    state["messages"].append(
        f"[Orchestrator] Conflict check: {state['orchestrator_decision']} | "
        f"Conflicts: {conflicts}"
    )
    return state


# ════════════════════════════════════════════════════════════════════
# STEP 4 — Final approval
# ════════════════════════════════════════════════════════════════════

def orchestrator_final_approval(state: TripState) -> TripState:
    """
    LangGraph Node — Orchestrator: Final Approval
    ----------------------------------------------
    The LAST check before the PDF is generated.
    Reviews what the Final Review Agent found.

    If review_status == 'needs_retry' AND retry_count < MAX_RETRIES:
      → Triggers specific agent retries
    If review_status == 'approved' OR retry_count >= MAX_RETRIES:
      → Approves and triggers PDF generation
    """
    print("\n[Orchestrator] 🎯 STEP 4 — Final approval check...")

    review_status = state.get("review_status", "pending")
    issues        = state.get("review_issues", [])
    retry_count   = state.get("retry_count", 0)

    if review_status == "approved":
        state["orchestrator_decision"] = "generate_pdf"
        print("[Orchestrator] ✅ APPROVED — triggering PDF generation")

    elif review_status == "needs_retry" and retry_count < MAX_RETRIES:
        state["retry_count"] = retry_count + 1
        # Determine which agents to retry based on issues
        retry = []
        for issue in issues:
            if "budget" in issue.lower():
                retry.append("budget")
            if "hotel" in issue.lower():
                retry.append("hotel")
            if "rain" in issue.lower() or "weather" in issue.lower():
                retry.append("places")
            if "transport" in issue.lower():
                retry.append("transport")
            if "itinerary" in issue.lower():
                retry.append("itinerary")

        if not retry:
            retry = ["review"]

        state["orchestrator_decision"] = f"retry:{','.join(set(retry))}"
        print(f"[Orchestrator] 🔄 Retry #{retry_count + 1} — agents: {retry}")
        print(f"[Orchestrator]    Issues: {issues}")

    else:
        # Max retries reached — approve anyway with warnings
        state["orchestrator_decision"] = "generate_pdf"
        if issues:
            state["messages"].append(
                f"[Orchestrator] WARNING: Generating PDF with unresolved issues "
                f"(max retries reached): {issues}"
            )
        print(f"[Orchestrator] ✅ Approving after {retry_count} retries. Generating PDF.")

    state["messages"].append(
        f"[Orchestrator] Final decision: {state['orchestrator_decision']}"
    )
    return state


# ════════════════════════════════════════════════════════════════════
# ROUTING FUNCTIONS (conditional edges for LangGraph)
# ════════════════════════════════════════════════════════════════════

def route_after_input_validation(state: TripState) -> str:
    """
    LangGraph Conditional Edge
    After input validation → where to go next?
    """
    decision = state.get("orchestrator_decision", "")
    if decision == "incomplete_input":
        return "end_with_error"
    return "memory_retrieval"


def route_after_conflict_check(state: TripState) -> str:
    """
    LangGraph Conditional Edge
    After conflict resolution → retry agents or run itinerary?
    """
    decision = state.get("orchestrator_decision", "")
    if decision.startswith("retry:"):
        # For this demo we'll proceed anyway (in production would loop back)
        print(f"[Orchestrator] 🔄 Note: Would retry {decision}. Proceeding for demo.")
        return "run_itinerary"
    return "run_itinerary"


def route_after_final_approval(state: TripState) -> str:
    """
    LangGraph Conditional Edge
    After final approval → generate PDF or retry?
    """
    decision = state.get("orchestrator_decision", "")
    if decision == "generate_pdf":
        return "generate_pdf"
    elif decision.startswith("retry:"):
        # In production this loops back; for demo, proceed
        print(f"[Orchestrator] 🔄 Note: Would retry agents. Proceeding to PDF.")
        return "generate_pdf"
    return "generate_pdf"
