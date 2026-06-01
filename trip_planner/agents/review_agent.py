"""
Final Review Agent
==================
Uses OpenRouter LLM to intelligently review the complete trip plan.
Falls back to rule-based checks if LLM is unavailable.

OUTPUTS:
  state['review_status']     = "approved" | "needs_retry"
  state['review_issues']     = list of problems found
  state['review_summary']    = human-readable LLM review paragraph
  state['review_highlights'] = positive aspects of the plan
"""

import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from state import TripState
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


def _build_review_prompt(state: TripState) -> str:
    dest      = state.get("destination", "")
    src       = state.get("source", "")
    budget    = state.get("budget_summary", {})
    hotel     = state.get("hotel_data", {})
    transport = state.get("transport_data", {})
    weather   = state.get("weather_data", {})
    itin      = state.get("itinerary", {})
    places    = state.get("places_data", {})
    days      = itin.get("days", [])

    day_summary = ""
    for d in days[:3]:
        acts = [a.get("activity", "") for a in d.get("activities", [])[:2]]
        day_summary += f"\n  Day {d.get('day')}: {', '.join(acts)}"

    return f"""You are a senior travel consultant reviewing a trip plan. Be helpful and specific.

TRIP SUMMARY:
- Route: {src} → {dest}
- Travelers: {state.get('num_travelers', 1)} ({state.get('travel_type', '')})
- Duration: {state.get('num_days', 3)} days | Dates: {state.get('travel_dates', '')}
- Total Budget: ₹{state.get('budget', 0):,}

WHAT THE AGENTS FOUND:
- Cost estimate: ₹{budget.get('estimated_total', 0):,} (within budget: {budget.get('within_budget', True)})
  Breakdown — Transport: ₹{budget.get('breakdown', {}).get('transport', 0):,} | Hotel: ₹{budget.get('breakdown', {}).get('hotel', 0):,} | Food: ₹{budget.get('breakdown', {}).get('food', 0):,}
- Hotel: {hotel.get('recommended', 'None')} (tier: {hotel.get('tier', '')})
- Transport: {transport.get('recommended', 'None')} | Mode: {transport.get('mode', '')}
- Weather: {weather.get('summary', 'Unknown')} | Temp: {weather.get('temperature', {}).get('min', '?')}–{weather.get('temperature', {}).get('max', '?')}°C | Rainfall risk: {weather.get('rainfall_risk', 'low')}
- Places found: {places.get('total_places', 0)} spots across {list(places.get('places', {}).keys())}
- Itinerary: {len(days)} days planned
- Sample itinerary:{day_summary}
- Packing checklist: {'Present' if itin.get('packing_checklist') else 'MISSING'}
- Emergency contacts: {'Present' if itin.get('emergency_contacts') else 'MISSING'}

Review this plan thoroughly. Return ONLY a valid JSON object:
{{
  "status": "approved",
  "issues": [],
  "summary": "2-3 sentences reviewing the overall trip plan quality and suitability",
  "highlights": ["strength 1", "strength 2", "strength 3"]
}}

Use "needs_retry" status only for serious problems (budget overrun, empty itinerary, no transport).
The "summary" must mention {dest} specifically and sound like a real travel consultant wrote it.
Return only JSON, no markdown, no extra text."""


def _llm_review(state: TripState) -> dict:
    import time
    for attempt in range(2):
        try:
            prompt = _build_review_prompt(state)
            resp = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a travel plan quality reviewer. Always respond with valid JSON only."},
                        {"role": "user",   "content": prompt},
                    ],
                    "temperature": 0.4,
                },
                timeout=30,
                verify=False,
            )
            if resp.status_code == 429:
                print(f"[ReviewAgent] Rate limited, retrying in 3s...")
                time.sleep(3)
                continue
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except Exception as e:
            print(f"[ReviewAgent] LLM error (attempt {attempt+1}): {e}")
            if attempt == 0:
                time.sleep(2)
    print("[ReviewAgent] LLM unavailable — using rule-based fallback")
    return {}


def _rule_based_review(state: TripState) -> dict:
    issues = []
    budget    = state.get("budget_summary", {})
    hotel     = state.get("hotel_data", {})
    weather   = state.get("weather_data", {})
    itin      = state.get("itinerary", {})
    places    = state.get("places_data", {})
    transport = state.get("transport_data", {})

    if not budget.get("within_budget", True):
        overage = budget.get("estimated_total", 0) - budget.get("total_budget", 0)
        issues.append(f"Budget exceeded by ₹{overage:,.0f}")
    if not hotel.get("recommended"):
        issues.append("No hotel recommendation found")
    if weather.get("rainfall_risk") == "high" and not places.get("indoor_only", False):
        issues.append("Heavy rain expected but outdoor-only plan — consider indoor alternatives")
    days = itin.get("days", [])
    if not days:
        issues.append("Itinerary is empty — no days planned")
    for day in days:
        if not day.get("activities"):
            issues.append(f"Day {day.get('day', '?')} has no activities")
    if not itin.get("packing_checklist"):
        issues.append("Packing checklist is missing")
    if not itin.get("emergency_contacts"):
        issues.append("Emergency contacts are missing")
    if not transport.get("options"):
        issues.append("No transport options found")

    status = "needs_retry" if issues else "approved"
    dest   = state.get("destination", "the destination")
    return {
        "status":     status,
        "issues":     issues,
        "summary":    f"Trip plan to {dest} reviewed. {'All checks passed.' if not issues else f'{len(issues)} issue(s) found.'}",
        "highlights": ["Live data used for search", "Budget calculated", "Itinerary generated"],
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

def final_review_agent(state: TripState) -> TripState:
    print("\n[ReviewAgent] 🔍 LLM reviewing complete trip plan...")

    result = {}
    if OPENROUTER_API_KEY:
        result = _llm_review(state)

    if not result or "status" not in result:
        print("[ReviewAgent] Using rule-based fallback")
        result = _rule_based_review(state)
    else:
        print("[ReviewAgent] LLM review complete")

    state["review_status"]     = result.get("status", "approved")
    state["review_issues"]     = result.get("issues", [])
    state["review_summary"]    = result.get("summary", "")
    state["review_highlights"] = result.get("highlights", [])

    for issue in result.get("issues", []):
        print(f"[ReviewAgent] Issue: {issue}")
    print(f"[ReviewAgent] {result.get('summary', '')}")

    state["messages"].append(
        f"[ReviewAgent] {state['review_status'].upper()} — {state['review_summary']}"
    )
    return state
