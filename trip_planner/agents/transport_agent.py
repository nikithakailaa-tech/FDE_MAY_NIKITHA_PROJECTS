"""
Transport Agent
===============
Finds best travel options (flights / trains / car) between source and destination.

REAL IMPLEMENTATION  → Serper API (Google Search) — active when SERPER_API_KEY is set
FALLBACK             → Empty options with error message if API key is missing
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from state import TripState
from config import SERPER_API_KEY, OPENWEATHER_API_KEY

SERPER_URL = "https://google.serper.dev/search"


def _serper_search(query: str) -> list[dict]:
    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": 6},
            timeout=8,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("organic", [])
        # answerBox often has direct answers for transport queries
        ab = data.get("answerBox", {})
        if ab.get("title") and ab.get("snippet"):
            results.insert(0, {"title": ab["title"], "snippet": ab["snippet"], "link": ""})
        return results[:6]
    except Exception as e:
        print(f"[TransportAgent] Serper error: {e}")
        return []


def _parse_transport(results: list[dict], mode: str, source: str,
                     destination: str, num_travelers: int) -> dict:
    options = []
    for r in results[:3]:
        title   = r.get("title", "").split(" - ")[0].split(" | ")[0].strip()
        snippet = r.get("snippet", "")
        options.append({
            "operator":   title,
            "mode":       mode,
            "details":    snippet[:150],
            "source_url": r.get("link", ""),
            "travelers":  num_travelers,
        })

    return {
        "mode":       mode,
        "options":    options,
        "recommended": options[0]["operator"] if options else "See results above",
        "data_source": "Serper / Google Search (live)",
        "search_tip":  f"Book directly via airline/railway site for best price",
    }


def _get_lat_lng(city: str):
    """Get lat/lng for a city using OpenWeatherMap geocoding API."""
    try:
        resp = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct"
            f"?q={city},IN&limit=1&appid={OPENWEATHER_API_KEY}",
            timeout=5, verify=False,
        )
        data = resp.json()
        if data:
            return round(data[0]["lat"], 4), round(data[0]["lon"], 4)
    except Exception:
        pass
    return None, None


# Known Indian city → nearest major transport hub (airport / railway junction)
_HUB_MAP = {
    # Andhra Pradesh / Telangana
    "tirupati":       ("Chennai", "~2.5 hours by road"),
    "nellore":        ("Chennai", "~2 hours by road"),
    "kadapa":         ("Tirupati", "~2 hours by road"),
    "kurnool":        ("Hyderabad", "~3 hours by road"),
    "anantapur":      ("Bengaluru", "~2.5 hours by road"),
    "rajahmundry":    ("Visakhapatnam", "~2 hours by road"),
    "eluru":          ("Vijayawada", "~1 hour by road"),
    "ongole":         ("Vijayawada", "~2 hours by road"),
    "machilipatnam":  ("Vijayawada", "~1.5 hours by road"),
    "srikakulam":     ("Visakhapatnam", "~2 hours by road"),
    "vizianagaram":   ("Visakhapatnam", "~1 hour by road"),
    "kakinada":       ("Rajahmundry", "~1 hour by road"),
    "warangal":       ("Hyderabad", "~2.5 hours by road"),
    "karimnagar":     ("Hyderabad", "~2 hours by road"),
    "nizamabad":      ("Hyderabad", "~2.5 hours by road"),
    "khammam":        ("Hyderabad", "~3 hours by road"),
    # Karnataka
    "mysore":         ("Bengaluru", "~3 hours by road"),
    "mysuru":         ("Bengaluru", "~3 hours by road"),
    "hubli":          ("Bengaluru", "~5 hours by road"),
    "mangalore":      ("Bengaluru", "~6 hours by road"),
    "gulbarga":       ("Hyderabad", "~2 hours by road"),
    "bellary":        ("Bengaluru", "~5 hours by road"),
    "shimoga":        ("Bengaluru", "~4 hours by road"),
    "tumkur":         ("Bengaluru", "~1.5 hours by road"),
    # Tamil Nadu
    "madurai":        ("Chennai", "~8 hours / fly direct"),
    "coimbatore":     ("Chennai", "~5 hours by road"),
    "trichy":         ("Chennai", "~5 hours by road"),
    "tirunelveli":    ("Madurai", "~2 hours by road"),
    "salem":          ("Coimbatore", "~2 hours by road"),
    "vellore":        ("Chennai", "~2 hours by road"),
    "ooty":           ("Coimbatore", "~1.5 hours by road"),
    # Kerala
    "thrissur":       ("Kochi", "~1 hour by road"),
    "palakkad":       ("Coimbatore", "~1.5 hours by road"),
    "kozhikode":      ("Kochi", "~3 hours by road"),
    "malappuram":     ("Kochi", "~2.5 hours by road"),
    "kannur":         ("Kochi", "~5 hours by road"),
    "kollam":         ("Thiruvananthapuram", "~1 hour by road"),
    "kottayam":       ("Kochi", "~1.5 hours by road"),
    # Maharashtra
    "nashik":         ("Mumbai", "~3 hours by road"),
    "aurangabad":     ("Pune", "~5 hours by road"),
    "kolhapur":       ("Pune", "~3 hours by road"),
    "solapur":        ("Pune", "~4 hours by road"),
    "nagpur":         ("Nagpur", "direct hub"),
    "nanded":         ("Hyderabad", "~3 hours by road"),
    "latur":          ("Hyderabad", "~3.5 hours by road"),
    "amravati":       ("Nagpur", "~2.5 hours by road"),
    # Gujarat
    "vadodara":       ("Ahmedabad", "~2 hours by road"),
    "surat":          ("Ahmedabad", "~3 hours by road"),
    "rajkot":         ("Ahmedabad", "~3.5 hours by road"),
    "bhavnagar":      ("Ahmedabad", "~3 hours by road"),
    "junagadh":       ("Rajkot", "~2 hours by road"),
    # Rajasthan
    "ajmer":          ("Jaipur", "~2.5 hours by road"),
    "udaipur":        ("Jaipur", "~5 hours by road"),
    "jodhpur":        ("Jaipur", "~5 hours by road"),
    "kota":           ("Jaipur", "~4 hours by road"),
    "bikaner":        ("Jaipur", "~5 hours by road"),
    # UP / Bihar
    "agra":           ("Delhi", "~3 hours by road"),
    "allahabad":      ("Varanasi", "~2 hours by road"),
    "prayagraj":      ("Varanasi", "~2 hours by road"),
    "mathura":        ("Delhi", "~2.5 hours by road"),
    "aligarh":        ("Delhi", "~2 hours by road"),
    "bareilly":       ("Delhi", "~5 hours by road"),
    "gaya":           ("Patna", "~2 hours by road"),
    "muzaffarpur":    ("Patna", "~2 hours by road"),
    # Madhya Pradesh
    "gwalior":        ("Delhi", "~4 hours by road"),
    "jabalpur":       ("Bhopal", "~3 hours by road"),
    "ujjain":         ("Bhopal", "~2 hours by road"),
    "sagar":          ("Bhopal", "~2.5 hours by road"),
    # North East / Hills
    "shimla":         ("Chandigarh", "~2 hours by road"),
    "manali":         ("Chandigarh", "~6 hours by road"),
    "dharamshala":    ("Chandigarh", "~5 hours by road"),
    "dehradun":       ("Delhi", "~5 hours by road"),
    "haridwar":       ("Dehradun", "~1 hour by road"),
    "rishikesh":      ("Dehradun", "~1 hour by road"),
    "gangtok":        ("Bagdogra", "~4 hours by road"),
    "darjeeling":     ("Bagdogra", "~3 hours by road"),
    "shillong":       ("Guwahati", "~2.5 hours by road"),
    "imphal":         ("Guwahati", "~9 hours / fly direct"),
}


def _find_nearest_hub(source: str, mode: str) -> dict:
    """
    Find nearest boarding hub.
    1. Check hardcoded lookup table first (fast, reliable)
    2. Fall back to Serper search with city name (not lat/lng)
    """
    src_lower = source.lower().strip()

    # Step 1: Lookup table
    if src_lower in _HUB_MAP:
        hub_name, travel_time = _HUB_MAP[src_lower]
        lat, lng = _get_lat_lng(source)
        print(f"[TransportAgent] Hub lookup: {source} -> {hub_name} ({travel_time})")
        return {"hub": hub_name, "lat": lat, "lng": lng, "travel_time": travel_time}

    # Step 2: Serper search using city name (more reliable than lat/lng)
    lat, lng = _get_lat_lng(source)
    if mode == "flight":
        query = f"nearest airport to {source} India"
    elif mode == "train":
        query = f"nearest major railway junction to {source} India"
    else:
        query = f"nearest major bus stand to {source} India"

    results = _serper_search(query)
    if not results:
        return {}

    title   = results[0].get("title", "").split(" - ")[0].split(" | ")[0].strip()[:60]
    snippet = results[0].get("snippet", "").lower()

    if "30 min" in snippet or "half hour" in snippet:
        travel_time = "~30 minutes by road"
    elif "1 hour" in snippet or "60 min" in snippet:
        travel_time = "~1 hour by road"
    elif "2 hour" in snippet:
        travel_time = "~2 hours by road"
    elif "3 hour" in snippet:
        travel_time = "~3 hours by road"
    else:
        travel_time = "1–3 hours by road (verify locally)"

    print(f"[TransportAgent] Nearest {mode} hub for {source}: {title} ({travel_time})")
    return {"hub": title, "lat": lat, "lng": lng, "travel_time": travel_time}


def _get_transport_live(source: str, destination: str, dates: str,
                        mode: str, num_travelers: int, seat_pref: str = "") -> dict:
    print(f"[TransportAgent] Calling Serper API for {mode} {source} -> {destination} seat={seat_pref}...")

    seat_hint = seat_pref.replace("_", " ") if seat_pref else ""

    if mode == "train":
        tier = seat_pref if seat_pref in ("1A","2A","3A","SL","CC","EC") else ""
        direct_query = f"best trains {source} to {destination} {tier} IRCTC schedule".strip()
    elif mode == "bus":
        direct_query = f"bus services {source} to {destination} {seat_hint} redbus".strip()
    elif mode == "car":
        driver = "with driver" if seat_pref == "with_driver" else "self drive"
        direct_query = f"{driver} cab {source} to {destination} distance route"
    else:
        direct_query = f"flights {source} to {destination} airlines schedule {seat_hint}".strip()

    results = _serper_search(direct_query)
    data    = _parse_transport(results, mode, source, destination, num_travelers)

    # ── No-service fallback: find nearest boarding hub via lat/lng ────────────
    if len(results) < 2 and mode != "car":
        print(f"[TransportAgent] ⚠️  Few/no direct results — finding nearest hub for {source} via lat/lng...")
        hub_info = _find_nearest_hub(source, mode)
        hub_name = hub_info.get("hub", "")

        if hub_name and hub_name.lower() not in source.lower():
            # Search again from the hub
            if mode == "train":
                hub_query = f"best trains {hub_name} to {destination} IRCTC schedule"
            elif mode == "bus":
                hub_query = f"bus services {hub_name} to {destination} redbus"
            else:
                hub_query = f"flights {hub_name} to {destination} airlines schedule"

            hub_results = _serper_search(hub_query)
            hub_data    = _parse_transport(hub_results, mode, hub_name, destination, num_travelers)

            travel_time = hub_info.get("travel_time", "30 min – 3 hours by road")
            lat, lng    = hub_info.get("lat"), hub_info.get("lng")

            for opt in hub_data["options"]:
                opt["boarding_note"] = f"Board from {hub_name} — {travel_time} from {source}"

            hub_data["nearest_hub"]    = hub_name
            hub_data["hub_lat"]        = lat
            hub_data["hub_lng"]        = lng
            hub_data["hub_travel_time"] = travel_time
            hub_data["boarding_alert"] = (
                f"No direct {mode} service from {source}. "
                f"Nearest boarding point: {hub_name} ({travel_time}). "
                f"You must travel personally from {source} to {hub_name} first."
            )
            hub_data["personal_travel_required"] = True
            hub_data["local_transfer"] = (
                f"Travel personally: {source} → {hub_name} by local cab / bus / auto ({travel_time})"
            )

            # If hub search also returned nothing, mark no tickets
            if not hub_data["options"]:
                hub_data["no_tickets_available"] = True
                hub_data["no_tickets_message"]   = (
                    f"No {mode} tickets found from {source} or nearest hub ({hub_name}) "
                    f"to {destination}. Please try a different transport mode."
                )
            return hub_data

    # ── No results at all → no tickets ────────────────────────────────────
    if not data["options"]:
        data["no_tickets_available"] = True
        data["no_tickets_message"]   = (
            f"No {mode} tickets found from {source} to {destination}. "
            "Please try a different transport mode or travel dates."
        )
    return data


# ── Fallback mock data ─────────────────────────────────────────────────────

def _no_key_result(mode: str) -> dict:
    return {
        "mode":        mode,
        "options":     [],
        "recommended": "Configure SERPER_API_KEY for live results",
        "data_source": "No API key — configure SERPER_API_KEY in .env",
        "message":     f"Add SERPER_API_KEY to .env to get live {mode} options for any route.",
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

def transport_agent(state: TripState) -> TripState:
    src   = state["source"]
    dest  = state["destination"]
    dates = state["travel_dates"]
    pref      = state.get("transport_pref", "flight").lower()
    seat_pref = state.get("seat_pref", "window")
    n         = state.get("num_travelers", 1)

    print(f"\n[TransportAgent] Finding {pref} ({seat_pref}) options: {src} -> {dest}...")

    if SERPER_API_KEY:
        data = _get_transport_live(src, dest, dates, pref, n, seat_pref)
    else:
        print("[TransportAgent] ⚠️  No Serper key — cannot fetch live transport data")
        data = _no_key_result(pref)

    data["seat_pref"] = seat_pref
    state["transport_data"] = data
    num_opts = len(data.get("options", []))
    msg = f"Transport ({pref}, {seat_pref}): found {num_opts} options via {data.get('data_source', 'live')}"
    state["messages"].append(f"[TransportAgent] {msg}")
    print(f"[TransportAgent] ✅ {msg}")
    return state
