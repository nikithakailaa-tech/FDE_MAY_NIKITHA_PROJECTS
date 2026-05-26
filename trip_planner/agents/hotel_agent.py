"""
Hotel Agent
===========
Finds hotels matching the user's preferences and budget via Serper API (Google Search).
No mock data — returns empty options with an error message if API key is missing.
"""

import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from state import TripState
from config import SERPER_API_KEY

SERPER_URL = "https://google.serper.dev/search"

_ARTICLE_SIGNALS = [
    "best ", "top ", "hotels in", "places to stay", "2025", "2026", "2024",
    "tripadvisor", "booking.com", "expedia", "makemytrip", "goibibo",
    "list of", "ranked", "review", "compare", "cheapest", "most popular",
    "things to know", "guide to", "worth staying",
]


def _is_article_title(title: str) -> bool:
    t = title.lower()
    return any(sig in t for sig in _ARTICLE_SIGNALS)


def _names_from_snippet(snippet: str, max_items: int = 4) -> list:
    """Extract individual hotel names from a listicle snippet."""
    numbered = re.findall(
        r'\d+\.\s+([A-Z][^·\n\d(]{2,50}?)(?:\s*[·•]\s*|\s*\n|$)',
        snippet
    )
    if len(numbered) >= 2:
        return [n.strip().rstrip('.,') for n in numbered[:max_items]]

    if '·' in snippet:
        parts = [p.strip() for p in snippet.split('·')]
        valid = [
            p.rstrip('.,') for p in parts
            if 3 < len(p.strip()) < 60
            and not p.strip()[0].isdigit()
            and not any(s in p.lower() for s in ['see more', 'read more', 'view all', 'rated', 'reviews', 'from $', 'from ₹'])
        ]
        if len(valid) >= 2:
            return valid[:max_items]

    rated = re.findall(r'([A-Z][A-Za-z\s\'&]{3,45}?)\s*\([\d.]+', snippet)
    if len(rated) >= 2:
        return [n.strip() for n in rated[:max_items]]

    return []


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
        # Google places pack — actual hotel names from Maps
        for p in data.get("places", []):
            results.append({
                "title":    p.get("title", ""),
                "snippet":  p.get("address", p.get("category", "")),
                "link":     p.get("website", ""),
                "_is_place": True,
            })
        return results[:8]
    except Exception as e:
        print(f"[HotelAgent] Serper error: {e}")
        return []


def _clean_hotel_name(title: str) -> str:
    """Extract real hotel name from rating-prefixed titles like '(1414 Ratings). BAY VIEW HOTEL ; 4.1'."""
    # Pattern: "(N Ratings). HOTEL NAME ; score"
    m = re.search(r'\([\d,]+\s+Ratings?\)\.\s*([A-Z][A-Za-z0-9\s\'&\-]+?)(?:\s*;\s*[\d.]+\s*)?$', title, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Remove trailing score like "Hotel Name ; 4.2"
    cleaned = re.sub(r'\s*;\s*[\d.]+\s*$', '', title).strip()
    return cleaned.split(" - ")[0].split(" | ")[0].strip()


def _parse_hotels(results: list[dict], num_days: int) -> list[dict]:
    hotels = []
    seen   = set()

    for r in results:
        raw_title = r.get("title", "")
        title    = _clean_hotel_name(raw_title)
        snippet  = r.get("snippet", "")
        is_place = r.get("_is_place", False)

        if is_place or not _is_article_title(title):
            name = title
            if name and name not in seen and len(name) > 3:
                seen.add(name)
                hotels.append({
                    "name":       name,
                    "details":    snippet[:150],
                    "source_url": r.get("link", ""),
                    "stay_nights": num_days,
                })
        else:
            for name in _names_from_snippet(snippet):
                if name and name not in seen and len(name) > 3:
                    seen.add(name)
                    hotels.append({
                        "name":       name,
                        "details":    snippet[:100],
                        "source_url": r.get("link", ""),
                        "stay_nights": num_days,
                    })

        if len(hotels) >= 4:
            break

    return hotels


def _get_hotels_live(destination: str, tier: str, num_days: int, budget: float) -> dict:
    print(f"[HotelAgent] 🌐 Calling Serper API for {tier} hotels in {destination}...")

    tier_map = {
        "luxury":    f"luxury 5 star hotels {destination} names",
        "mid-range": f"4 star hotels {destination} names",
        "budget":    f"budget hotels {destination} affordable",
    }
    query = tier_map.get(tier, f"hotels in {destination}")
    results = _serper_search(query)
    options = _parse_hotels(results, num_days)

    hotel_budget = budget * 0.40
    return {
        "tier":         tier,
        "options":      options,
        "recommended":  options[0]["name"] if options else "See search results",
        "hotel_budget": hotel_budget,
        "data_source":  "Serper / Google Search (live)",
        "notes":        f"Showing live Google results for {tier} hotels in {destination}",
    }


# ── Fallback mock data ─────────────────────────────────────────────────────

def _no_key_result(tier: str, budget: float) -> dict:
    hotel_budget = budget * 0.40
    return {
        "tier":         tier,
        "options":      [],
        "recommended":  "Configure SERPER_API_KEY for live results",
        "hotel_budget": hotel_budget,
        "data_source":  "No API key — configure SERPER_API_KEY in .env",
        "notes":        "Add SERPER_API_KEY to .env to get live hotel options for any destination.",
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

def _rooms_label(state) -> str:
    """Human-readable room requirement label for search queries."""
    travel_type   = (state.get("travel_type") or "solo").lower()
    num_travelers = state.get("num_travelers", 1)
    num_rooms     = state.get("num_rooms", 0)

    if num_rooms and int(num_rooms) > 0:
        rooms = int(num_rooms)
    elif travel_type == "couple":
        rooms = 1
    elif travel_type == "solo":
        rooms = 1
    elif travel_type == "business":
        rooms = num_travelers
    else:
        import math
        rooms = max(1, math.ceil(num_travelers / 2))

    if rooms == 1:
        room_str = "1 double room"
    else:
        room_str = f"{rooms} rooms"

    return room_str, rooms


def hotel_agent(state: TripState) -> TripState:
    dest   = state["destination"]
    tier   = state.get("luxury_or_budget", "mid-range")
    days   = state.get("num_days", 3)
    budget = state.get("budget", 30000)

    room_str, rooms = _rooms_label(state)
    print(f"\n[HotelAgent] 🏨  Finding {tier} hotels in {dest} ({room_str}, {days} nights)...")

    if SERPER_API_KEY:
        data = _get_hotels_live(dest, tier, days, budget)
    else:
        print("[HotelAgent] ⚠️  No Serper key — cannot fetch live hotel data")
        data = _no_key_result(tier, budget)

    data["rooms_needed"] = rooms
    data["rooms_label"]  = room_str
    state["hotel_data"] = data
    num_opts = len(data.get("options", []))
    msg = f"Hotels: {num_opts} options found ({room_str}, {days} nights). Recommended: {data['recommended']}"
    state["messages"].append(f"[HotelAgent] {msg}")
    print(f"[HotelAgent] ✅ {msg}")
    return state
