"""
Budget Agent
============
Aggregates costs from all agents and checks if the trip fits within budget.
If not, it suggests optimisation strategies.

Cost Categories:
  • Transport (flights/train/car)      — 30% of budget
  • Hotels                             — 40% of budget
  • Food & dining                      — 15% of budget
  • Activities / entry fees            — 10% of budget
  • Miscellaneous / emergency          —  5% of budget

Orchestrator uses review from this agent to:
  • Trigger Hotel Agent retry if accommodation > 40%
  • Trigger Transport Agent retry if travel > 35%
  • Flag budget breach to Final Review Agent
"""

import re
import math
from state import TripState


def _num_rooms(state) -> int:
    """
    Rooms to book — uses user's explicit num_rooms if provided,
    otherwise auto-calculates from travel type:
      solo     → 1 room
      couple   → 1 room  (they share)
      family   → ceil(travelers/2)
      friends  → ceil(travelers/2)  (club/share rooms)
      business → 1 room per person
    """
    # User explicitly set rooms from the UI
    if state.get("num_rooms") and int(state["num_rooms"]) > 0:
        return int(state["num_rooms"])

    travel_type   = (state.get("travel_type") or "solo").lower()
    num_travelers = max(1, state.get("num_travelers", 1))

    if travel_type == "solo":
        return 1
    elif travel_type == "couple":
        return 1
    elif travel_type in ("friends", "group"):
        return max(1, math.ceil(num_travelers / 2))
    elif travel_type == "family":
        return max(1, math.ceil(num_travelers / 2))
    elif travel_type == "business":
        return num_travelers
    else:
        return max(1, math.ceil(num_travelers / 2))


