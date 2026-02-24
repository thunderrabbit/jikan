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
    timezone: str = "UTC",
    intended_sec: int = 0,
) -> dict:
    """Start a new behavioral session. Costs 1 credit.

    The server records the current time automatically — the agent does not
    need to track time. Returns the new session including its ak_id, which
    you need to stop or check the session later.

    Args:
        activity_id: Activity type ID (default 1 = Meditation).
                     Use list_activities to see all options.
        timezone: IANA timezone name, e.g. 'Asia/Tokyo' (default UTC).
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


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
