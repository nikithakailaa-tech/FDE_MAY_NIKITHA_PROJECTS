"""
Weather Agent
=============
Fetches real weather forecast for the destination from OpenWeatherMap API.
No mock data — if API is unavailable, returns empty data with an error message.
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from state import TripState
from config import OPENWEATHER_API_KEY


def _no_key_result(destination: str, dates: str) -> dict:
    return {
        "destination":   destination,
        "dates":         dates,
        "summary":       "Weather data unavailable — configure OPENWEATHER_API_KEY",
        "temperature":   {"min": "N/A", "max": "N/A", "unit": "°C"},
        "humidity":      "N/A",
        "rainfall_risk": "low",
        "uv_index":      "N/A",
        "warnings":      ["No weather API key — add OPENWEATHER_API_KEY to .env"],
        "packing_tips":  ["Check weather.com for live conditions before travelling"],
        "data_source":   "No API key",
    }


def _fetch_live_weather(destination: str) -> dict:
    """Hit OpenWeatherMap forecast API for real daily min/max range."""
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={destination}&appid={OPENWEATHER_API_KEY}&units=metric&cnt=8"
    )
    resp = requests.get(url, timeout=10, verify=False)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("list", [])
    if not items:
        raise ValueError("Empty forecast response")

    temp_min = round(min(item["main"]["temp_min"] for item in items), 1)
    temp_max = round(max(item["main"]["temp_max"] for item in items), 1)
    humidity = items[0]["main"]["humidity"]
    description = items[0]["weather"][0]["description"].title()

    rain_codes = {item["weather"][0]["id"] for item in items}
    if any(200 <= c < 600 for c in rain_codes):
        rainfall_risk = "high"
    elif any(600 <= c < 700 or c == 741 for c in rain_codes):
        rainfall_risk = "moderate"
    else:
        rainfall_risk = "low"

    return {
        "destination":   destination,
        "summary":       description,
        "temperature":   {"min": temp_min, "max": temp_max, "unit": "°C"},
        "humidity":      f"{humidity}%",
        "rainfall_risk": rainfall_risk,
        "uv_index":      "N/A",
        "warnings":      [],
        "packing_tips":  [
            "Light cotton clothes",
            "Sunscreen SPF 50+",
            "Compact umbrella" if rainfall_risk != "low" else "Sunglasses",
            "Stay hydrated",
        ],
        "data_source":   "OpenWeatherMap (live)",
    }


# ── LangGraph Node ─────────────────────────────────────────────────────────

def weather_agent(state: TripState) -> TripState:
    destination = state["destination"]
    dates       = state["travel_dates"]
    print(f"\n[WeatherAgent] Fetching live weather for {destination} on {dates}...")

    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "YOUR_WEATHER_KEY":
        print("[WeatherAgent] No API key — skipping weather fetch")
        state["weather_data"] = _no_key_result(destination, dates)
        state["messages"].append("[WeatherAgent] Skipped — no OPENWEATHER_API_KEY configured")
        return state

    try:
        weather = _fetch_live_weather(destination)
        weather["dates"] = dates
        state["weather_data"] = weather
        msg = (f"Weather: {weather['summary']}, "
               f"Temp {weather['temperature']['min']}–{weather['temperature']['max']}"
               f"{weather['temperature']['unit']}, "
               f"Rainfall risk: {weather['rainfall_risk']}")
        state["messages"].append(f"[WeatherAgent] {msg}")
        print(f"[WeatherAgent] {msg}")

    except Exception as e:
        err = f"WeatherAgent error: {e}"
        state["errors"].append(err)
        state["weather_data"] = _no_key_result(destination, dates)
        state["weather_data"]["warnings"] = [f"Live weather fetch failed: {e}"]
        print(f"[WeatherAgent] {err} — no fallback data used")

    return state
