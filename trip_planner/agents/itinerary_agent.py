"""
Itinerary Agent
===============
Generates a detailed day-wise trip plan using the LLM.

This is the CREATIVE agent — it takes all structured data from other agents
and synthesises it into a narrative, time-blocked daily itinerary.

LLM is used here because:
  • Requires natural language generation
  • Must weave together weather, places, food, timing constraints
  • Should adapt tone (romantic / adventure / family) based on travel_type
"""

import os
import json
import math
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from state import TripState
from config import OPENAI_API_KEY, LLM_MODEL, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


def _build_itinerary_prompt(state: TripState) -> str:
    """Construct a rich, structured prompt for the LLM."""
    dest             = state['destination']
    src              = state['source']
    weather          = state.get("weather_data", {})
    places           = state.get("places_data", {}).get("places", {})
    food             = state.get("places_data", {}).get("places", {}).get("food_spots", [])
    transport        = state.get("transport_data", {})
    hotel            = state.get("hotel_data", {})
    budget_s         = state.get("budget_summary", {})
    num_days         = state.get("num_days", 3)
    must_visit       = state.get("must_visit_places", "").strip()

    # Flatten places by category
    all_attractions = []
    nearby_daytrips = []
    for category, items in places.items():
        if category == "food_spots":
            continue
        elif category == "nearby_daytrips":
            nearby_daytrips.extend([p.get("name", "") for p in items])
        else:
            all_attractions.extend([p.get("name", "") for p in items])

    food_spots = [f.get("name", "") for f in food]
    hotel_name = hotel.get("recommended", f"a hotel in {dest}")
    transport_rec = transport.get("recommended", f"transport to {dest}")

    attractions_line = (
        f"Use these real places IN {dest}: {', '.join(all_attractions)}"
        if all_attractions
        else f"Use your knowledge of REAL tourist places in {dest} — beaches, monuments, parks, museums."
    )

    # Calculate how many day trips to schedule based on trip length
    # Rule: roughly every other mid-day is a day trip (ceil of half the mid-days)
    num_daytrip_slots = 0
    if nearby_daytrips and num_days >= 3:
        num_daytrip_slots = min(len(nearby_daytrips), max(1, math.ceil((num_days - 2) / 2)))
    daytrip_destinations = nearby_daytrips[:num_daytrip_slots]

    # Assign specific mid-trip days (skip day 1 and last day)
    # e.g. 3-day → day 2; 5-day → days 2 & 4; 7-day → days 2, 4 & 6
    daytrip_day_numbers = [2 + i * 2 for i in range(num_daytrip_slots) if 2 + i * 2 < num_days]
    daytrip_assignments = list(zip(daytrip_day_numbers, daytrip_destinations))

    if daytrip_assignments:
        assignments_text = "; ".join(
            f"Day {day}: full-day excursion to {place} (1–3 hr drive each way)"
            for day, place in daytrip_assignments
        )
        daytrip_line = (
            f"NEARBY DAY TRIPS — you MUST schedule these excursions on the specified days: {assignments_text}. "
            f"For each day-trip day: depart early (6 AM), explore destination for 3–4 hours, have lunch there, return by evening."
        )
    else:
        daytrip_line = ""

    must_visit_line = (
        f"MUST-VISIT PLACES (user specifically requested these — include ALL of them in the itinerary): {must_visit}"
        if must_visit else ""
    )
    food_line = (
        f"Use these food spots: {', '.join(food_spots)}"
        if food_spots
        else f"Suggest REAL local restaurants and food specialities of {dest}."
    )

    prompt = f"""
You are an expert travel planner creating a trip to {dest}, India.

=== DESTINATION: {dest} ===
THIS TRIP IS TO {dest.upper()}. ALL places, locations, activities and restaurants MUST be IN {dest}.
DO NOT mention any places from Goa, Baga, Anjuna, Calangute, Dabolim, Mumbai, Kerala, Rajasthan or any city OTHER than {dest}.
Every "location" field in the JSON must be a real place IN {dest}.

TRIP DETAILS:
- Route: {src} → {dest}
- Dates: {state['travel_dates']} ({num_days} days)
- Travelers: {state['num_travelers']} ({state['travel_type']})
- Budget: ₹{state['budget']:,}
- Preferences: {', '.join(state.get('places_interest', []))}

AVAILABLE DATA:
- Weather at {dest}: {weather.get('summary', 'Pleasant')} | Temp: {weather.get('temperature', {}).get('min', 26)}–{weather.get('temperature', {}).get('max', 34)}°C
- Staying at: {hotel_name} (in {dest})
- Transport: {transport_rec}
- {attractions_line}
- {food_line}
- {daytrip_line if daytrip_line else "No nearby day-trip data available."}
- {must_visit_line if must_visit_line else "No specific must-visit requests."}
- Budget for activities/food: ₹{budget_s.get('breakdown', {}).get('food', 3000) + budget_s.get('breakdown', {}).get('activities', 2000):,.0f}

INSTRUCTIONS:
1. Create a time-blocked itinerary for each of {num_days} days
2. Day 1 morning: depart {src}, travel to {dest}, arrive and check-in at hotel
3. Last day: checkout, brief sightseeing, travel back to {src}
4. {f"MANDATORY day trips: {'; '.join(f'Day {d} → {p}' for d,p in daytrip_assignments)}" if daytrip_assignments else "No day trips required — stay in " + dest + " for all mid-days"}
5. For each MANDATORY day-trip day: start at 06:00 AM, drive to destination, explore 3–4 hrs, lunch there, drive back by 4 PM, dinner in {dest}
6. Non-day-trip mid-days: cover local attractions in {dest}
7. {f"MUST-VISIT: Spread {must_visit} across the itinerary. Every place listed MUST appear as an activity." if must_visit else "No specific must-visit constraints."}
8. Morning: sightseeing, Afternoon: leisure/local, Evening: dining/entertainment
9. Tone should match travel type: {state['travel_type']} trip

Return ONLY a valid JSON object (no markdown, no extra text):
{{
  "title": "{num_days}-Day {dest} Trip",
  "summary": "...",
  "days": [
    {{
      "day": 1,
      "theme": "Arrival & First Impressions",
      "activities": [
        {{
          "time": "09:00 AM",
          "activity": "Depart {src} — travel to {dest}",
          "location": "{src}",
          "cost": "As booked",
          "tip": "..."
        }},
        {{
          "time": "02:00 PM",
          "activity": "Check in at hotel and freshen up",
          "location": "{dest} hotel area",
          "cost": "₹300",
          "tip": "Keep luggage light for easy check-in"
        }}
      ],
      "meals": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
      "daily_budget": "₹..."
    }}
  ],
  "packing_checklist": ["...", "..."],
  "emergency_contacts": {{"police": "100", "ambulance": "108", "tourist_helpline": "1800-111-363"}}
}}
"""
    return prompt


