"""
Flask Web App — Multi-Agent Trip Planner
=========================================
Run locally:  python app.py
Then open:    http://localhost:8000
"""

import os
import sys
import json
import threading
from flask import Flask, render_template, request, jsonify, send_file

sys.path.insert(0, os.path.dirname(__file__))
from workflow   import run_trip_planner
from guardrails import validate_inputs

app = Flask(__name__)

# Store latest run result in memory
_result_store = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/architecture")
def architecture():
    return send_file(os.path.join(os.path.dirname(__file__), "architecture.html"))


@app.route("/presentation")
def presentation():
    return send_file(os.path.join(os.path.dirname(__file__), "PRESENTATION.html"))


@app.route("/plan", methods=["POST"])
def plan():
    data = request.get_json()
    try:
        trip_request = {
            "source":           data.get("source", ""),
            "destination":      data.get("destination", ""),
            "travel_dates":     data.get("travel_dates", ""),
            "num_days":         int(data.get("num_days", 3)),
            "budget":           float(data.get("budget", 20000)),
            "num_travelers":    int(data.get("num_travelers", 1)),
            "travel_type":      data.get("travel_type", "solo"),
            "hotel_pref":       data.get("hotel_pref", "mid-range hotel"),
            "food_pref":        data.get("food_pref", "local cuisine"),
            "transport_pref":   data.get("transport_pref", "flight"),
            "seat_pref":        data.get("seat_pref", "window"),
            "num_rooms":        int(data.get("num_rooms", 1)),
            "places_interest":  data.get("places_interest", ["sightseeing"]),
            "luxury_or_budget": data.get("luxury_or_budget", "mid-range"),
            "must_visit_places": data.get("must_visit_places", ""),
        }

        # ── Input Guardrails ───────────────────────────────────────────────
        guard = validate_inputs(trip_request)
        if not guard["passed"]:
            return jsonify({
                "status":   "guardrail_error",
                "errors":   guard["errors"],
                "warnings": guard["warnings"],
                "message":  "Input validation failed. Please fix the errors and try again.",
            }), 400

        final_state = run_trip_planner(trip_request)
        _result_store["last"] = final_state

        evaluation     = final_state.get("evaluation", {})
        budget_summary = final_state.get("budget_summary", {})
        transport_data = final_state.get("transport_data", {})
        weather_data   = final_state.get("weather_data", {})

        # ── Derived alert flags ────────────────────────────────────────────
        weather_risk = weather_data.get("rainfall_risk", "low")
        temp_max     = weather_data.get("temperature", {}).get("max", 0)
        try:
            temp_max = float(temp_max)
        except (TypeError, ValueError):
            temp_max = 0

        is_rainy  = weather_risk == "high"
        is_hot    = temp_max >= 38
        show_warn = is_rainy or is_hot

        if is_rainy and is_hot:
            warn_msg  = (f"It will be very hot ({temp_max}°C) AND heavy rain is expected. "
                         "Carry sunscreen, umbrella and stay hydrated. Proceed?")
            warn_type = "rain+heat"
        elif is_rainy:
            warn_msg  = ("Heavy rain is expected during your trip. "
                         "Outdoor activities may be disrupted. Do you want to proceed?")
            warn_type = "rain"
        elif is_hot:
            warn_msg  = (f"Very hot weather expected ({temp_max}°C). "
                         "Carry water, avoid midday outdoor activities, wear sunscreen. Proceed?")
            warn_type = "heat"
        else:
            warn_msg  = ""
            warn_type = "none"

        weather_warning = {
            "show":    show_warn,
            "risk":    weather_risk,
            "type":    warn_type,
            "temp_max": temp_max,
            "summary": weather_data.get("summary", ""),
            "message": warn_msg,
        }

        budget_exceeded = {
            "show":    budget_summary.get("budget_exceeded", False),
            "message": budget_summary.get("budget_exceeded_message", ""),
        }

        no_tickets = {
            "show":    transport_data.get("no_tickets_available", False),
            "message": transport_data.get("no_tickets_message", ""),
        }

        return jsonify({
            "status":            "success",
            "review":            final_state.get("review_status"),
            "review_summary":    final_state.get("review_summary", ""),
            "review_highlights": final_state.get("review_highlights", []),
            "pdf_status":        final_state.get("pdf_status"),
            "pdf_path":          final_state.get("pdf_path", ""),
            "budget":            budget_summary,
            "hotel":             final_state.get("hotel_data", {}).get("recommended"),
            "transport":         transport_data.get("recommended"),
            "weather":           weather_data,
            "itinerary_title":   final_state.get("itinerary", {}).get("title"),
            "num_days":          len(final_state.get("itinerary", {}).get("days", [])),
            "messages":          final_state.get("messages", []),
            "errors":            final_state.get("errors", []),
            "warnings":          guard.get("warnings", []),
            "transport_data":    transport_data,
            "hotel_data":        final_state.get("hotel_data", {}),
            "places_data":       final_state.get("places_data", {}),
            "itinerary":         final_state.get("itinerary", {}),
            "weather_warning":   weather_warning,
            "budget_exceeded":   budget_exceeded,
            "no_tickets":        no_tickets,
            "evaluation": {
                "total_score":     evaluation.get("total_score", 0),
                "grade":           evaluation.get("grade", "N/A"),
                "breakdown":       evaluation.get("breakdown", {}),
                "recommendations": evaluation.get("recommendations", []),
            },
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Trippy chatbot — conversational trip planning assistant."""
    data     = request.get_json()
    messages = data.get("messages", [])

    from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL, OPENAI_API_KEY, LLM_MODEL
    import requests as req, re as _re

    system_prompt = """You are Trippy, a friendly AI travel assistant for an Indian trip planner app.
Collect trip details through short, natural conversation. Ask at most 1-2 questions per turn.

COLLECT (in order, skip what the user already told you):
1. Source city + Destination
2. Start date + number of days (min 2 days)
3. Number of travelers + type: solo / couple / family / friends / business
4. Total budget in INR (vague words: low=15000, moderate=30000, high=60000, luxury=100000)
5. Interests from: trekking, beach, mountains, heritage, food, nightlife, nature, sightseeing
6. Any must-visit places (temple, beach, viewpoint, restaurant, etc.)
7. Hotel style: beach resort / city centre hotel / heritage boutique hotel / hill station resort / business hotel
8. Transport: flight / train / bus / car

CRITICAL RULE — GENERATE ##EXTRACT## TAG:
As soon as you know source, destination, dates, num_travelers, AND budget — you MUST output the ##EXTRACT## tag
at the very end of your message. Do NOT keep asking more questions once you have these 5 fields.
Use sensible defaults for anything not mentioned (transport=train, hotel_pref=city centre hotel, food_pref=local cuisine, interests=["sightseeing"]).

FORMAT (compact JSON, no line breaks inside the tag):
##EXTRACT:{"source":"Hyderabad","destination":"Visakhapatnam","travel_dates":"2026-06-15 to 2026-06-19","num_days":4,"num_travelers":2,"travel_type":"couple","budget":40000,"places_interest":["beach","trekking"],"must_visit_places":"Araku Valley, RK Beach","luxury_or_budget":"mid-range","transport_pref":"train","hotel_pref":"beach resort","food_pref":"local cuisine"}##

RULES:
- Keep replies to 2-3 sentences max
- Use travel emojis occasionally
- travel_dates format: YYYY-MM-DD to YYYY-MM-DD (if only month given, pick the 15th as start date)
- places_interest values must be from: beach, trekking, mountains, heritage, food, nightlife, nature, sightseeing
- luxury_or_budget values: budget / mid-range / luxury"""

    llm_msgs = [{"role": "system", "content": system_prompt}]
    for m in messages:
        llm_msgs.append({"role": m["role"], "content": m["content"]})

    reply = ""
    use_openai = OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_KEY"

    try:
        if use_openai:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            llm = ChatOpenAI(model=LLM_MODEL, temperature=0.7, api_key=OPENAI_API_KEY, max_tokens=400)
            lc = [SystemMessage(content=system_prompt)]
            for m in messages:
                lc.append(HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]))
            reply = llm.invoke(lc).content
        elif OPENROUTER_API_KEY:
            r = req.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                json={"model": OPENROUTER_MODEL, "messages": llm_msgs, "max_tokens": 400},
                timeout=20, verify=False,
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"]
        else:
            reply = "Hi! I'm Trippy. No AI key is configured right now — please fill the form directly. 😊"
    except Exception as e:
        reply = f"Sorry, I hit a snag ({e}). Please fill the form directly."

    extracted = {}
    match = _re.search(r'##EXTRACT:(.*?)##', reply, _re.DOTALL)
    if match:
        try:
            extracted = json.loads(match.group(1).strip())
            reply = reply.replace(match.group(0), "").strip()
            reply += "\n\nI've gathered everything! Click **Fill the Form** below to auto-populate your trip details. ✈️"
        except Exception:
            pass

    return jsonify({"reply": reply, "extracted": extracted})


@app.route("/places_for_city", methods=["POST"])
def places_for_city():
    """Fetch places for a stopover/hub city on demand."""
    data      = request.get_json()
    city      = data.get("city", "").strip()
    interests = data.get("interests", ["sightseeing"])
    if not city:
        return jsonify({"status": "error", "message": "City is required"}), 400
    try:
        from agents.places_agent import _get_places_live, _no_key_result
        from config import SERPER_API_KEY
        if SERPER_API_KEY:
            places = _get_places_live(city, interests, indoor_only=False)
        else:
            places = _no_key_result(city)
        return jsonify({"status": "success", "city": city, "places_data": places})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/download")
def download():
    state    = _result_store.get("last", {})
    pdf_path = state.get("pdf_path", "")
    if pdf_path and os.path.exists(pdf_path):
        return send_file(
            os.path.abspath(pdf_path),
            as_attachment=True,
            download_name=os.path.basename(pdf_path),
            mimetype="application/pdf"
        )
    return jsonify({"error": "No PDF available. Run a trip plan first."}), 404


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    os.makedirs("memory", exist_ok=True)
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  AI Trip Planner is running!")
    print(f"   Open: http://localhost:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)
