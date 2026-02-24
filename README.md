# meiso-gambare-mcp

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
git clone https://github.com/thunderrabbit/meiso-gambare-mcp.git
cd meiso-gambare-mcp

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
    "meiso-gambare": {
      "command": "uv",
      "args": ["--directory", "/path/to/meiso-gambare-mcp", "run", "server.py"],
      "env": {
        "MG_API_KEY": "sk_your_key_here"
      }
    }
  }
}
```

Replace `/path/to/meiso-gambare-mcp` with the actual path where you cloned this repo,
and `sk_your_key_here` with your key from [mg.robnugen.com/settings/](https://mg.robnugen.com/settings/).

The config file is usually at:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## API Reference

Full OpenAPI spec: [mg.robnugen.com/api/v1/openapi.yaml](https://mg.robnugen.com/api/v1/openapi.yaml)

## Local Testing

```bash
# Smoke test — should start without error (Ctrl-C to stop)
MG_API_KEY=sk_your_key_here python server.py

# Interactive tool inspector
mcp dev server.py
```