def _build_itinerary_from_state(state: TripState) -> dict:
    """
    Builds a destination-aware itinerary using only live data already in state.
    No hardcoded city names, places, or prices — everything comes from the agents.
    """
    dest         = state.get("destination", "")
    src          = state.get("source", "")
    num_days     = state.get("num_days", 3)
    dates        = state.get("travel_dates", "")
    transport    = state.get("transport_data", {})
    hotel        = state.get("hotel_data", {})
    places       = state.get("places_data", {}).get("places", {})
    budget       = state.get("budget", 0)
    daily_bud    = round(budget / max(num_days, 1))
    must_visit   = [p.strip() for p in state.get("must_visit_places", "").split(",") if p.strip()]

    hotel_name = hotel.get("recommended", f"hotel in {dest}")
    transport_rec = transport.get("recommended", f"{transport.get('mode','transport')} to {dest}")

    # Flatten all attractions, food, and nearby day trips from live places data
    attractions  = []
    food_spots   = []
    nearby_trips = []
    for cat, items in places.items():
        for p in (items or []):
            name = p.get("name") or p.get("title") or ""
            if not name:
                continue
            if cat == "food_spots":
                food_spots.append(name)
            elif cat == "nearby_daytrips":
                nearby_trips.append(name)
            else:
                attractions.append((name, cat))

    # Pre-compute which mid-days are day trips and to which nearby destination
    # Rule: roughly every other mid-day is a day trip (ceil of half the mid-days)
    num_daytrip_slots = 0
    if nearby_trips and num_days >= 3:
        num_daytrip_slots = min(len(nearby_trips), max(1, math.ceil((num_days - 2) / 2)))
    # day-trip day indices (0-based): 1, 3, 5, ...
    daytrip_index_map = {}  # {day_index: nearby_destination}
    for slot in range(num_daytrip_slots):
        day_idx = 1 + slot * 2
        if day_idx < num_days - 1:  # never assign last day
            daytrip_index_map[day_idx] = nearby_trips[slot]

    days = []
    day_themes = [
        "Arrival & Settling In",
        "Day Trip Excursion",
        "Culture & Sightseeing",
        "Day Trip Excursion",
        "Leisure & Local Flavours",
        "Explore & Discover",
        "Final Day & Departure",
    ]

    # Prepend must-visit places to attractions so they get scheduled first
    if must_visit:
        mv_attractions = [(p, "requested") for p in must_visit]
        attractions    = mv_attractions + [a for a in attractions if a[0] not in must_visit]
    local_attraction_idx = 0

    for i in range(num_days):
        is_first = (i == 0)
        is_last  = (i == num_days - 1)

        if is_first:
            theme = "Arrival & Settling In"
        elif is_last:
            theme = "Final Day & Departure"
        elif i in daytrip_index_map:
            theme = f"Day Trip — {daytrip_index_map[i]}"
        else:
            theme = day_themes[i % len(day_themes)]

        acts = []

        if is_first:
            acts.append({"time": "09:00 AM", "activity": f"Depart {src} — {transport_rec}", "location": src, "duration": "Travel day", "cost": "As booked", "tip": "Carry snacks and ID proof"})
            acts.append({"time": "01:00 PM", "activity": f"Arrive in {dest}", "location": dest, "duration": "—", "cost": "—", "tip": "Note local emergency numbers on arrival"})
            acts.append({"time": "02:00 PM", "activity": f"Check-in at {hotel_name}", "location": dest, "duration": "1h", "cost": "As booked", "tip": "Request early check-in if arriving before noon"})
            if attractions:
                name, cat = attractions[0]
                acts.append({"time": "04:00 PM", "activity": f"First look — visit {name}", "location": name, "duration": "2h", "cost": "—", "tip": f"Great {cat} spot to start your trip"})
            food = food_spots[0] if food_spots else f"local restaurant in {dest}"
            acts.append({"time": "07:30 PM", "activity": f"Welcome dinner at {food}", "location": dest, "duration": "1.5h", "cost": "—", "tip": "Try the local speciality dish"})

        elif is_last:
            acts.append({"time": "07:00 AM", "activity": "Morning walk & last views", "location": dest, "duration": "1h", "cost": "Free", "tip": "Capture memories before checkout"})
            acts.append({"time": "09:00 AM", "activity": f"Checkout from {hotel_name}", "location": dest, "duration": "1h", "cost": "Included", "tip": "Store luggage at reception if needed"})
            acts.append({"time": "11:00 AM", "activity": f"Last-minute shopping in {dest}", "location": dest, "duration": "1.5h", "cost": "—", "tip": "Buy local souvenirs and snacks for the journey"})
            food = food_spots[-1] if food_spots else f"local restaurant in {dest}"
            acts.append({"time": "01:00 PM", "activity": f"Farewell lunch at {food}", "location": dest, "duration": "1h", "cost": "—", "tip": "Try dishes you may have missed"})
            acts.append({"time": "03:00 PM", "activity": f"Depart {dest} — return to {src}", "location": dest, "duration": "Travel", "cost": "As booked", "tip": "Reach departure point 2h early"})

        elif i in daytrip_index_map:
            # Full day trip to a nearby destination
            trip_dest = daytrip_index_map[i]
            food = food_spots[i % len(food_spots)] if food_spots else f"local dhaba near {trip_dest}"
            acts.append({"time": "06:00 AM", "activity": f"Early start — drive to {trip_dest}", "location": trip_dest, "duration": "1–3h drive", "cost": "Fuel / cab fare", "tip": "Start early to beat crowds and the afternoon heat"})
            acts.append({"time": "09:30 AM", "activity": f"Arrive & explore {trip_dest}", "location": trip_dest, "duration": "3h", "cost": "Entry fee if applicable", "tip": "Carry water, snacks, and a light jacket"})
            acts.append({"time": "01:00 PM", "activity": f"Lunch at a local spot near {trip_dest}", "location": trip_dest, "duration": "1h", "cost": "₹200–500/person", "tip": "Try regional specialities unique to this area"})
            acts.append({"time": "02:30 PM", "activity": f"Continue exploring {trip_dest} — viewpoints / nature trails", "location": trip_dest, "duration": "2h", "cost": "Free", "tip": "Check for sunset viewpoints or hidden trails"})
            acts.append({"time": "04:30 PM", "activity": f"Return drive to {dest}", "location": dest, "duration": "1–3h drive", "cost": "—", "tip": "Head back before dark; roads may be narrow"})
            acts.append({"time": "08:00 PM", "activity": f"Dinner and rest at {dest}", "location": dest, "duration": "1.5h", "cost": "—", "tip": "Relax after a full day of travel"})

        else:
            # Local sightseeing day — must-visit places are at the front of attractions list
            food = food_spots[i % len(food_spots)] if food_spots else f"local restaurant in {dest}"
            a1   = attractions[local_attraction_idx % len(attractions)] if attractions else (f"Explore {dest}", "sightseeing")
            a2   = attractions[(local_attraction_idx + 1) % len(attractions)] if len(attractions) > 1 else a1
            local_attraction_idx += 2
            acts.append({"time": "07:30 AM", "activity": f"Morning visit — {a1[0]}", "location": a1[0], "duration": "2h", "cost": "—", "tip": f"Best time for {a1[1]}"})
            acts.append({"time": "10:00 AM", "activity": f"Visit {a2[0]}", "location": a2[0], "duration": "2h", "cost": "—", "tip": "Check local entry timings"})
            acts.append({"time": "01:00 PM", "activity": f"Lunch at {food}", "location": dest, "duration": "1h", "cost": "—", "tip": "Ask for the chef's recommendation"})
            acts.append({"time": "03:30 PM", "activity": f"Afternoon leisure in {dest}", "location": dest, "duration": "2h", "cost": "Free", "tip": "Explore at your own pace"})
            acts.append({"time": "07:00 PM", "activity": f"Dinner and evening in {dest}", "location": dest, "duration": "2h", "cost": "—", "tip": "Explore local nightlife or relax at hotel"})

        lunch_place = food_spots[i % len(food_spots)] if food_spots else f"local restaurant in {dest}"
        days.append({
            "day":          i + 1,
            "theme":        theme,
            "activities":   acts,
            "meals": {
                "breakfast": f"At {hotel_name}" if not is_first else "During travel",
                "lunch":     lunch_place,
                "dinner":    food_spots[(i + 1) % len(food_spots)] if food_spots else f"local restaurant in {dest}",
            },
            "daily_budget": f"~Rs.{daily_bud:,}",
        })

    return {
        "title":   f"{num_days}-Day {dest} Trip — {dates}",
        "summary": f"Your personalised trip from {src} to {dest} built from live search data.",
        "days":    days,
        "packing_checklist": [
            "Valid ID proof (Aadhaar / Passport)",
            "Travel insurance documents",
            "Phone charger & power bank",
            "Reusable water bottle",
            "Comfortable walking shoes",
            "Weather-appropriate clothing",
            "Sunscreen & basic medicines",
            "Cash for local markets",
        ],
        "emergency_contacts": {
            "Police":          "100",
            "Ambulance":       "108",
            "Tourist Helpline":"1800-111-363",
            "Fire":            "101",
        },
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

def itinerary_agent(state: TripState) -> TripState:
    """
    LangGraph Node — Itinerary Agent
    -----------------------------------
    Generates day-wise itinerary. Uses LLM if API key available,
    otherwise uses rule-based itinerary built from live agent data.
    """
    dest     = state["destination"]
    num_days = state.get("num_days", 3)
    print(f"\n[ItineraryAgent] 📅 Building {num_days}-day itinerary for {dest}...")

    use_openai     = (OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_KEY")
    use_openrouter = bool(OPENROUTER_API_KEY)
    use_llm        = use_openai or use_openrouter

    if use_llm:
        try:
            if use_openai:
                print(f"[ItineraryAgent] 🤖 Using OpenAI ({LLM_MODEL})")
                llm = ChatOpenAI(model=LLM_MODEL, temperature=0.7, api_key=OPENAI_API_KEY)
            else:
                print(f"[ItineraryAgent] 🤖 Using OpenRouter ({OPENROUTER_MODEL})")
                llm = ChatOpenAI(
                    model=OPENROUTER_MODEL,
                    temperature=0.7,
                    api_key=OPENROUTER_API_KEY,
                    base_url=OPENROUTER_BASE_URL,
                )
            prompt = _build_itinerary_prompt(state)
            resp   = llm.invoke([
                SystemMessage(content="You are a professional travel planner. Always respond with valid JSON only."),
                HumanMessage(content=prompt),
            ])
            raw = resp.content.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            itinerary = json.loads(raw)

            # Validate LLM didn't hallucinate wrong-city content
            dest_lower = dest.lower()
            raw_lower  = raw.lower()
            wrong_city_keywords = [
                "baga", "anjuna", "calangute", "dabolim", "fort aguada",
                "candolim", "palolem", "vasco", "panaji", "margao",
            ]
            if dest_lower not in ["goa", "north goa", "south goa"]:
                if any(kw in raw_lower for kw in wrong_city_keywords):
                    print(f"[ItineraryAgent] ⚠  LLM hallucinated Goa content for {dest} — using fallback")
                    itinerary = _build_itinerary_from_state(state)
                else:
                    print(f"[ItineraryAgent] ✅ LLM itinerary generated successfully")
            else:
                print(f"[ItineraryAgent] ✅ LLM itinerary generated successfully")
        except Exception as e:
            print(f"[ItineraryAgent] ⚠  LLM failed ({e}) — using built-in itinerary")
            itinerary = _build_itinerary_from_state(state)
    else:
        print("[ItineraryAgent] ℹ  No OpenAI key — using built-in detailed itinerary")
        itinerary = _build_itinerary_from_state(state)

    state["itinerary"] = itinerary
    msg = f"Itinerary: {itinerary['title']} ({len(itinerary.get('days', []))} days)"
    state["messages"].append(f"[ItineraryAgent] {msg}")
    print(f"[ItineraryAgent] ✅ {msg}")
    return state
