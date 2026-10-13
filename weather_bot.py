"""Interactive Weather Bot using Google ADK (Agent Development Kit).

This script prompts the user for their location, communicates with the ADK
Weather Agent ("Pat"), retrieves real-time weather and alerts, and prints
the formatted weather report.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Ensure utf-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google.adk.runners import InMemoryRunner
from google.genai import types
from weather_agent.agent import root_agent
from weather_agent.tools import get_current_weather_for_location
from weather_agent.model_armor import screen_prompt, BLOCKED_RESPONSE_TEXT
from weather_agent.callbacks import ConversationLogger

# Load .env file
load_dotenv()


def print_banner():
    """Displays the welcome banner."""
    print("=" * 65)
    print("         Google ADK Weather Bot -- Agent 'Pat'")
    print("=" * 65)
    print("Powered by Google Agent Development Kit (ADK) & Gemini")
    print("Protected by Google Model Armor Guardrails")
    print("Conversation logging enabled to 'conversation.log'")
    print("Type 'exit' or 'quit' at any time to end the session.")
    print("-" * 65)


def run_direct_demo_mode():
    """Runs a direct interactive demo using the weather tools when no API key is set."""
    print("\n[Notice] No GEMINI_API_KEY detected.")
    print("Starting in Direct Tool Interactive Mode with Model Armor guardrails")
    print("and conversation logging enabled. (To enable full Gemini reasoning,")
    print("add GEMINI_API_KEY to your .env file).\n")

    session_id = "direct_demo_session"

    while True:
        try:
            user_input = input("\nEnter your location (e.g., 'Austin, TX', 'Seattle', 'London'): ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nThank you for using Weather Bot! Goodbye.\n")
                break

            # 1. Screen user prompt with Model Armor template
            verdict = screen_prompt(user_input)
            if verdict.is_blocked:
                ConversationLogger.log_blocked(
                    agent_name="Pat",
                    session_id=session_id,
                    user_prompt=user_input,
                    category=verdict.violation_category or "Policy Violation",
                    reason=verdict.reason or "Prohibited content",
                    blocked_response=verdict.blocked_message,
                )
                print(f"\n[Pat]: {verdict.blocked_message}")
                continue

            # 2. Log approved user prompt
            ConversationLogger.log_user(
                agent_name="Pat",
                session_id=session_id,
                message=user_input,
            )

            print(f"\n[Fetching real-time weather for '{user_input}'...]")
            data = get_current_weather_for_location(user_input)

            if data.get("status") != "success":
                err_msg = data.get("message", "Location not found.")
                print(f"[Error] {err_msg}")
                ConversationLogger.log_model(
                    agent_name="Pat",
                    session_id=session_id,
                    response=f"[Error] {err_msg}",
                )
                continue

            loc_name = data.get("location", user_input)
            forecast = data.get("forecast", {})
            alerts = data.get("alerts", {})

            summary_lines = [
                f"Location:     {loc_name}",
                f"Temperature:  {forecast.get('temperature', 'N/A')}",
            ]
            if "short_forecast" in forecast:
                summary_lines.append(f"Condition:    {forecast.get('short_forecast')}")
            elif "condition" in forecast:
                summary_lines.append(f"Condition:    {forecast.get('condition')}")
            if "wind" in forecast:
                summary_lines.append(f"Wind:         {forecast.get('wind')}")
            if "detailed_forecast" in forecast:
                summary_lines.append(f"Forecast:     {forecast.get('detailed_forecast')}")

            alert_list = alerts.get("alerts", [])
            if alert_list:
                summary_lines.append(f"Active Alerts ({len(alert_list)}):")
                for alt in alert_list:
                    summary_lines.append(f"   * [{alt.get('severity', 'Alert')}] {alt.get('event')}: {alt.get('headline')}")
            else:
                summary_lines.append("No active severe weather alerts.")

            formatted_summary = "\n".join(summary_lines)

            print("\n" + "=" * 55)
            print(formatted_summary)
            print("=" * 55)

            # 3. Log model / system response
            ConversationLogger.log_model(
                agent_name="Pat",
                session_id=session_id,
                response=formatted_summary,
            )

        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended. Goodbye!")
            break


async def run_adk_agent_bot():
    """Runs the full Google ADK Agent event loop."""
    print_banner()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        run_direct_demo_mode()
        return

    # Initialize the ADK InMemoryRunner with the weather agent
    runner = InMemoryRunner(agent=root_agent)
    user_id = "default_user"

    # Create a persistent session for multi-turn conversation
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
    )

    print("[Pat]: Hello! I'm Pat, your friendly weather assistant.")
    print("[Pat]: What city or location would you like the weather for today?\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n[Pat]: Stay safe and have a wonderful day! Goodbye!\n")
                break

            # Format the message for ADK Runner
            new_message = types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input)],
            )

            print("\n[Pat]: ", end="", flush=True)

            agent_responded = False

            # Drive the ADK Event Loop
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=new_message,
            ):
                # Inspect for tool invocations
                func_calls = event.get_function_calls()
                if func_calls:
                    for fc in func_calls:
                        args_summary = ", ".join(f"{k}='{v}'" for k, v in fc.args.items()) if fc.args else ""
                        print(f"\n[Tool Execution: {fc.name}({args_summary})]...\n[Pat]: ", end="", flush=True)

                # Extract generated text from event parts
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(part.text, end="", flush=True)
                            agent_responded = True

                # Check for errors in the event
                if event.error_code:
                    print(f"\n[ADK Error: {event.error_code}] {event.error_message}")
                    agent_responded = True

            print("\n")

        except (KeyboardInterrupt, EOFError):
            print("\n\n[Pat]: Session interrupted. Take care!\n")
            break
        except Exception as e:
            print(f"\n[Unexpected error]: {e}\n")


def main():
    """Main entrypoint."""
    try:
        asyncio.run(run_adk_agent_bot())
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")


if __name__ == "__main__":
    main()
