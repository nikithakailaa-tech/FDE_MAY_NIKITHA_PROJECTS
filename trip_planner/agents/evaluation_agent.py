"""
Evaluation Agent
================
Uses OpenRouter LLM to score and evaluate the complete trip plan intelligently.
Falls back to rule-based scoring if LLM is unavailable.

SCORING BREAKDOWN (100 pts total):
  Budget Fit       25 pts
  Completeness     25 pts
  Weather Match    20 pts
  Data Quality     15 pts
  Transport Fit    15 pts

GRADES: Excellent (90+) | Good (75+) | Fair (60+) | Needs Improvement (<60)
"""

import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from state import TripState
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


def _build_evaluation_prompt(state: TripState) -> str:
    dest      = state.get("destination", "")
    budget    = state.get("budget_summary", {})
    hotel     = state.get("hotel_data", {})
    transport = state.get("transport_data", {})
    weather   = state.get("weather_data", {})
    itin      = state.get("itinerary", {})
    places    = state.get("places_data", {})
    days      = itin.get("days", [])

    activities_sample = []
    for d in days[:2]:
        for a in d.get("activities", [])[:2]:
            activities_sample.append(a.get("activity", ""))

    total_b = budget.get("total_budget", 1)
    est     = budget.get("estimated_total", 0)
    ratio   = round((est / total_b * 100), 1) if total_b else 0

    return f"""You are a travel plan quality evaluator. Score this trip plan out of 100.

TRIP TO EVALUATE: {dest}
- Duration: {state.get('num_days', 3)} days | Travelers: {state.get('num_travelers', 1)} ({state.get('travel_type', '')})
- Budget: ₹{total_b:,} | Estimated cost: ₹{est:,} ({ratio}% of budget used)
- Hotel: {hotel.get('recommended', 'None')} | Transport: {transport.get('recommended', 'None')}
- Weather: {weather.get('summary', 'N/A')} | Rainfall risk: {weather.get('rainfall_risk', 'low')}
- Places found: {places.get('total_places', 0)} | Days planned: {len(days)}
- Data sources: weather={weather.get('data_source', 'unknown')}, transport={transport.get('data_source', 'unknown')}, hotel={hotel.get('data_source', 'unknown')}
- Sample activities: {', '.join(activities_sample[:4]) if activities_sample else 'None'}
- Packing list: {'Yes' if itin.get('packing_checklist') else 'No'}
- Emergency contacts: {'Yes' if itin.get('emergency_contacts') else 'No'}

Score each category and explain WHY. Be specific to {dest}.

Return ONLY a valid JSON object:
{{
  "total_score": 82,
  "grade": "Good",
  "breakdown": {{
    "budget_fit":    {{"score": 20, "max": 25, "note": "specific reason mentioning actual numbers"}},
    "completeness":  {{"score": 22, "max": 25, "note": "specific reason about itinerary quality"}},
    "weather_match": {{"score": 15, "max": 20, "note": "specific reason about weather suitability"}},
    "data_quality":  {{"score": 13, "max": 15, "note": "specific reason about live vs static data"}},
    "transport_fit": {{"score": 12, "max": 15, "note": "specific reason about transport options"}}
  }},
  "recommendations": [
    "specific actionable tip 1 for this trip",
    "specific actionable tip 2 for this trip"
  ]
}}

Grade rules: 90-100=Excellent, 75-89=Good, 60-74=Fair, below 60=Needs Improvement
Make sure total_score equals sum of all category scores.
Return only JSON, no markdown, no extra text."""


def _llm_evaluate(state: TripState) -> dict:
    import time
    for attempt in range(2):
        try:
            prompt = _build_evaluation_prompt(state)
            resp = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a travel plan evaluator. Always respond with valid JSON only."},
                        {"role": "user",   "content": prompt},
                    ],
                    "temperature": 0.3,
                },
                timeout=30,
                verify=False,
            )
            if resp.status_code == 429:
                print(f"[EvaluationAgent] Rate limited, retrying in 3s...")
                time.sleep(3)
                continue
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw)
            bd = result.get("breakdown", {})
            actual_sum = sum(v.get("score", 0) for v in bd.values())
            result["total_score"] = actual_sum
            result["grade"] = _grade(actual_sum)
            return result
        except Exception as e:
            print(f"[EvaluationAgent] LLM error (attempt {attempt+1}): {e}")
            if attempt == 0:
                time.sleep(2)
    print("[EvaluationAgent] LLM unavailable — using rule-based fallback")
    return {}


def _grade(score: int) -> str:
    if score >= 90: return "Excellent"
    if score >= 75: return "Good"
    if score >= 60: return "Fair"
    return "Needs Improvement"


