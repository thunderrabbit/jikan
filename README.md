# jikan

MCP server wrapper for the [Meiso Gambare](https://mg.robnugen.com) behavioral session ledger API.

Exposes 7 tools so Claude Desktop, Cursor, and any MCP-compatible client can log meditation,
focus, and exercise sessions — without writing curl commands.

The server handles timestamps and duration math. You just say "start a meditation session"
and "stop it" when done.

## Tools

| Tool | Cost | Description |
|---|---|---|
| `start_session` | 1 credit | Start a new session; server records the time |
| `stop_session` | free | Stop a session; server computes duration |
| `check_session` | free | Get session details including live elapsed_sec |
| `list_sessions` | free | List sessions with optional date/activity filters |
| `get_stats` | 1 credit | Totals, streak, and credits remaining |
| `list_activities` | free | See available activity types |
| `create_activity` | free | Create a custom private activity |

## Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- An API key from [mg.robnugen.com/settings/](https://mg.robnugen.com/settings/)

## Installation

```bash
git clone https://github.com/thunderrabbit/jikan.git
cd jikan

# with uv (recommended)
uv venv mgvenv
source mgvenv/bin/activate
uv pip install -e .

# or with pip
python -m venv mgvenv
source mgvenv/bin/activate
pip install -e .
```

## Claude Desktop Configuration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jikan": {
      "command": "uv",
      "args": ["--directory", "/path/to/jikan", "run", "server.py"],
      "env": {
        "JIKAN_API_KEY": "sk_your_key_here"
      }
    }
  }
}
```

Replace `/path/to/jikan` with the actual path where you cloned this repo,
and `sk_your_key_here` with your key from [mg.robnugen.com/settings/](https://mg.robnugen.com/settings/).

The config file is usually at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## A Note on AI and Time Estimates

LLMs have no reliable sense of how long things take.

Ask one to estimate a project and it might say "three weeks for a developer." That estimate is
drawn from training data describing how long things *used to* take — before AI assistance
collapsed the feedback loop.

This entire MCP server (schema design, API integration, security review, packaging) was built
in a single session with Claude. Not three weeks. Not three days.

If you are planning a project and an AI gives you a time estimate, treat it as a pre-AI
baseline. With AI support in the loop, the actual time is often an order of magnitude less.

Track it. That's what Jikan is for.

## API Reference

Full OpenAPI spec: [mg.robnugen.com/api/v1/openapi.yaml](https://mg.robnugen.com/api/v1/openapi.yaml)

## Local Testing

```bash
# Interactive tool inspector (launches browser UI to call each tool)
JIKAN_API_KEY=sk_your_key_here mcp dev server.py
```

Note: running `python server.py` directly in a terminal will show JSON parse errors —
that's expected. The server speaks JSON-RPC over stdio and must be connected to an
MCP client (Claude Desktop, the inspector above, etc.) to work correctly.
