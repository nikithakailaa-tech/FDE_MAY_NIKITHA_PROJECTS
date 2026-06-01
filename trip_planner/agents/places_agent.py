"""
Places Explorer Agent
=====================
Discovers tourist attractions, local experiences, and food spots.

REAL IMPLEMENTATION  → Serper API (Google Search) — active when SERPER_API_KEY is set
FALLBACK             → Empty results with error message if API key is missing
"""

import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from state import TripState
from config import SERPER_API_KEY


SERPER_URL = "https://google.serper.dev/search"

# Curated nearby day-trip destinations for major Indian cities (1–3 hr drive)
_NEARBY_DAYTRIPS = {
    "visakhapatnam": ["Araku Valley", "Lambasingi", "Borra Caves", "Ananthagiri Hills", "Bheemunipatnam"],
    "vizag":         ["Araku Valley", "Lambasingi", "Borra Caves", "Ananthagiri Hills"],
    "bangalore":     ["Nandi Hills", "Chikballapur", "Mysore", "Coorg", "Chikmagalur", "Skandagiri"],
    "bengaluru":     ["Nandi Hills", "Chikballapur", "Mysore", "Coorg", "Chikmagalur", "Skandagiri"],
    "chennai":       ["Mahabalipuram", "Pondicherry", "Vellore Fort", "Tirupati", "Kanchipuram"],
    "hyderabad":     ["Nagarjuna Sagar", "Warangal", "Gandikota", "Bidar", "Medak"],
    "mumbai":        ["Lonavala", "Khandala", "Matheran", "Karjat", "Alibaug"],
    "pune":          ["Lonavala", "Mahabaleshwar", "Lavasa", "Sinhagad Fort", "Imagica"],
    "delhi":         ["Agra", "Mathura", "Vrindavan", "Haridwar", "Rishikesh"],
    "new delhi":     ["Agra", "Mathura", "Vrindavan", "Haridwar", "Rishikesh"],
    "kolkata":       ["Sundarbans", "Digha", "Murshidabad", "Santiniketan"],
    "jaipur":        ["Ajmer", "Pushkar", "Ranthambore", "Abhaneri"],
    "kochi":         ["Munnar", "Alleppey", "Thrissur", "Wayanad"],
    "cochin":        ["Munnar", "Alleppey", "Thrissur", "Wayanad"],
    "ahmedabad":     ["Vadodara", "Anand", "Modhera", "Patan"],
    "indore":        ["Mandu", "Maheshwar", "Omkareshwar", "Ujjain"],
    "bhopal":        ["Bhimbetka", "Sanchi", "Pachmarhi", "Raisen"],
    "goa":           ["Dudhsagar Falls", "Hampi", "Dandeli", "Mollem"],
    "mysore":        ["Coorg", "Nagarhole", "Bandipur", "Ooty"],
    "mysuru":        ["Coorg", "Nagarhole", "Bandipur", "Ooty"],
    "coimbatore":    ["Ooty", "Kodaikanal", "Valparai", "Pollachi"],
    "nagpur":        ["Pench", "Tadoba", "Ramtek", "Wardha"],
    "varanasi":      ["Sarnath", "Allahabad", "Chunar Fort", "Vindhyachal"],
    "lucknow":       ["Agra", "Mathura", "Dudhwa", "Naimisharanya"],
    "chandigarh":    ["Shimla", "Kasauli", "Morni Hills", "Nalagarh"],
    "amritsar":      ["Wagah Border", "Pathankot", "Dalhousie", "Chintpurni"],
}

# Titles that are article/listicle headers, not specific place names
_ARTICLE_SIGNALS = [
    "best ", "top ", "things to do", "places to visit", "places to see",
    "must visit", "things to see", "guide to", "2025", "2026", "2024",
    "tripadvisor", "timeout", "reddit", ": r/", "what are", "go to food",
    "favourite", "list of", "travel guide", "worth visiting", "planning a trip",
    "you'll need", "complete guide", "ultimate guide", "day trip", "tourist guide",
]

