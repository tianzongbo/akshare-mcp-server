# AkShare MCP Server

Local MCP server exposing AkShare tools for A-share and index data.

## Features

- Query single-stock latest data: `get_a_share_quote`
- Query historical bars by date range: `get_a_share_history`
- Query China index snapshot: `get_china_index_snapshot`
- Built-in fallback logic for unstable realtime endpoints

## Tool List

1. `get_a_share_quote(symbol)`
   - Input example: `000001`
   - Output: realtime quote if available, otherwise latest daily fallback

2. `get_a_share_history(symbol, start_date, end_date, period="daily", adjust="", limit=120)`
   - Date format: `YYYYMMDD`
   - `period`: `daily | weekly | monthly`
   - `adjust`: `"" | "qfq" | "hfq"`

3. `get_china_index_snapshot(limit=20)`
   - Snapshot source: Sina
   - Fallback: recent bar from index daily endpoint

## Install

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Run Server

```bash
./.venv/bin/python server.py
```

Server runs via stdio transport and is ready for MCP clients.

## OpenCode Configuration

Add this block to your `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "akshare-finance": {
      "type": "local",
      "enabled": true,
      "command": [
        "/ABSOLUTE/PATH/TO/.venv/bin/python",
        "/ABSOLUTE/PATH/TO/akshare_mcp_server/server.py"
      ]
    }
  }
}
```

Then verify:

```bash
opencode mcp list
```

Expected: `akshare-finance` shows `connected`.

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "akshare-finance": {
      "command": "/ABSOLUTE/PATH/TO/.venv/bin/python",
      "args": ["/ABSOLUTE/PATH/TO/akshare_mcp_server/server.py"]
    }
  }
}
```

## Example Prompts

- "用 akshare-finance 查 000001 最近 30 个交易日"
- "用 akshare-finance 查中国主要指数快照"
- "用 akshare-finance 查 600519 从 20240101 到 20240301 的日线"

## Notes

- `get_a_share_quote` and `get_a_share_history` include fallback to Sina daily when Eastmoney realtime/history endpoints are unstable.
- If your network is unstable, retry once before concluding endpoint failure.
