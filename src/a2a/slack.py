"""
Slack Bot Integration using FastAPI.
Receives incoming Slack events (messages/mentions) and routes them through
the A2A agent network (Weather, Search, Gemini LLM) to generate responses.
"""

from fastapi import FastAPI, Request, Response
from python_a2a import AgentNetwork, A2AClient
import hmac
import hashlib
import time
import os
import logging
import httpx
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")

# A2A agent endpoints
WEATHER_AGENT_URL = os.getenv("WEATHER_AGENT_URL", "http://localhost:8001")
SEARCH_AGENT_URL = os.getenv("SEARCH_AGENT_URL", "http://localhost:8002")
LLM_AGENT_URL = os.getenv("LLM_AGENT_URL", "http://localhost:5001")

# --- FastAPI App ---
app = FastAPI(title="Slack A2A Bot", version="1.0.0")

# --- A2A Agent Network ---
network = AgentNetwork(name="Slack Bot Agent Network")
network.add("weather", WEATHER_AGENT_URL)
network.add("search", SEARCH_AGENT_URL)
llm_client = A2AClient(LLM_AGENT_URL)


def verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    """Verify that the request actually came from Slack."""
    if not SLACK_SIGNING_SECRET:
        logger.warning("SLACK_SIGNING_SECRET not set — skipping verification")
        return True

    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False  # Request too old

    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    computed = "v0=" + hmac.new(
        SLACK_SIGNING_SECRET.encode(), sig_basestring.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


async def send_slack_message(channel: str, text: str, thread_ts: str = None):
    """Post a message back to Slack."""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=payload,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.error(f"Slack API error: {data.get('error')}")


def route_to_agent(text: str) -> str:
    """Route the user message to the appropriate A2A agent and return a response."""
    text_lower = text.lower()

    try:
        # Weather queries
        if any(kw in text_lower for kw in ["weather", "temperature", "forecast"]):
            weather_agent = network.get_agent("weather")
            return weather_agent.ask(text)

        # Search queries
        if any(kw in text_lower for kw in ["search", "find", "look up", "lookup"]):
            search_agent = network.get_agent("search")
            return search_agent.ask(text)

        # Default: send to Gemini LLM for general conversation
        return llm_client.ask(text)

    except Exception as e:
        logger.error(f"Agent error: {e}")
        return f"Sorry, I encountered an error processing your request: {e}"


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Handle incoming Slack Events API requests.
    - URL verification challenge
    - message & app_mention events
    """
    body = await request.body()
    data = await request.json()

    # --- Slack URL Verification (one-time handshake) ---
    if data.get("type") == "url_verification":
        return {"challenge": data["challenge"]}

    # --- Signature verification ---
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if not verify_slack_signature(body, timestamp, signature):
        logger.warning("Invalid Slack signature")
        return Response(status_code=403)

    # --- Process events ---
    event = data.get("event", {})
    event_type = event.get("type")

    # Ignore bot's own messages to prevent loops
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return Response(status_code=200)

    if event_type in ("message", "app_mention"):
        user_text = event.get("text", "").strip()
        channel = event.get("channel", "")
        thread_ts = event.get("thread_ts") or event.get("ts")

        if not user_text:
            return Response(status_code=200)

        logger.info(f"Received from #{channel}: {user_text}")

        # Route to A2A agents and reply
        response_text = route_to_agent(user_text)
        await send_slack_message(channel, response_text, thread_ts)

    return Response(status_code=200)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "agents": ["weather", "search", "llm"]}


# ──────────────────────────────────────────────
# Run with: uvicorn slack:app --port 3000 --reload
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000)
