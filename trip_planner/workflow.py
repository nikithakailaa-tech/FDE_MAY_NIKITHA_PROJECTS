"""
Main LangGraph Workflow
========================
This is where everything comes together.

GRAPH STRUCTURE:
  START
    → orchestrator_validate_input    [Checkpoint 1 — input valid?]
    → memory_retrieval_agent
    → weather_agent
    → transport_agent
    → hotel_agent
    → places_explorer_agent
    → budget_agent
    → orchestrator_resolve_conflicts [Checkpoint 2 — conflicts?]
    → itinerary_agent
    → final_review_agent
    → evaluation_agent
    → orchestrator_final_approval    [Checkpoint 3 — plan good?]
    → memory_update_agent
    → pdf_generator_agent
  END

CONDITIONAL EDGES (3 decision gates):
  Checkpoint 1: missing fields → error END  |  ok → memory retrieval
  Checkpoint 2: conflicts found → flag + proceed  |  clean → itinerary
  Checkpoint 3: review failed → retry (max 3x)  |  approved → PDF
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from langgraph.graph import StateGraph, END
from state import TripState

# Import all agent nodes
from agents.orchestrator    import (
    orchestrator_validate_input,
    orchestrator_resolve_conflicts,
    orchestrator_final_approval,
    route_after_input_validation,
    route_after_conflict_check,
    route_after_final_approval,
)
from agents.memory_agent    import memory_retrieval_agent, memory_update_agent
from agents.weather_agent   import weather_agent
from agents.transport_agent import transport_agent
from agents.hotel_agent     import hotel_agent
from agents.places_agent    import places_explorer_agent
from agents.budget_agent    import budget_agent
from agents.itinerary_agent import itinerary_agent
from agents.review_agent     import final_review_agent
from agents.evaluation_agent import evaluation_agent
from agents.pdf_agent        import pdf_generator_agent


def build_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph workflow.

    Each .add_node() registers an agent function.
    Each .add_edge() defines the flow between agents.
    .add_conditional_edges() lets the Orchestrator decide routing.
    """
    graph = StateGraph(TripState)

    # ── Register all nodes ─────────────────────────────────────────────────
    graph.add_node("orchestrator_validate",    orchestrator_validate_input)
    graph.add_node("memory_retrieval",         memory_retrieval_agent)
    graph.add_node("weather",                  weather_agent)
    graph.add_node("transport",                transport_agent)
    graph.add_node("hotel",                    hotel_agent)
    graph.add_node("places",                   places_explorer_agent)
    graph.add_node("budget",                   budget_agent)
    graph.add_node("orchestrator_conflicts",   orchestrator_resolve_conflicts)
    graph.add_node("itinerary",                itinerary_agent)
    graph.add_node("review",                   final_review_agent)
    graph.add_node("evaluation",               evaluation_agent)
    graph.add_node("orchestrator_approval",    orchestrator_final_approval)
    graph.add_node("memory_update",            memory_update_agent)
    graph.add_node("pdf_generator",            pdf_generator_agent)

    # ── Entry point ───────────────────────────────────────────────────────
    graph.set_entry_point("orchestrator_validate")

    # ── Step 1: Input validation → conditional routing ────────────────────
    graph.add_conditional_edges(
        "orchestrator_validate",
        route_after_input_validation,
        {
            "memory_retrieval": "memory_retrieval",
            "end_with_error":   END,
        }
    )

    # ── Step 2: Memory retrieval → data agents ────────────────────────────
    # 4 agents run sequentially (logically independent data-gathering)
    graph.add_edge("memory_retrieval", "weather")
    graph.add_edge("weather",                  "transport")
    graph.add_edge("transport",                "hotel")
    graph.add_edge("hotel",                    "places")

    # ── Step 4: Budget aggregation ────────────────────────────────────────
    graph.add_edge("places", "budget")

    # ── Step 5: Orchestrator conflict check → conditional ─────────────────
    graph.add_edge("budget", "orchestrator_conflicts")
    graph.add_conditional_edges(
        "orchestrator_conflicts",
        route_after_conflict_check,
        {
            "run_itinerary": "itinerary",
        }
    )

    # ── Step 6: Itinerary → Final Review → Evaluation ────────────────────
    graph.add_edge("itinerary", "review")
    graph.add_edge("review",    "evaluation")

    # ── Step 7: Orchestrator final approval → conditional ─────────────────
    graph.add_edge("evaluation", "orchestrator_approval")
    graph.add_conditional_edges(
        "orchestrator_approval",
        route_after_final_approval,
        {
            "generate_pdf": "memory_update",
        }
    )

    # ── Step 8: Memory update → PDF → END ─────────────────────────────────
    graph.add_edge("memory_update", "pdf_generator")
    graph.add_edge("pdf_generator", END)

    return graph.compile()