def _extract_price_from_text(text: str) -> int:
    """Pull the first ₹ / Rs. amount from a snippet string."""
    text = text.replace(",", "")
    for pattern in [r"₹\s*(\d+)", r"Rs\.?\s*(\d+)", r"INR\s*(\d+)"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return 0


def _estimate_transport(state: TripState) -> int:
    """
    Best-effort transport cost:
      1. Try to extract price from Serper snippet text.
      2. Fall back to mode-based realistic defaults × num_travelers.
    """
    transport_data = state.get("transport_data", {})
    options        = transport_data.get("options", [])
    num_travelers  = state.get("num_travelers", 1)
    mode           = (transport_data.get("mode") or
                      state.get("transport_pref", "train")).lower()

    # Try to parse price from snippet
    for o in options:
        text = f"{o.get('details','')} {o.get('operator','')} {o.get('snippet','')}"
        price = _extract_price_from_text(text)
        if price and 50 < price < 50000:
            return price * num_travelers

    # Mode-based realistic defaults per person (one-way)
    defaults = {"flight": 4500, "train": 800, "bus": 400, "car": 2500}
    per_person = defaults.get(mode, 800)
    return per_person * num_travelers


def _estimate_hotel(state: TripState) -> int:
    """
    Best-effort hotel cost considering number of rooms needed.
      couple  → 1 room
      friends → ceil(travelers/2) rooms (clubbed sharing)
      family  → ceil(travelers/2) rooms
      business→ 1 room per person
      solo    → 1 room
    """
    hotel_data  = state.get("hotel_data", {})
    options     = hotel_data.get("options", [])
    num_days    = state.get("num_days", 3)
    tier        = (hotel_data.get("tier") or
                   state.get("luxury_or_budget", "mid-range")).lower()
    rooms       = _num_rooms(state)

    for o in options:
        text = f"{o.get('details','')} {o.get('name','')}"
        price = _extract_price_from_text(text)
        if price and 300 < price < 30000:
            return price * num_days * rooms

    # Tier-based realistic defaults per room per night
    tier_defaults = {"luxury": 4000, "mid-range": 2000, "budget": 900}
    per_night = tier_defaults.get(tier, 2000)
    return per_night * num_days * rooms


def _calculate_budget(state: TripState) -> dict:
    total_budget  = state.get("budget", 30000)
    num_days      = state.get("num_days", 3)
    num_travelers = state.get("num_travelers", 1)

    # ── Transport cost ─────────────────────────────────────────────────────
    transport_cost = _estimate_transport(state)

    # ── Hotel cost ────────────────────────────────────────────────────────
    hotel_cost = _estimate_hotel(state)

    # ── Food estimate ─────────────────────────────────────────────────────
    # Rough estimate: ₹500/person/meal × 3 meals × days
    food_cost = 500 * num_travelers * 3 * num_days

    # ── Activities estimate ───────────────────────────────────────────────
    # Average entry fee ₹300/person × 2 places/day
    activity_cost = 300 * num_travelers * 2 * num_days

    # ── Miscellaneous ─────────────────────────────────────────────────────
    misc_cost = 0.05 * total_budget

    # ── Totals ────────────────────────────────────────────────────────────
    estimated_total = transport_cost + hotel_cost + food_cost + activity_cost + misc_cost
    remaining       = total_budget - estimated_total
    within_budget   = estimated_total <= total_budget

    # ── Optimisation suggestions ──────────────────────────────────────────
    suggestions = []
    if not within_budget:
        overage = estimated_total - total_budget
        suggestions.append(f"Over budget by ₹{overage:,.0f}")
        if hotel_cost > total_budget * 0.45:
            suggestions.append("Switch to a lower-tier hotel to save ₹"
                                f"{hotel_cost - total_budget * 0.4:,.0f}")
        if transport_cost > total_budget * 0.35:
            suggestions.append("Consider train instead of flight to save ~₹"
                                f"{transport_cost * 0.4:,.0f}")
        suggestions.append("Reduce dining at premium restaurants by 1 meal/day")

    return {
        "total_budget":      total_budget,
        "estimated_total":   round(estimated_total, 2),
        "remaining":         round(remaining, 2),
        "within_budget":     within_budget,
        "breakdown": {
            "transport":    round(transport_cost, 2),
            "hotel":        round(hotel_cost, 2),
            "food":         round(food_cost, 2),
            "activities":   round(activity_cost, 2),
            "miscellaneous": round(misc_cost, 2),
        },
        "optimisation_tips": suggestions if suggestions else [
            "Budget looks healthy! Consider upgrading one dinner.",
            "You have a comfortable buffer for souvenirs and unexpected costs.",
        ],
        "per_person_cost":   round(estimated_total / max(num_travelers, 1), 2),
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

_TIER_ORDER = ["luxury", "mid-range", "budget"]
_MODE_ORDER = ["flight", "train", "bus"]


def budget_agent(state: TripState) -> TripState:
    """
    LangGraph Node — Budget Agent
    Calculates costs. If over budget, retries with cheaper hotel then cheaper
    transport. If still over budget after retries, sets budget_exceeded flag.
    """
    print("\n[BudgetAgent] 💰 Calculating total trip cost...")

    summary = _calculate_budget(state)
    state["budget_summary"] = summary

    # ── Auto-retry with cheaper options if over budget ─────────────────────
    if not summary["within_budget"]:
        overage = summary["estimated_total"] - summary["total_budget"]
        print(f"[BudgetAgent] ⚠  Over budget by ₹{overage:,.0f} — trying cheaper alternatives...")

        retried = False

        # Try 1: downgrade hotel tier
        current_tier = state.get("luxury_or_budget", "mid-range")
        tier_idx = _TIER_ORDER.index(current_tier) if current_tier in _TIER_ORDER else 1
        if tier_idx < len(_TIER_ORDER) - 1:
            cheaper_tier = _TIER_ORDER[tier_idx + 1]
            print(f"[BudgetAgent] 🔄 Retrying hotel with tier: {cheaper_tier}")
            from agents.hotel_agent import hotel_agent as _hotel_agent
            state["luxury_or_budget"] = cheaper_tier
            state = _hotel_agent(state)
            summary = _calculate_budget(state)
            state["budget_summary"] = summary
            retried = True

        # Try 2: if still over, downgrade transport mode
        if not summary["within_budget"]:
            current_mode = state.get("transport_pref", "train")
            mode_idx = _MODE_ORDER.index(current_mode) if current_mode in _MODE_ORDER else 0
            if mode_idx < len(_MODE_ORDER) - 1:
                cheaper_mode = _MODE_ORDER[mode_idx + 1]
                print(f"[BudgetAgent] 🔄 Retrying transport with mode: {cheaper_mode}")
                from agents.transport_agent import transport_agent as _transport_agent
                state["transport_pref"] = cheaper_mode
                state = _transport_agent(state)
                summary = _calculate_budget(state)
                state["budget_summary"] = summary
                retried = True

        if retried:
            print(f"[BudgetAgent] After retry — Estimated: ₹{summary['estimated_total']:,}")

    # ── Set budget_exceeded flag if still over after retries ───────────────
    if not summary["within_budget"]:
        overage = summary["estimated_total"] - summary["total_budget"]
        summary["budget_exceeded"] = True
        summary["budget_exceeded_message"] = (
            f"Your trip costs ₹{overage:,.0f} more than your budget of "
            f"₹{summary['total_budget']:,}. No cheaper alternatives found. "
            "Please increase your budget or reduce the number of days."
        )
        state["budget_summary"] = summary
        state["errors"].append("Budget exceeded after retries")
    else:
        summary["budget_exceeded"] = False
        state["budget_summary"] = summary

    status = "✅ Within budget" if summary["within_budget"] else "⚠  OVER BUDGET"
    msg = (f"{status} | Estimated: ₹{summary['estimated_total']:,} / "
           f"Budget: ₹{summary['total_budget']:,} | "
           f"Remaining: ₹{summary['remaining']:,}")
    state["messages"].append(f"[BudgetAgent] {msg}")
    print(f"[BudgetAgent] {msg}")
    return state