# Names that look like institutions/infrastructure, not tourist places
_NON_PLACE_SIGNALS = [
    "university", "college", "school", "hospital", "institute", "corporation",
    "municipality", "government", "police", "station", "tourism", " r/",
    "wikipedia", "?", "...", "you'll", "planning a", "which area", "close to",
    "beautiful beaches", " of vizag", " of india", "from ovenstory", "from deepak",
    "day trips", "camping", "trekking", "tour in", "romantic", "getaway",
    "$", "₹", "weekend", "itinerary", "package", "trip from",
]

_SENTENCE_STARTERS = ("in ", "what ", "which ", "how ", "why ", "where ", "when ",
                       "is ", "are ", "was ", "the best", "a list", "an overview")


def _is_article_title(title: str) -> bool:
    t = title.lower()
    return any(sig in t for sig in _ARTICLE_SIGNALS)


def _is_valid_place_name(name: str) -> bool:
    """Return False for institution names, article remnants, or garbage."""
    n = name.lower().strip()
    if any(sig in n for sig in _NON_PLACE_SIGNALS):
        return False
    if len(name) < 4 or len(name) > 60:
        return False
    if name.endswith("...") or "?" in name or "," in name:
        return False
    # Reject names that start like sentences
    if any(n.startswith(s) for s in _SENTENCE_STARTERS):
        return False
    # Reject names with too many words (>6 is likely a sentence, not a place)
    if len(name.split()) > 6:
        return False
    return True


def _names_from_snippet(snippet: str, max_items: int = 5) -> list:
    """
    Extract individual place/restaurant names from a Serper snippet that
    contains a numbered or bullet-separated list.
    e.g. "1. RK Beach · 2. Rushikonda Beach · 3. ..."
      or "Waltair Club · Blue Fox · Hotel Daspalla"
    """
    # Pattern 1: numbered list  "1. Name · 2. Name"
    numbered = re.findall(
        r'\d+\.\s+([A-Z][^·\n\d(]{2,45}?)(?:\s*[·•]\s*|\s*\n|$)',
        snippet
    )
    if len(numbered) >= 2:
        return [n.strip().rstrip('.,') for n in numbered[:max_items]]

    # Pattern 2: bullet/mid-dot separated  "Name · Name · Name"
    if '·' in snippet:
        parts = [p.strip() for p in snippet.split('·')]
        valid = [
            p.rstrip('.,') for p in parts
            if 3 < len(p.strip()) < 55
            and not p.strip()[0].isdigit()
            and not any(s in p.lower() for s in ['see more', 'read more', 'view all', 'rated', 'reviews'])
        ]
        if len(valid) >= 2:
            return valid[:max_items]

    # Pattern 3: "Name (4.2 ★)" — rating-annotated lists
    rated = re.findall(r'([A-Z][A-Za-z\s\'&]{3,40}?)\s*\([\d.]+', snippet)
    if len(rated) >= 2:
        return [n.strip() for n in rated[:max_items]]

    return []


def _serper_search(query: str) -> list[dict]:
    """Call Serper API — returns organic + places pack results merged."""
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

        # Google "places pack" (local business results) — best for actual place names
        for p in data.get("places", []):
            results.append({
                "title":   p.get("title", ""),
                "snippet": p.get("address", p.get("category", "")),
                "link":    p.get("website", ""),
                "_is_place": True,   # already a specific name, skip article check
            })

        ab = data.get("answerBox", {})
        if ab.get("title") and ab.get("snippet"):
            results.insert(0, {"title": ab["title"], "snippet": ab["snippet"], "link": ""})

        return results[:6]
    except Exception as e:
        print(f"[PlacesAgent] Serper error: {e}")
        return []


def _parse_results(results: list[dict], category: str) -> list[dict]:
    """
    Convert Serper results to named places.
    If a result is a listicle title (TOP 10, BEST…), extract individual
    names from the snippet instead of using the article title.
    """
    places = []
    seen   = set()

    for r in results:
        raw_title = r.get("title", "")
        # Clean common separators from titles
        title = raw_title.split(" - ")[0].split(" | ")[0].split(". ")[0].strip()
        snippet = r.get("snippet", "")
        is_place = r.get("_is_place", False)

        if is_place or not _is_article_title(title):
            # Title is already a real place name
            name = title.split(". ")[0].strip()
            if name and name not in seen and _is_valid_place_name(name):
                seen.add(name)
                places.append({
                    "name":      name,
                    "type":      category,
                    "best_time": "Check locally",
                    "tip":       snippet[:120],
                    "source":    r.get("link", ""),
                })
        else:
            # Article title — pull individual names out of the snippet
            names = _names_from_snippet(snippet)
            for name in names:
                name = name.split(". ")[0].strip()
                if name and name not in seen and _is_valid_place_name(name):
                    seen.add(name)
                    places.append({
                        "name":      name,
                        "type":      category,
                        "best_time": "Check locally",
                        "tip":       snippet[:100],
                        "source":    r.get("link", ""),
                    })

    return places