# ── Helper: pretty print execution log ────────────────────────────────────

def print_execution_summary(final_state: TripState):
    print("\n" + "="*65)
    print("  EXECUTION SUMMARY")
    print("="*65)
    print(f"\n  Trip: {final_state['source']} → {final_state['destination']}")
    print(f"  Dates: {final_state['travel_dates']}")
    print(f"  Budget: Rs.{final_state['budget']:,} | Estimated: "
          f"Rs.{final_state.get('budget_summary', {}).get('estimated_total', 0):,}")
    print(f"\n  Review Status:  {final_state.get('review_status', 'N/A').upper()}")
    print(f"  PDF Status:     {final_state.get('pdf_status', 'N/A').upper()}")
    print(f"  PDF File:       {final_state.get('pdf_path', 'N/A')}")
    print(f"\n  Errors:  {final_state.get('errors', []) or 'None'}")
    print(f"\n  Agent Execution Log ({len(final_state.get('messages', []))} steps):")
    for m in final_state.get("messages", []):
        print(f"    → {m}")
    print("="*65)


# ── Main: run with sample trip ─────────────────────────────────────────────

def run_trip_planner(trip_request: dict) -> TripState:
    """
    Build and run the workflow with a trip request.

    Args:
        trip_request: dict with all trip parameters

    Returns:
        final_state: complete TripState with all results + PDF path
    """
    print("\n" + "="*65)
    print("  🌍  AI MULTI-AGENT TRIP PLANNER  — LangGraph Workflow")
    print("="*65)

    # ── Build default initial state ────────────────────────────────────────
    initial_state: TripState = {
        # User inputs
        "source":           trip_request.get("source", ""),
        "destination":      trip_request.get("destination", ""),
        "travel_dates":     trip_request.get("travel_dates", ""),
        "num_days":         trip_request.get("num_days", 3),
        "budget":           trip_request.get("budget", 20000),
        "num_travelers":    trip_request.get("num_travelers", 1),
        "travel_type":      trip_request.get("travel_type", "solo"),
        "hotel_pref":       trip_request.get("hotel_pref", "mid-range hotel"),
        "food_pref":        trip_request.get("food_pref", "local cuisine"),
        "transport_pref":   trip_request.get("transport_pref", "flight"),
        "seat_pref":        trip_request.get("seat_pref", "window"),
        "num_rooms":        trip_request.get("num_rooms", 1),
        "places_interest":   trip_request.get("places_interest", ["sightseeing"]),
        "luxury_or_budget":  trip_request.get("luxury_or_budget", "mid-range"),
        "must_visit_places": trip_request.get("must_visit_places", ""),
        # Memory
        "user_profile":  {},
        "past_trips":    [],
        # Agent outputs
        "weather_data":   {},
        "hotel_data":     {},
        "transport_data": {},
        "places_data":    {},
        "budget_summary": {},
        "itinerary":      {},
        # Control
        "review_status":     "pending",
        "review_issues":     [],
        "review_summary":    "",
        "review_highlights": [],
        "pdf_status":        "pending",
        "pdf_path":       "",
        # Guardrails & Evaluation
        "guardrail_warnings": [],
        "evaluation":         {},
        # Orchestrator
        "orchestrator_decision": "",
        "retry_count":    0,
        "errors":         [],
        "messages":       [],
    }

    # ── Build and run the graph ────────────────────────────────────────────
    app = build_graph()
    final_state = app.invoke(initial_state)

    print_execution_summary(final_state)
    return final_state


# ── Sample trip from assignment ────────────────────────────────────────────

if __name__ == "__main__":
    sample_trip = {
        "source":          "Bangalore",
        "destination":     "Goa",
        "travel_dates":    "June 10-15, 2025",
        "num_days":        5,
        "budget":          30000,
        "num_travelers":   2,
        "travel_type":     "couple",
        "hotel_pref":      "beach resort",
        "food_pref":       "seafood",
        "transport_pref":  "flight",
        "places_interest": ["beach", "nightlife", "sightseeing"],
        "luxury_or_budget":"mid-range",
    }

    final = run_trip_planner(sample_trip)
    if final.get("pdf_path"):
        print(f"\n  ✅ Download your PDF: {final['pdf_path']}")
