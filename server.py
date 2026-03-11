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
def create_past_session(
    activity_id: int,
    start_time: str,
    end_time: str,
    timezone: str = JIKAN_DEFAULT_TZ,
) -> dict:
    """Create a completed session retroactively with custom start/end times. Costs 1 credit.

    Use this when the user forgot to start a timer, or wants to log a past
    activity. The session is created already stopped with actual_sec computed
    from the time difference.

    Args:
        activity_id: Activity type ID. Use list_activities to see all options.
        start_time: When the session started. Accepts ISO format (e.g. '2025-03-11T14:00:00')
                    or 'HH:MM' for today in the given timezone.
        end_time: When the session ended. Same formats as start_time.
        timezone: IANA timezone name, e.g. 'Asia/Tokyo' (default reflects JIKAN_DEFAULT_TZ).
    """
    from datetime import datetime, date as date_cls

    def _expand_time(raw: str, tz: str) -> str:
        """If raw looks like HH:MM, expand to today's ISO datetime in tz."""
        raw = raw.strip()
        if len(raw) <= 5 and ":" in raw and "T" not in raw and "-" not in raw:
            try:
                from zoneinfo import ZoneInfo
            except ImportError:
                from backports.zoneinfo import ZoneInfo
            today = datetime.now(ZoneInfo(tz)).date()
            return f"{today}T{raw}:00"
        return raw

    start_time = _expand_time(start_time, timezone)
    end_time = _expand_time(end_time, timezone)

    payload = {
        "activity_id": activity_id,
        "start_time": start_time,
        "end_time": end_time,
        "timezone": timezone,
    }
    with _client() as client:
        response = client.post("/sessions/backfill", json=payload)
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
def delete_session(ak_id: int) -> dict:
    """Delete a session. Free (0 credits).

    Args:
        ak_id: The session ID to delete.
    """
    with _client() as client:
        response = client.delete(f"/sessions/{ak_id}")
    if response.status_code == 204:
        return {"deleted": True, "ak_id": ak_id}
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
def rename_emotion_vocab(my_id: int, state: str) -> dict:
    """Rename an existing vocab entry. Preserves the my_id and all event associations.

    Args:
        my_id: The vocab entry's numeric handle
        state: The new label for this emotional state
    """
    with _client() as client:
        response = client.patch("/emotions/vocab", json={"my_id": my_id, "state": state})
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
def patch_emotion_event(
    event_id: int,
    content: str | None = None,
    my_id: int | None = None,
) -> dict:
    """Update an existing event's content and/or tag. Only provided fields are changed.

    Args:
        event_id: The event ID to update
        content: New content text (omit to leave unchanged)
        my_id: Vocab my_id to tag with (omit to leave unchanged)
    """
    payload: dict = {"event_id": event_id}
    if content is not None:
        payload["content"] = content
    if my_id is not None:
        payload["my_id"] = my_id
    with _client() as client:
        response = client.patch("/emotions/events", json=payload)
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


# ── Todo tools ────────────────────────────────────────────────────────────────


@mcp.tool()
def list_todos(timezone: str = JIKAN_DEFAULT_TZ) -> dict:
    """Get today's todos based on recurrence rules and timezone. Free (0 credits).

    Returns todos filtered by day-of-week, day-of-month, due date, and
    days-between rules. Includes completion status for today.

    Args:
        timezone: IANA timezone name, e.g. 'Asia/Tokyo'
    """
    with _client() as client:
        response = client.get("/todos/list", params={"timezone": timezone})
    return response.json()


@mcp.tool()
def complete_todo(
    todo_id: int,
    nth: int = 1,
    timezone: str = JIKAN_DEFAULT_TZ,
) -> dict:
    """Mark a todo as completed for today. Free (0 credits).

    Args:
        todo_id: The todo to complete
        nth: Which occurrence (1 for first, 2 for second, etc.)
        timezone: IANA timezone name
    """
    with _client() as client:
        response = client.post("/todos/complete", json={
            "todo_id": todo_id, "nth": nth, "timezone": timezone
        })
    return response.json()


@mcp.tool()
def uncomplete_todo(
    todo_id: int,
    nth: int = 1,
    timezone: str = JIKAN_DEFAULT_TZ,
) -> dict:
    """Remove a todo completion for today. Free (0 credits).

    Args:
        todo_id: The todo to uncomplete
        nth: Which occurrence to remove
        timezone: IANA timezone name
    """
    with _client() as client:
        response = client.post("/todos/uncomplete", json={
            "todo_id": todo_id, "nth": nth, "timezone": timezone
        })
    return response.json()


@mcp.tool()
def create_todo(
    title: str,
    do_days: str = "",
    do_dates: str = "",
    do_every_n_days: int | None = None,
    due_date: str = "",
    do_time: str = "",
    target_count: int = 1,
    activity_id: int | None = None,
    description: str = "",
) -> dict:
    """Create a new todo. Free (0 credits).

    Args:
        title: Todo title
        do_days: Comma-separated days of week (e.g. 'Mon,Wed,Fri')
        do_dates: Comma-separated dates of month (e.g. '1,15,30')
        do_every_n_days: Repeat every N days after completion (1-365)
        due_date: One-time due date (YYYY-MM-DD)
        do_time: Time of day (HH:MM)
        target_count: How many times per day (default 1)
        activity_id: Link to an activity for timed todos
        description: Optional description
    """
    payload: dict = {"title": title}
    if do_days:
        payload["do_days"] = do_days
    if do_dates:
        payload["do_dates"] = do_dates
    if do_every_n_days is not None:
        payload["do_every_n_days"] = do_every_n_days
    if due_date:
        payload["due_date"] = due_date
    if do_time:
        payload["do_time"] = do_time
    if target_count != 1:
        payload["target_count"] = target_count
    if activity_id is not None:
        payload["activity_id"] = activity_id
    if description:
        payload["description"] = description
    with _client() as client:
        response = client.post("/todos/create", json=payload)
    return response.json()


