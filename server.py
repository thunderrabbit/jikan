import os
import sys
import httpx
from mcp.server.fastmcp import FastMCP

# Fail fast if API key is missing
JIKAN_API_KEY = os.environ.get("JIKAN_API_KEY")
if not JIKAN_API_KEY:
    print("ERROR: JIKAN_API_KEY environment variable is not set.", file=sys.stderr)
    print("Generate a key at https://mg.robnugen.com/settings/", file=sys.stderr)
    sys.exit(1)

MG_BASE_URL = os.environ.get("MG_BASE_URL", "https://mg.robnugen.com/api/v1")
JIKAN_DEFAULT_TZ = os.environ.get("JIKAN_DEFAULT_TZ", "UTC")

mcp = FastMCP("jikan")

HEADERS = {
    "X-API-Key": JIKAN_API_KEY,
    "Content-Type": "application/json",
}


def _client() -> httpx.Client:
    return httpx.Client(base_url=MG_BASE_URL, headers=HEADERS, timeout=30)


@mcp.tool()
def start_session(
    activity_id: int = 1,
    timezone: str = JIKAN_DEFAULT_TZ,
    intended_sec: int = 0,
) -> dict:
    """Start a new behavioral session. Costs 1 credit.

    The server records the current time automatically — the agent does not
    need to track time. Returns the new session including its ak_id, which
    you need to stop or check the session later.

    Args:
        activity_id: Activity type ID (default 1 = Meditation).
                     Use list_activities to see all options.
        timezone: IANA timezone name, e.g. 'Asia/Tokyo' (default reflects JIKAN_DEFAULT_TZ).
        intended_sec: Planned duration in seconds (default 0 = open-ended).
    """
    payload = {
        "activity_id": activity_id,
        "timezone": timezone,
        "intended_sec": intended_sec,
    }
    with _client() as client:
        response = client.post("/sessions", json=payload)
    return response.json()


@mcp.tool()
def stop_session(ak_id: int) -> dict:
    """Stop an active session. Free (0 credits).

    The server computes actual_sec automatically using the stored start time.
    The agent does not need to track elapsed time.

    Args:
        ak_id: The session ID returned by start_session.
    """
    with _client() as client:
        response = client.patch(f"/sessions/{ak_id}/stop")
    return response.json()


@mcp.tool()
def check_session(ak_id: int) -> dict:
    """Get details for a single session, including elapsed_sec if active. Free (0 credits).

    Args:
        ak_id: The session ID to look up.
    """
    with _client() as client:
        response = client.get(f"/sessions/{ak_id}")
    return response.json()


@mcp.tool()
def list_sessions(
    from_date: str = "",
    to_date: str = "",
    activity_id: int = 0,
    limit: int = 20,
    offset: int = 0,
    is_active: int = -1,
) -> dict:
    """List completed and active sessions. Free (0 credits).

    Args:
        from_date: Start date filter in YYYY-MM-DD format (optional).
        to_date: End date filter in YYYY-MM-DD format (optional).
        activity_id: Filter by activity type ID (optional, 0 = no filter).
        limit: Number of results to return (default 20, max 50).
        offset: Pagination offset (default 0).
        is_active: Filter by active status (1 = running, 0 = stopped, -1 = no filter).
    """
    params: dict = {"limit": limit, "offset": offset}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if activity_id:
        params["activity_id"] = activity_id
    if is_active in (0, 1):
        params["is_active"] = is_active
    with _client() as client:
        response = client.get("/sessions", params=params)
    return response.json()


@mcp.tool()
def get_stats() -> dict:
    """Get pre-computed session aggregates. Costs 1 credit.

    Returns total sessions, total seconds, current streak in days, and
    credits remaining. Offloads all calendar arithmetic to the server.
    """
    with _client() as client:
        response = client.get("/stats")
    return response.json()


@mcp.tool()
def list_activities() -> dict:
    """List available activity types (FREE, PUBLIC, and your PRIVATE). Free (0 credits)."""
    with _client() as client:
        response = client.get("/activities")
    return response.json()