# ── Rule-based fallback ────────────────────────────────────────────────────

def _rule_score_budget(state):
    summary  = state.get("budget_summary", {})
    total    = summary.get("total_budget", 1)
    estimate = summary.get("estimated_total", 0)
    if not estimate:
        return 10, "Budget estimate unavailable"
    ratio = estimate / total
    if ratio <= 0.85: return 25, f"Excellent — uses only {ratio*100:.0f}% of budget"
    if ratio <= 1.00: return 20, f"Good — uses {ratio*100:.0f}% of budget"
    if ratio <= 1.10: return 10, f"Warning — exceeds budget by {(ratio-1)*100:.0f}%"
    return 0, f"Critical — exceeds budget by {(ratio-1)*100:.0f}%"


def _rule_score_completeness(state):
    itin  = state.get("itinerary", {})
    days  = itin.get("days", [])
    score = 0
    notes = []
    if days:
        score += 10
        with_acts  = sum(1 for d in days if d.get("activities"))
        with_meals = sum(1 for d in days if d.get("meals"))
        score += round(5 * with_acts / len(days))
        score += round(5 * with_meals / len(days))
        if with_acts < len(days): notes.append(f"{len(days)-with_acts} day(s) missing activities")
        if with_meals < len(days): notes.append(f"{len(days)-with_meals} day(s) missing meals")
    else:
        notes.append("No days in itinerary")
    if itin.get("packing_checklist"): score += 3
    else: notes.append("Packing checklist missing")
    if itin.get("emergency_contacts"): score += 2
    else: notes.append("Emergency contacts missing")
    return min(score, 25), ("Complete itinerary" if not notes else "; ".join(notes))


def _rule_score_weather(state):
    weather = state.get("weather_data", {})
    if not weather: return 5, "No weather data"
    risk  = weather.get("rainfall_risk", "low")
    score = {"low": 20, "medium": 12, "high": 4}.get(risk, 10)
    return score, f"{risk.capitalize()} rainfall risk"


def _rule_score_data(state):
    sources = [state.get(k, {}).get("data_source", "") for k in ("weather_data", "transport_data", "hotel_data", "places_data")]
    live = sum(1 for s in sources if any(x in s.lower() for x in ("live", "api", "serper", "openweather")))
    return round(live / max(len(sources), 1) * 15), f"{live}/{len(sources)} agents using live data"


def _rule_score_transport(state):
    transport = state.get("transport_data", {})
    if not transport or not transport.get("options"): return 5, "No transport options"
    return 12, "Transport options available"


def _rule_based_evaluate(state: TripState) -> dict:
    b, bn = _rule_score_budget(state)
    c, cn = _rule_score_completeness(state)
    w, wn = _rule_score_weather(state)
    d, dn = _rule_score_data(state)
    t, tn = _rule_score_transport(state)
    total = b + c + w + d + t

    recs = []
    if b < 15: recs.append("Consider increasing budget or reducing trip duration.")
    if c < 15: recs.append("Fill in missing activities and meal plans.")
    if w < 10: recs.append("Heavy rain expected — consider indoor activities.")
    if d < 10: recs.append("Configure all API keys for fully live results.")
    if not recs: recs.append("Trip plan looks great! Confirm your bookings.")

    return {
        "total_score": total,
        "grade": _grade(total),
        "breakdown": {
            "budget_fit":    {"score": b, "max": 25, "note": bn},
            "completeness":  {"score": c, "max": 25, "note": cn},
            "weather_match": {"score": w, "max": 20, "note": wn},
            "data_quality":  {"score": d, "max": 15, "note": dn},
            "transport_fit": {"score": t, "max": 15, "note": tn},
        },
        "recommendations": recs,
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

def evaluation_agent(state: TripState) -> TripState:
    print("\n[EvaluationAgent] 📊 LLM scoring trip plan quality...")

    result = {}
    if OPENROUTER_API_KEY:
        result = _llm_evaluate(state)

    if not result or "total_score" not in result:
        print("[EvaluationAgent] Using rule-based fallback")
        result = _rule_based_evaluate(state)
    else:
        print("[EvaluationAgent] LLM evaluation complete")

    state["evaluation"] = result

    total = result.get("total_score", 0)
    grade = result.get("grade", "N/A")
    print(f"[EvaluationAgent] Score: {total}/100 — {grade}")
    for cat, v in result.get("breakdown", {}).items():
        print(f"  {cat:<18} {v['score']:>3}/{v['max']}  {v['note']}")

    state["messages"].append(
        f"[EvaluationAgent] Score: {total}/100 ({grade}) | "
        + " | ".join(f"{k}: {v['score']}/{v['max']}" for k, v in result.get("breakdown", {}).items())
    )
    return state