@mcp.tool()
def update_todo(todo_id: int, field: str, value: str) -> dict:
    """Update a single field on a todo. Free (0 credits).

    Args:
        todo_id: The todo to update
        field: Field name (title, do_time, due_date, target_duration_seconds, do_every_n_days, is_timer, is_counter)
        value: New value for the field
    """
    with _client() as client:
        response = client.patch("/todos/update", json={
            "todo_id": todo_id, "field": field, "value": value
        })
    return response.json()


@mcp.tool()
def archive_todo(todo_id: int) -> dict:
    """Soft-delete a todo (sets is_active = 0). Free (0 credits).

    Args:
        todo_id: The todo to archive
    """
    with _client() as client:
        response = client.request("DELETE", "/todos/archive", json={"todo_id": todo_id})
    return response.json()


@mcp.tool()
def complete_todo_with_session(
    todo_id: int,
    ak_id: int,
    duration_seconds: int | None = None,
    timezone: str = JIKAN_DEFAULT_TZ,
) -> dict:
    """Complete a timed todo and link it to an activity session. Free (0 credits).

    Automatically determines the nth completion for today.

    Args:
        todo_id: The todo to complete
        ak_id: The activity_kai session ID to link
        duration_seconds: Override duration (otherwise uses session duration)
        timezone: IANA timezone name
    """
    payload: dict = {"todo_id": todo_id, "ak_id": ak_id, "timezone": timezone}
    if duration_seconds is not None:
        payload["duration_seconds"] = duration_seconds
    with _client() as client:
        response = client.post("/todos/complete-with-session", json=payload)
    return response.json()


@mcp.tool()
def todo_history(limit: int = 20, offset: int = 0) -> dict:
    """List fully completed todos with pagination. Free (0 credits).

    Args:
        limit: Max results (default 20, max 50)
        offset: Pagination offset
    """
    with _client() as client:
        response = client.get("/todos/history", params={
            "limit": limit, "offset": offset
        })
    return response.json()


# ── Agent Inbox tools ─────────────────────────────────────────────────────────


@mcp.tool()
def list_inbox(
    status: str = "",
    limit: int = 50,
    offset: int = 0,
    include_future: bool = True,
) -> dict:
    """List messages in the agent inbox. Free (0 credits).

    Call this at session start to check for pending instructions from the user.

    Args:
        status: Filter by status: 'pending', 'seen', 'done', or '' for all.
        limit: Max results (default 50, max 100).
        offset: Pagination offset.
        include_future: Include messages with a future show_date (default True).
    """
    params: dict = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    if include_future:
        params["include_future"] = 1
    with _client() as client:
        response = client.get("/inbox/list", params=params)
    return response.json()


@mcp.tool()
def send_inbox(message: str, priority: str = "normal") -> dict:
    """Send a message to the agent inbox. Free (0 credits).

    Use this when the user wants to leave a note for a future session,
    or when you need to save an instruction for later processing.

    Args:
        message: The message text.
        priority: 'low', 'normal', or 'high' (default 'normal').
    """
    with _client() as client:
        response = client.post("/inbox/send", json={
            "message": message, "priority": priority
        })
    return response.json()


@mcp.tool()
def mark_inbox_seen(message_id: int) -> dict:
    """Mark an inbox message as seen. Free (0 credits).

    Call this after reading a message to acknowledge you've seen it.

    Args:
        message_id: The message to mark as seen.
    """
    with _client() as client:
        response = client.patch("/inbox/mark-seen", json={
            "message_id": message_id
        })
    return response.json()


@mcp.tool()
def mark_inbox_done(message_id: int, response: str = "") -> dict:
    """Mark an inbox message as done, with an optional response. Free (0 credits).

    Call this after you've acted on a message. The response is visible
    to the user on the web interface.

    Args:
        message_id: The message to mark as done.
        response: Optional note about what you did (shown to user).
    """
    payload: dict = {"message_id": message_id}
    if response:
        payload["response"] = response
    with _client() as client:
        resp = client.patch("/inbox/mark-done", json=payload)
    return resp.json()


@mcp.tool()
def edit_inbox(message_id: int, message: str = "", priority: str = "") -> dict:
    """Edit an inbox message's text and/or priority. Free (0 credits).

    Args:
        message_id: The message to edit.
        message: New message text (omit to keep current).
        priority: New priority: 'low', 'normal', or 'high' (omit to keep current).
    """
    payload: dict = {"message_id": message_id}
    if message:
        payload["message"] = message
    if priority:
        payload["priority"] = priority
    with _client() as client:
        response = client.patch("/inbox/edit", json=payload)
    return response.json()


@mcp.tool()
def archive_inbox(message_id: int) -> dict:
    """Archive an inbox message (soft-hide). Free (0 credits).

    Use this instead of delete to preserve history.

    Args:
        message_id: The message to archive.
    """
    with _client() as client:
        response = client.patch("/inbox/archive", json={
            "message_id": message_id
        })
    return response.json()


@mcp.tool()
def delete_inbox(message_id: int) -> dict:
    """Delete an inbox message. Free (0 credits).

    Args:
        message_id: The message to delete.
    """
    with _client() as client:
        response = client.request("DELETE", "/inbox/delete", json={
            "message_id": message_id
        })
    return response.json()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
