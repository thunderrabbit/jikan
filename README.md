# jikan

AI agents have a time problem.

Every time you start a new conversation, the agent wakes up with no idea when you last spoke
because fundamentally: **LLMs have no internal clock.** They don't know what time it is, what day
it is, or how long your current conversation has lasted. From the model's perspective,
five minutes and five years are indistinguishable.

This time-blindness creates a real problem for tracking continuous work. If you ask an agent to log how much
time you spent debugging a complex issue, it can't tell you how long you worked. If you ask whether you've
been consistently putting in deep work lately, it has no way to know. It needs an external reference —
something outside itself that actually *measured* the time.

Jikan is that reference. The key design decision: **the server does the work agents are bad at.**

- The server records the exact start time — the agent never needs to know it
- The server computes elapsed duration — the agent never does date math
- The server maintains the session ledger between conversations — the agent never manages state

LLMs also have no reliable sense of how long *building things* takes.

Ask one to estimate a project and it might say "three weeks for a developer." That estimate is
drawn from training data describing how long things *used to* take — before AI assistance
collapsed the feedback loop.

This entire MCP server (schema design, API integration, security review, packaging) was built
in a single session with Claude. Not three weeks. Not three days.

If you are planning a project and an AI gives you a time estimate, treat it as a pre-AI
baseline. With AI support in the loop, the actual time is often an order of magnitude less.

Track it. That's what Jikan is for.

The server handles timestamps and duration math. You just say "start a meditation session"
and "stop the timer" when done.

Exposes 7 tools so Claude Desktop, Cursor, and any MCP-compatible client can log meditation,
focus, and exercise sessions — without writing curl commands.

---

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
