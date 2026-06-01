"""
Guardrails
==========
Input validation and safety checks run BEFORE the workflow starts
and after each agent output. Returns structured pass/fail results.
"""

import re
from typing import Dict, Any


# ── Input Guardrails ───────────────────────────────────────────────────────

def validate_inputs(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all user inputs before the workflow runs.
    Returns {"passed": bool, "errors": [...], "warnings": [...]}.
    """
    errors   = []
    warnings = []

    source      = str(data.get("source", "")).strip()
    destination = str(data.get("destination", "")).strip()
    dates       = str(data.get("travel_dates", "")).strip()
    num_days    = data.get("num_days", 0)
    budget      = data.get("budget", 0)
    num_trav    = data.get("num_travelers", 0)

    # ── Required fields ────────────────────────────────────────────────────
    if not source:
        errors.append("Source city is required.")
    if not destination:
        errors.append("Destination city is required.")
    if not dates:
        errors.append("Travel dates are required.")

    # ── Source ≠ Destination (including aliases) ──────────────────────────
    _ALIASES = {
        "bangalore": {"bengaluru", "bangaluru", "blr"},
        "bengaluru": {"bangalore", "bangaluru", "blr"},
        "mumbai":    {"bombay"},
        "bombay":    {"mumbai"},
        "chennai":   {"madras"},
        "madras":    {"chennai"},
        "kolkata":   {"calcutta"},
        "calcutta":  {"kolkata"},
        "kochi":     {"cochin", "ernakulam"},
        "cochin":    {"kochi", "ernakulam"},
        "thiruvananthapuram": {"trivandrum"},
        "trivandrum": {"thiruvananthapuram"},
        "vadodara":  {"baroda"},
        "baroda":    {"vadodara"},
        "visakhapatnam": {"vizag", "vishakhapatnam"},
        "vizag":     {"visakhapatnam", "vishakhapatnam"},
        "mysuru":    {"mysore"},
        "mysore":    {"mysuru"},
        "varanasi":  {"banaras", "benares", "kashi"},
        "prayagraj": {"allahabad"},
        "delhi":     {"new delhi"},
        "new delhi": {"delhi"},
        "pune":      {"poona"},
        "shimla":    {"simla"},
        "simla":     {"shimla"},
    }
    src_l  = source.lower().strip()
    dest_l = destination.lower().strip()
    if source and destination:
        same = src_l == dest_l
        if not same:
            src_aliases  = _ALIASES.get(src_l,  set()) | {src_l}
            dest_aliases = _ALIASES.get(dest_l, set()) | {dest_l}
            same = bool(src_aliases & dest_aliases)
        if same:
            errors.append(
                f"'{source}' and '{destination}' are the same city. "
                "Please enter a different destination."
            )

    # ── Budget range ───────────────────────────────────────────────────────
    try:
        budget = float(budget)
        if budget < 500:
            errors.append("Budget must be at least ₹500.")
        elif budget > 10_000_000:
            errors.append("Budget exceeds maximum allowed value (₹1 crore).")
        elif budget < 5000:
            warnings.append("Budget is very low — plan may be limited.")
    except (ValueError, TypeError):
        errors.append("Budget must be a valid number.")

    # ── Number of days ─────────────────────────────────────────────────────
    try:
        num_days = int(num_days)
        if num_days < 2:
            errors.append("Trip must be at least 2 days.")
        elif num_days > 90:
            errors.append("Trip duration cannot exceed 90 days.")
        elif num_days > 30:
            warnings.append("Very long trip (>30 days) — itinerary may be approximate.")
    except (ValueError, TypeError):
        errors.append("Number of days must be a valid integer.")

    # ── Number of travelers ────────────────────────────────────────────────
    try:
        num_trav = int(num_trav)
        if num_trav < 1:
            errors.append("At least 1 traveler is required.")
        elif num_trav > 50:
            errors.append("Cannot plan for more than 50 travelers at once.")
        elif num_trav > 20:
            warnings.append("Large group (>20 travelers) — consider group booking discounts.")
    except (ValueError, TypeError):
        errors.append("Number of travelers must be a valid integer.")

    # ── Injection / script safety ──────────────────────────────────────────
    text_fields = [source, destination, dates,
                   str(data.get("hotel_pref", "")),
                   str(data.get("food_pref", ""))]
    pattern = re.compile(r"[<>\"'`]|--|;|script|DROP|SELECT|INSERT|DELETE", re.IGNORECASE)
    for field in text_fields:
        if pattern.search(field):
            errors.append("Input contains invalid characters or potential injection attempt.")
            break

    # ── Minimum budget per person per day ─────────────────────────────────
    if not errors and budget and num_days and num_trav:
        per_person_per_day = budget / (num_days * num_trav)
        if per_person_per_day < 200:
            warnings.append(
                f"Budget of ₹{per_person_per_day:.0f}/person/day is very tight — "
                "expect limited options."
            )

    return {
        "passed":   len(errors) == 0,
        "errors":   errors,
        "warnings": warnings,
    }


# ── Output Guardrails (per-agent sanity checks) ────────────────────────────

def check_weather_output(weather_data: Dict) -> list[str]:
    issues = []
    if not weather_data:
        issues.append("Weather agent returned no data.")
    elif not weather_data.get("summary") and not weather_data.get("temperature"):
        issues.append("Weather data is incomplete — missing summary or temperature.")
    return issues


def check_transport_output(transport_data: Dict) -> list[str]:
    issues = []
    if not transport_data:
        issues.append("Transport agent returned no data.")
    elif not transport_data.get("options"):
        issues.append("Transport agent found no options.")
    return issues


def check_hotel_output(hotel_data: Dict) -> list[str]:
    issues = []
    if not hotel_data:
        issues.append("Hotel agent returned no data.")
    elif not hotel_data.get("options") and not hotel_data.get("recommended"):
        issues.append("Hotel agent found no options.")
    return issues


def check_places_output(places_data: Dict) -> list[str]:
    issues = []
    if not places_data:
        issues.append("Places agent returned no data.")
    elif places_data.get("total_places", 0) == 0:
        issues.append("Places agent found no attractions or food spots.")
    return issues


def check_itinerary_output(itinerary: Dict) -> list[str]:
    issues = []
    if not itinerary:
        issues.append("Itinerary agent returned no data.")
        return issues
    days = itinerary.get("days", [])
    if not days:
        issues.append("Itinerary has no days planned.")
    else:
        for day in days:
            if not day.get("activities"):
                issues.append(f"Day {day.get('day', '?')} has no activities.")
            if not day.get("meals"):
                issues.append(f"Day {day.get('day', '?')} has no meal plan.")
    if not itinerary.get("packing_checklist"):
        issues.append("Itinerary is missing a packing checklist.")
    return issues


def run_output_guardrails(state: Dict) -> Dict[str, Any]:
    """
    Run all output guardrails on a completed state.
    Returns {"passed": bool, "issues": [...]}.
    """
    issues = []
    issues += check_weather_output(state.get("weather_data", {}))
    issues += check_transport_output(state.get("transport_data", {}))
    issues += check_hotel_output(state.get("hotel_data", {}))
    issues += check_places_output(state.get("places_data", {}))
    issues += check_itinerary_output(state.get("itinerary", {}))

    return {
        "passed": len(issues) == 0,
        "issues": issues,
    }
