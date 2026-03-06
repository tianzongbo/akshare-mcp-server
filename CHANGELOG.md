# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-03-06

### Added

- Initial MCP server implementation with `akshare-finance` tool namespace.
- Tools:
  - `get_a_share_quote(symbol)`
  - `get_a_share_history(symbol, start_date, end_date, period, adjust, limit)`
  - `get_china_index_snapshot(limit)`
- Fallback logic for unstable realtime/history endpoints.
- OpenCode and Claude Desktop configuration examples.
- Project metadata and packaging files (`pyproject.toml`, `requirements.txt`, `.gitignore`, `LICENSE`).
