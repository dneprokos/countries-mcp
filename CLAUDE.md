# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Single-file FastMCP server (`server.py`) exposing REST Countries data over MCP stdio. No package layout, no test suite, no linter config — the whole implementation is `server.py`, plus one static JSON asset in `data/`.

## Commands

```bash
# Setup (Python 3.10+, uv required)
uv venv --python 3.10
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
cp .env.example .env      # then set RESTCOUNTRIES_API_KEY

# Run the server directly (stdio; sanity-check that it imports and starts)
.venv/Scripts/python.exe server.py
```

On macOS/Linux the interpreter is `.venv/bin/python` instead of `.venv/Scripts/python.exe`.

There are no tests, no lint step, and no build step. Verification is manual: start the server, or call the tool through a connected MCP client.

## MCP surface

`server.py` registers four kinds of MCP objects, all via FastMCP decorators:

- `@mcp.tool()` — `get_country_info(country_name)`, `shawarma_with_or_without_potatoes()` (joke tool, Ukrainian text, returns `images/kebab.png` inlined as a base64 data URI)
- `@mcp.resource("countries://country-codes")` — serves `data/country_codes.json`
- `@mcp.prompt()` — `compare_countries_prompt`, `country_research_prompt`

FastMCP derives tool schemas from type hints and tool descriptions from docstrings, so signature and docstring are the public API — changing either changes what clients see.

## Architecture notes

**REST Countries v5 is the only backend, and it is not v3.1.** The old free `v3.1` endpoints are retired and now answer every request with a deprecation notice. All calls go to `https://api.restcountries.com/countries/v5/name?q=...` with `Authorization: Bearer <key>`. Response shape differs from v3.1 in ways the formatter depends on: `data.objects` is always a list, `capitals` are objects with `name`/coordinates, `languages` and `currencies` are lists of objects (not code-keyed dicts), `area` splits into `kilometers`/`miles`, `names.native` is keyed by ISO 639-3.

**`RESPONSE_FIELDS` (server.py:26-39) is a hard gate on what the tool can return.** A full v5 record has 90+ fields; the server requests 12. Fields like calling codes, timezones, borders, TLDs, driving side and flag emoji are *never fetched*, so they cannot appear in output no matter what the caller asks. Adding a field to the formatter requires adding it to `RESPONSE_FIELDS` too, or it will silently be missing.

**Demo-key fallback.** A missing `RESTCOUNTRIES_API_KEY` falls back to the public `rc_live_demo` key so the server degrades to "works, with a warning" instead of a 401. The demo key returns a fixed sample country and ignores the search term — the tool appends an explicit warning line in that case. If results look wrong and identical across queries, check the key first.

**Tools return error strings, never raise.** Every failure path — blank input, non-JSON body, non-200, transport error, unexpected exception — returns a human-readable `Error: ...` string. `_error_for_status` maps status codes to actionable hints (401 → key problem, 429 → ~20 req/10s rate limit). Keep this contract when adding tools; an escaping exception surfaces to the MCP client as a protocol-level failure instead of a usable message.

**Search is substring-based, so disambiguation is explicit.** `q=` matches loosely ("Ukraine", "India" can each return several records). `_best_match` resolves in priority order: exact common name → exact official name → exact alternate name → first result. When more than one country matched, the tool appends an `Other matches:` line (capped at 9) so the caller can re-query rather than trust the top hit.

**Paths resolve from `__file__`, not cwd.** `.env`, `data/country_codes.json` and `images/kebab.png` are all loaded relative to `Path(__file__).parent` because MCP clients launch the server from arbitrary working directories. Preserve this for any new file access.

## Client integration

Clients (Cursor, Claude Code, etc.) launch the server by absolute path to the venv interpreter plus absolute path to `server.py` in their `mcp.json`. Consequence: **the client must be restarted after any change to `server.py`** — edits are not hot-reloaded, and a tool that appears stale is usually a stale process.

## Docs to keep in sync

`README.md` documents setup, client config, and the extension pattern for new tools. `PROMPT_USAGE.md` documents the prompts and the shawarma tool. Adding or changing an MCP object means updating both.

## Cursor rules

`.cursor/rules/AGENTS.md` exists but is a generic FastAPI/Pydantic/SQLAlchemy ruleset that does not describe this stack (no FastAPI, no Pydantic models, no DB). The parts that do apply: functional style over classes, type hints on all signatures, guard clauses and early returns for error conditions with the happy path last, no unnecessary `else`. Note `.cursor/` is git-ignored, so that file is local-only and not shared with collaborators.