def _get_places_live(destination: str, interests: list, indoor_only: bool) -> dict:
    """Fetch real places from Serper (Google Search)."""
    print(f"[PlacesAgent] 🌐 Calling Serper API for {destination}...")

    selected = {}
    interest_str = " ".join(interests).lower()

    if not indoor_only:
        if "beach" in interest_str:
            results = _serper_search(f"best beaches to visit in {destination}")
            selected["beaches"] = _parse_results(results, "beach")

        if "sightseeing" in interest_str or not interests:
            results = _serper_search(f"top tourist attractions in {destination}")
            selected["sightseeing"] = _parse_results(results, "sightseeing")

        if "nightlife" in interest_str:
            results = _serper_search(f"best nightlife bars clubs in {destination}")
            selected["nightlife"] = _parse_results(results, "nightlife")
    else:
        results = _serper_search(f"best indoor activities museums things to do in {destination}")
        selected["indoor_activities"] = _parse_results(results, "indoor")

    food_results = _serper_search(f"famous restaurants to eat in {destination} names")
    selected["food_spots"] = _parse_results(food_results, "restaurant")

    # Nearby day-trip destinations (1–3 hr drive)
    dest_key = destination.lower().strip()
    curated  = _NEARBY_DAYTRIPS.get(dest_key, [])
    nearby   = [{"name": n, "type": "day_trip", "best_time": "Early morning start", "tip": f"~1–3 hr drive from {destination}", "source": ""} for n in curated]
    # Also try Serper for cities not in curated list
    if not curated:
        daytrip_results = _serper_search(f"one day trip from {destination} nearby hill station")
        dest_lower = destination.lower()
        serper_trips = [
            p for p in _parse_results(daytrip_results, "day_trip")
            if dest_lower not in p["name"].lower()
        ]
        nearby = serper_trips
    selected["nearby_daytrips"] = nearby

    total = sum(len(v) for v in selected.values())
    return {
        "destination":  destination,
        "indoor_only":  indoor_only,
        "places":       selected,
        "total_places": total,
        "data_source":  "Serper / Google Search (live)",
        "pro_tips": [
            f"Search Google Maps for real-time hours and reviews in {destination}",
            "Book popular spots 1–2 days in advance",
            "Ask locals for hidden gems not listed online",
        ],
    }


# ── Fallback static data ───────────────────────────────────────────────────

def _no_key_result(destination: str) -> dict:
    return {
        "destination":  destination,
        "indoor_only":  False,
        "places":       {},
        "total_places": 0,
        "data_source":  "No API key — configure SERPER_API_KEY in .env",
        "pro_tips":     ["Add SERPER_API_KEY to .env to get live places for any destination."],
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

def places_explorer_agent(state: TripState) -> TripState:
    dest      = state["destination"]
    interests = state.get("places_interest", ["sightseeing", "beach"])
    weather   = state.get("weather_data", {})
    indoor_only = weather.get("rainfall_risk", "low") == "high"

    print(f"\n[PlacesAgent] 📍 Discovering places in {dest} "
          f"{'(indoor focus — rain expected)' if indoor_only else ''}...")

    if SERPER_API_KEY:
        data = _get_places_live(dest, interests, indoor_only)
    else:
        print("[PlacesAgent] ⚠️  No Serper key — cannot fetch live places data")
        data = _no_key_result(dest)

    state["places_data"] = data
    msg = (f"Found {data['total_places']} places via {data['data_source']} "
           f"across {list(data['places'].keys())}")
    state["messages"].append(f"[PlacesAgent] {msg}")
    print(f"[PlacesAgent] ✅ {msg}")
    return state
