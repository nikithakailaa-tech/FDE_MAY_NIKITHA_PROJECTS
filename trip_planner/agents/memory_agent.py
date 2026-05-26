"""
Memory Agent
============
Handles persistent user memory across sessions.

WHAT IT DOES:
  • Loads past user preferences from a JSON file (simulates Vector DB / Redis)
  • Injects them into state so other agents can personalise their responses
  • After a trip is approved, updates the store with the new trip

In production you would replace the JSON file with:
  - FAISS / ChromaDB  → semantic preference retrieval
  - Redis             → fast session memory
  - PostgreSQL        → structured trip history
"""

import json
import os
from state import TripState
from config import MEMORY_FILE


def _load_store() -> dict:
    """Load the JSON memory store from disk."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_store(store: dict) -> None:
    """Persist updated memory back to disk."""
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(store, f, indent=2)


# ── Node: retrieve memory ──────────────────────────────────────────────────

def memory_retrieval_agent(state: TripState) -> TripState:
    """
    LangGraph Node — Memory Retrieval
    ----------------------------------
    Reads saved preferences and past trips for this user.
    Enriches the state before other agents run.
    """
    print("\n[MemoryAgent] 🧠 Retrieving user preferences from memory store...")

    store = _load_store()
    user_key = f"{state['travel_type']}_{state['source']}"   # simple key scheme

    profile   = store.get("user_profile",  {})
    past_trips = store.get("past_trips",   [])

    # If we have a stored food/hotel preference, respect it unless overridden
    if profile.get("food_pref") and not state.get("food_pref"):
        state["food_pref"] = profile["food_pref"]

    state["user_profile"] = profile
    state["past_trips"]   = past_trips

    msg = (f"Memory loaded — profile keys: {list(profile.keys())}, "
           f"past trips: {len(past_trips)}")
    state["messages"].append(f"[MemoryAgent] {msg}")
    print(f"[MemoryAgent] ✅ {msg}")
    return state


# ── Node: update memory ────────────────────────────────────────────────────

def memory_update_agent(state: TripState) -> TripState:
    """
    LangGraph Node — Memory Update
    --------------------------------
    Called ONLY after the Orchestrator approves the final itinerary.
    Saves preferences so future trips are personalised.
    """
    print("\n[MemoryAgent] 💾 Saving updated preferences to memory store...")

    store = _load_store()

    # Update profile with latest preferences
    store["user_profile"] = {
        "food_pref":        state.get("food_pref", ""),
        "hotel_pref":       state.get("hotel_pref", ""),
        "transport_pref":   state.get("transport_pref", ""),
        "luxury_or_budget": state.get("luxury_or_budget", ""),
        "travel_type":      state.get("travel_type", ""),
    }

    # Append this trip to history (keep last 10)
    new_trip = {
        "destination":  state.get("destination"),
        "dates":        state.get("travel_dates"),
        "budget":       state.get("budget"),
        "num_days":     state.get("num_days"),
    }
    past = store.get("past_trips", [])
    past.append(new_trip)
    store["past_trips"] = past[-10:]   # keep rolling window of 10

    _save_store(store)

    state["messages"].append("[MemoryAgent] Memory updated with latest trip.")
    print("[MemoryAgent] ✅ Memory saved.")
    return state