@mcp.tool()
def create_activity(activity_name: str, description: str = "") -> dict:
    """Create a custom PRIVATE activity visible only to your account. Free (0 credits).

    Args:
        activity_name: Name for the new activity (max 64 characters).
        description: Optional description of the activity.
    """
    payload: dict = {"activity_name": activity_name}
    if description:
        payload["description"] = description
    with _client() as client:
        response = client.post("/activities", json=payload)
    return response.json()


# ── Emotional Interaction Ledger tools ────────────────────────────────────────


@mcp.tool()
def post_emotion_vocab(state: str) -> dict:
    """Add a new state label to the agent's private vocabulary.
    Returns my_id: the agent's private numeric handle for this state.
    Call when the state is not yet in the loaded vocab.

    Args:
        state: Label for this emotional state (any string, e.g. 'frustration_at_jargon')
    """
    with _client() as client:
        response = client.post("/emotions/vocab", json={"state": state})
    return response.json()


@mcp.tool()
def get_emotion_vocab() -> list:
    """Load the agent's full private vocabulary. Call once at session start.
    Returns a list of {my_id, state} pairs. Hold in context for the session.
    Returns [] on a fresh install.
    """
    with _client() as client:
        response = client.get("/emotions/vocab")
    return response.json()


@mcp.tool()
def log_emotion_event(
    event_type: str,
    content: str,
    my_id: int | None = None,
) -> dict:
    """Log an interaction event to the emotional ledger.

    Args:
        event_type: 'user_reaction', 'user_input', or 'agent_action'
        content: Specific honest observation about what happened
        my_id: Vocab my_id for this state (omit if event has no state tag)
    """
    payload: dict = {"event_type": event_type, "content": content}
    if my_id is not None:
        payload["my_id"] = my_id
    with _client() as client:
        response = client.post("/emotions/events", json=payload)
    return response.json()


@mcp.tool()
def get_emotion_events(
    my_id: int | None = None,
    session_id: int | None = None,
    from_date: str = "",
    to_date: str = "",
    event_type: str = "",
    limit: int = 50,
) -> list:
    """Query past interaction events. At least one of my_id, session_id, or from_date required.

    Args:
        my_id: Filter by emotional state (agent's private vocab ID)
        session_id: Filter to a specific session
        from_date: ISO datetime start of range
        to_date: ISO datetime end of range
        event_type: 'agent_action', 'user_input', or 'user_reaction'
        limit: Max results (default 50, max 200)
    """
    params: dict = {"limit": limit}
    if my_id is not None:
        params["my_id"] = my_id
    if session_id is not None:
        params["session_id"] = session_id
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    if event_type:
        params["event_type"] = event_type
    with _client() as client:
        response = client.get("/emotions/events", params=params)
    return response.json()


@mcp.tool()
def get_emotion_sessions(
    from_date: str = "",
    to_date: str = "",
    limit: int = 20,
) -> list:
    """List past interaction sessions with duration and event count. No decryption required.

    Args:
        from_date: ISO datetime start of range
        to_date: ISO datetime end of range
        limit: Max results (default 20, max 100)
    """
    params: dict = {"limit": limit}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    with _client() as client:
        response = client.get("/emotions/sessions", params=params)
    return response.json()


@mcp.tool()
def delete_emotion_event(event_id: int) -> dict:
    """Delete a single event by event_id. Returns {"deleted": 1} or {"deleted": 0}.
    Never returns 404 — avoids leaking whether an ID exists.
    """
    with _client() as client:
        response = client.request("DELETE", "/emotions/events", json={"event_id": event_id})
    return response.json()


@mcp.tool()
def delete_emotion_vocab(my_id: int) -> dict:
    """Delete a vocab entry by my_id. Associated events are preserved but lose
    their state tag (mifmus_id set to NULL). Returns {"deleted": 1, "events_untagged": N}.
    """
    with _client() as client:
        response = client.request("DELETE", "/emotions/vocab", json={"my_id": my_id})
    return response.json()


@mcp.tool()
def delete_emotion_everything() -> dict:
    """Wipe ALL emotional data for this API key: all events, sessions, and vocab.
    This is irreversible. The confirmation string is handled automatically.
    Returns counts of deleted rows.
    """
    with _client() as client:
        response = client.request("DELETE", "/emotions/everything", json={"confirm": "delete everything"})
    return response.json()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
