# Google-SDk-Course-Weather-Armor
# 🌦️ Google ADK Weather Bot ("Pat")

A conversational Weather Bot built in Python using the **Google Agent Development Kit (ADK)** and Google Gemini models.

The bot prompts users for their location, uses custom Python tools to fetch real-time forecasts and active weather alerts, and responds with a friendly, structured weather summary and recommendations.

---

## 🌟 Key Features

- **Google Agent Development Kit (ADK) Native:** Built using `google.adk.agents.Agent` and driven by ADK's `InMemoryRunner` event loop and session service.
- **National Weather Service (NWS) API Integration:** Fetches multi-period forecasts, high/low temperatures, wind conditions, and detailed outlooks for U.S. locations.
- **Global Fallback Support:** Includes Open-Meteo integration for international locations.
- **Real-Time Weather Alerts:** Automatically retrieves active severe weather watches, warnings, and advisories to keep users informed.
- **Google Model Armor Guardrails:** Inspects incoming user queries for prompt injection, jailbreak attempts, and dangerous content (such as asking how to create a bomb). Inappropriate queries are blocked before model invocation with: `"Sorry, I cannot answer that.  Your question violates our guidlines."`.
- **Conversation Logging:** Full lifecycle callbacks (`before_model_callback`, `after_model_callback`) log every user turn, model output, and security violation to `conversation.log` with timestamps and session context.
- **Multiple Ways to Run:**
  1. **Interactive Terminal Bot:** Custom multi-turn CLI application (`weather_bot.py`).
  2. **ADK Command-Line Interface:** Native ADK runner (`adk run weather_agent`).
  3. **ADK Web UI:** Browser-based chat and agent inspection interface (`adk web weather_agent`).
- **Zero Weather API Keys Required:** NWS and Open-Meteo require no API keys, working immediately out-of-the-box.

---

## 📁 Project Structure

```text
GoogleAgents/
├── weather_agent/               # ADK Agent Package
│   ├── __init__.py              # Package exports
│   ├── agent.py                 # Agent definition ('Pat' with lifecycle callbacks)
│   ├── tools.py                 # Weather & geocoding tools (PEP 8 type hints + docstrings)
│   ├── model_armor.py           # Google Model Armor guardrail template (Prompt Injection / Harmful Content)
│   └── callbacks.py             # ADK callbacks (moderation, conversation logging)
├── weather_bot.py               # Interactive CLI bot with guardrails & logging
├── test_weather_bot.py          # Comprehensive test suite (16 automated unit tests)
├── conversation.log             # Persistent log of user queries, model responses, & security blocks
├── requirements.txt             # Project dependencies
├── .env.example                 # Environment variables template
└── .env                         # Local environment configuration (API keys)
```

---

## 🚀 Quickstart

### 1. Prerequisites & Virtual Environment

Ensure you have Python 3.10+ installed:

```bash
# Verify Python version
py -3.10 --version
```

### 2. Install Dependencies

Install the required packages:

```bash
py -3.10 -m pip install -r requirements.txt
```

*(Or directly `pip install google-adk python-dotenv`)*

### 3. Configure Gemini API Key

Copy `.env.example` to `.env` (if not already created) and add your Gemini API key:

```bash
# In .env:
GEMINI_API_KEY=your_gemini_api_key_here
```

> **Note:** You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
> If no API key is provided, `weather_bot.py` automatically runs in **Direct Tool Mode**, allowing you to test real-time weather retrieval immediately!

---

## 🖥️ Running the Weather Bot

### Option A: Interactive CLI Bot

Run the interactive bot:

```bash
py -3.10 weather_bot.py
```

**Example interaction:**
```text
=================================================================
         Google ADK Weather Bot -- Agent 'Pat'
=================================================================
Powered by Google Agent Development Kit (ADK) & Gemini
Type 'exit' or 'quit' at any time to end the session.
-----------------------------------------------------------------

[Pat]: Hello! I'm Pat, your friendly weather assistant.
[Pat]: What city or location would you like the weather for today?

You: Austin, TX

[Tool Execution: get_current_weather_for_location(location='Austin, TX')]...
[Pat]: The weather in Austin, Texas is currently 95°F with partly sunny skies.
Heat index values reach around 103°F with south winds between 5 to 10 mph.
Tonight will be partly cloudy with a low around 78°F.
No active severe weather alerts are in effect for Austin today.
Be sure to stay hydrated in the heat! Would you like the forecast for another location?
```

### Option B: ADK CLI (`adk run`)

Run the agent directly via the Google ADK command-line runner:

```bash
py -3.10 -m google.adk.cli run weather_agent
```

Or if `adk` is on your PATH:
```bash
adk run weather_agent
```

### Option C: ADK Web Interface (`adk web`)

Launch the visual browser interface provided by ADK:

```bash
py -3.10 -m google.adk.cli web weather_agent
```

Then open `http://localhost:8000` in your browser to chat with Pat and inspect events, state deltas, and tool calls.

---

## 🧪 Running Automated Tests

Run the test suite to verify tool functionality and multi-city forecast retrieval:

```bash
py -3.10 test_weather_bot.py
```

**Tests include:**
- Geocoding coordinates resolution (`Austin, TX`, `Seattle, WA`, `New York, NY`, `Miami, FL`, `Chicago, IL`).
- Graceful error handling for invalid locations.
- Weather forecast retrieval via National Weather Service API.
- Active weather alert checking.
- Multi-city weather retrieval.
- Global fallback for international destinations.
- ADK Agent identity, tools registration, and `InMemoryRunner` compatibility.

---

## 🛠️ How Tools & Agent Work

ADK automatically introspects Python functions with docstrings and type annotations to generate function schemas for the LLM:

1. **`get_lat_lon(location_name: str) -> dict`**:
   Resolves a text location to `(latitude, longitude)`.
2. **`get_weather_forecast(lat: float, lon: float) -> dict`**:
   Fetches forecasts from U.S. National Weather Service (`api.weather.gov/points/...`) with Open-Meteo fallback.
3. **`get_weather_alerts(lat: float, lon: float) -> dict`**:
   Queries `api.weather.gov/alerts/active` for hazards, watches, or warnings.
4. **`get_current_weather_for_location(location: str) -> dict`**:
   High-level composite tool that geocodes, retrieves forecasts, and checks alerts in a single step.
