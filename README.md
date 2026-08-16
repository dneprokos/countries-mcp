# Countries MCP Server

![Countries MCP](images/Coutries_MCP.png)

A Model Context Protocol (MCP) server built with FastMCP that serves country information from the REST Countries API v5. It exposes two tools, one resource, and two prompt templates over stdio to any MCP-compatible client — Cursor, Claude Code, and others.

## MCP surface

| Type | Name | What it does |
|------|------|--------------|
| Tool | `get_country_info(country_name)` | Fetches one country from REST Countries v5 and formats it |
| Tool | `shawarma_with_or_without_potatoes()` | Joke tool (Ukrainian): answers "with potatoes", returns `images/kebab.png` inline |
| Resource | `countries://country-codes` | Serves `data/country_codes.json` |
| Prompt | `compare_countries_prompt(country1, country2)` | Structured two-country comparison |
| Prompt | `country_research_prompt(country_name, focus_areas="all")` | Country research with optional focus areas |

See [PROMPT_USAGE.md](PROMPT_USAGE.md) for prompt-by-prompt usage details.

## Features

- **Get Country Information Tool**: Retrieve detailed information about any country by name
  - Country name (common, official, and native names)
  - Capital city (or cities)
  - Region and subregion
  - Population
  - Area in km²
  - Languages
  - Currencies (code, name, symbol)
  - ISO alpha-2 / alpha-3 codes
  - Flag emoji and flag image URL
  - `Other matches:` line when the search term matched more than one country

- **Country Codes Resource**: Access a static JSON file with common country codes and names
  - 30+ countries with ISO codes
  - Quick reference for country codes
  - Available as a read-only resource

- **Prompt Templates**: Ready-made comparison and research workflows exposed to the client's prompt picker

- **Graceful errors**: Every failure path returns a readable `Error: ...` string (bad key, rate limit, transport error) instead of raising

## Prerequisites

- Python 3.10 or higher
- `uv` package manager (for installing FastMCP)
- Cursor IDE (for integration)

## Installation

### 1. Install `uv` Package Manager

`uv` is required to install FastMCP and its dependencies.

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, add `uv` to your PATH or restart your terminal.

### 2. Set Up the Project

1. Clone or navigate to this project directory:
   ```bash
   cd countries-mcp
   ```

2. Create a virtual environment with Python 3.10+:
   ```bash
   uv venv --python 3.10
   ```

3. Install dependencies:
   ```bash
   uv pip install --python .venv/Scripts/python.exe fastmcp httpx python-dotenv
   ```

   Or if you prefer using the requirements file:
   ```bash
   uv pip install --python .venv/Scripts/python.exe -r requirements.txt
   ```

4. Add your REST Countries API key:
   ```bash
   cp .env.example .env
   ```

   Then open `.env` and set your key:
   ```
   RESTCOUNTRIES_API_KEY=rc_live_your_key_here
   ```

   Get a key from [restcountries.com](https://restcountries.com/) ("Get an API key").
   The old free v3.1 API was retired, so v5 requires a key. Without one the server
   falls back to the public demo key, which returns a fixed sample country and
   ignores your search term.

   `.env` is git-ignored — never commit your key.

## Client Configuration

The server speaks MCP over **stdio**: the client launches it with the venv interpreter and the absolute path to `server.py`.

### Cursor

#### Step 1: Locate Your MCP Configuration File

The MCP configuration file is located at:
- **Windows**: `C:\Users\<YourUsername>\.cursor\mcp.json`
- **macOS/Linux**: `~/.cursor/mcp.json`

#### Step 2: Add the Server Configuration

Open `mcp.json` and add the `countries-mcp` server configuration. Your file should look like this:

```json
{
  "mcpServers": {
    "countries-mcp": {
      "command": "C:/PersonalProjects/mcp-servers/countries-mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/PersonalProjects/mcp-servers/countries-mcp/server.py"
      ]
    }
  }
}
```

**Important Notes:**
- Update the path to match your actual project location
- On Windows, use forward slashes (`/`) or escaped backslashes (`\\`) in paths
- On macOS/Linux, the Python executable will be at `.venv/bin/python` instead of `.venv/Scripts/python.exe`

#### Step 3: Restart Cursor

After saving `mcp.json`, restart Cursor IDE completely for the changes to take effect.

#### Step 4: Verify Installation

After restarting, you can verify the server is working by asking in Cursor's chat:
- "Get information about Ukraine"
- "What's the capital of France?"

If the server is configured correctly, Cursor will use the tool to fetch country information.

### Claude Code

Register the same command with the CLI:

```bash
claude mcp add countries-mcp -- C:/PersonalProjects/mcp-servers/countries-mcp/.venv/Scripts/python.exe C:/PersonalProjects/mcp-servers/countries-mcp/server.py
```

Then check it with `/mcp` in a Claude Code session. Any other MCP client works the same way — same command, same two arguments.

> **Restart after every edit.** `server.py` is not hot-reloaded. A tool that looks stale is almost always a stale server process.

## Usage

Once configured, you can use the tools, the resource, and the prompts from your MCP client's chat interface (examples below use Cursor wording):

### Using Tools - Get Country Information

The `get_country_info` tool fetches detailed information about any country by name. Here are example prompts:

**Basic Information Requests:**
- "Get information about Ukraine"
- "What are the details for the United States?"
- "Show me country information for Japan"
- "Get country info for Brazil"
- "What's the capital of France?"

**Specific Information Requests:**
- "Tell me about Germany's population and area"
- "What languages are spoken in Canada?"
- "Show me the currency used in Australia"
- "Get the flag URL for Italy"
- "What's the region and subregion of Mexico?"

**Multiple Countries:**
- "Get information about both France and Spain"
- "Compare Ukraine and Poland"
- "Show me details for Japan and South Korea"

The AI will automatically detect your request and use the `get_country_info` tool to fetch the information.

### Using Resources - Country Codes Reference

The `countries://country-codes` resource provides a static JSON file with common country codes and names. Here are example prompts:

**Accessing the Resource:**
- "Show me the country codes resource"
- "What countries are available in the country codes file?"
- "Read the country codes resource"
- "Get the list of country codes"
- "Show me the country codes JSON"

**Using the Resource in Context:**
- "Use the country codes resource to find the code for United States"
- "Check the country codes file and tell me what code Ukraine has"
- "From the country codes resource, list all available countries"
- "What country codes are in the resource file?"

**Combining Tool and Resource:**
- "First show me the country codes, then get detailed info for Ukraine"
- "List the country codes and then get information about one of them"
- "Check the country codes resource and get details for a country from that list"

The resource returns a JSON structure with country codes and names that can be used as a reference when working with country data.

### Using Tools - Shawarma (joke tool)

`shawarma_with_or_without_potatoes` takes no arguments and always answers the same way: **з картоплею краща** ("with potatoes is better"), together with the kebab photo from `images/kebab.png` inlined as a base64 data URI. The answer text is in Ukrainian.

Example prompts (any language triggers it):
- "Яка шаурма краще — з картоплею чи без?"
- "Which shawarma is better, with potatoes or without?"

### Using Prompts - Structured Country Analysis

The server provides prompt templates that guide structured country analysis. Prompts are available in Cursor's prompt picker or can be invoked directly.

#### Compare Countries Prompt

The `compare_countries_prompt` helps you systematically compare two countries. In Cursor:

1. **Using the Prompt Picker:**
   - Open Cursor's chat
   - Look for the prompt picker (usually accessible via a prompt icon or menu)
   - Select "compare_countries_prompt"
   - Provide the two country names when prompted

2. **Direct Invocation:**
   - Simply ask: "Use the compare countries prompt for Ukraine and Poland"
   - Or: "Compare France and Germany using the comparison prompt"

3. **What it does:**
   - Automatically fetches detailed information for both countries
   - Compares population, area, capitals, languages, currencies, and regions
   - Highlights differences and similarities
   - Provides a structured comparison summary

**Example Usage:**
- "Use the compare countries prompt to compare United States and Canada"
- "Compare Japan and South Korea using the comparison prompt"
- "Run the country comparison prompt for Brazil and Argentina"

#### Country Research Prompt

The `country_research_prompt` helps you research a country with optional focus areas.

**Usage:**
- "Use the country research prompt for Ukraine"
- "Research Japan with focus on population and currency"
- "Use the research prompt for France, focusing on geography and languages"

**Focus Areas:**
- You can specify focus areas like: "geography", "population", "currency", "languages"
- Or use "all" (default) for comprehensive information
- Example: "Research Germany focusing on population,currency,area"

## Project Structure

```
countries-mcp/
├── server.py              # Whole implementation: tools, resource, prompts
├── data/
│   └── country_codes.json # Backing file for the countries://country-codes resource
├── images/
│   ├── Coutries_MCP.png   # README banner
│   └── kebab.png          # Returned by the shawarma tool
├── .env.example           # Template for RESTCOUNTRIES_API_KEY
├── .env                   # Your key (git-ignored, created during setup)
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata
├── PROMPT_USAGE.md        # Prompt and shawarma-tool usage guide
├── CLAUDE.md              # Guidance for Claude Code in this repo
├── .venv/                 # Virtual environment (created during setup)
└── README.md              # This file
```

All runtime paths (`.env`, `data/`, `images/`) resolve from `Path(__file__).parent`, not the working directory, because MCP clients launch the server from arbitrary locations. Keep that pattern for any new file access.

## Extending the Server

This server is designed to be easily extended with additional tools. Here's how to add new tools:

### Adding a New Tool

1. **Define your tool function** in `server.py`:

```python
@mcp.tool()
def your_new_tool(parameter: str) -> str:
    """Description of what your tool does.
    
    Args:
        parameter: Description of the parameter
    
    Returns:
        Description of what the tool returns
    """
    # Your implementation here
    return "Result"
```

2. **Example: Adding a tool to get country by code**

```python
@mcp.tool()
def get_country_by_code(country_code: str) -> str:
    """Get country information by ISO country code (e.g., 'US', 'UA', 'GB').
    
    Args:
        country_code: Two-letter ISO country code
    
    Returns:
        Formatted country information
    """
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            response = client.get(
                f"{API_BASE}/codes.alpha_2/{country_code}",
                headers={"Authorization": f"Bearer {os.getenv('RESTCOUNTRIES_API_KEY')}"},
            )
            payload = response.json()
            if response.status_code != 200:
                return _error_for_status(response.status_code, payload)
            countries = payload.get("data", {}).get("objects", [])
            if not countries:
                return f"Error: Country code '{country_code}' not found"
            # v5 always returns records as a list under data.objects
            return "\n".join(_format_country(countries[0]))
    except httpx.HTTPError as e:
        return f"Error: {str(e)}"
```

3. **Restart the server** - After adding new tools, restart Cursor for the changes to take effect.

### Best Practices for Extending

- **Use type hints**: FastMCP uses type hints to generate tool schemas automatically
- **Write clear docstrings**: The docstring becomes the tool description in MCP
- **Never raise**: Return an `Error: ...` string instead. An escaping exception reaches the client as a protocol failure, not a usable message
- **Add new fields to `RESPONSE_FIELDS`**: The server requests only 12 of the 90+ v5 fields. A field the formatter reads but `RESPONSE_FIELDS` does not request is silently missing
- **Resolve paths from `__file__`**: Not from the working directory
- **Follow the existing pattern**: Keep code style consistent with existing tools
- **Test your tools**: Verify new tools work before committing

## Dependencies

- **fastmcp**: FastMCP framework for building MCP servers
- **httpx**: HTTP client for making API requests
- **python-dotenv**: Loads the API key from `.env`

## Troubleshooting

### Server Not Starting

1. **Check Python version**: Ensure you're using Python 3.10 or higher
   ```bash
   .venv/Scripts/python.exe --version
   ```

2. **Verify dependencies**: Make sure all dependencies are installed
   ```bash
   uv pip install --python .venv/Scripts/python.exe -r requirements.txt
   ```

3. **Check file paths**: Verify the paths in `mcp.json` are correct and use forward slashes

### Tool Not Available in Cursor

1. **Restart Cursor**: Always restart Cursor after changing `mcp.json`
2. **Check logs**: Look for errors in Cursor's MCP logs
3. **Verify server runs**: Test the server manually:
   ```bash
   .venv/Scripts/python.exe server.py
   ```

### Import Errors

If you see import errors, ensure the virtual environment is activated and dependencies are installed:
```bash
.venv/Scripts/activate
pip install -r requirements.txt
```

### Every Query Returns the Same Country

The demo-key fallback is active: `RESTCOUNTRIES_API_KEY` is unset or empty, so the server used the public `rc_live_demo` key, which returns a fixed sample country and ignores the search term. The tool output ends with an explicit warning line in that case. Set a real key in `.env` and restart the client.

### `Error: API key missing, invalid, or revoked` (401)

The key in `.env` is wrong or revoked. Confirm `.env` sits next to `server.py` and that the value starts with `rc_live_`.

### `Error: Rate limited` (429)

The API allows roughly 20 requests per 10 seconds. Wait a moment and retry.

### Wrong Country Returned

`q=` is a substring search, so several countries can match. The tool resolves in priority order — exact common name, exact official name, exact alternate name, then first result — and appends an `Other matches:` line. Re-query with a more specific name from that list.

## API Reference

### REST Countries API

This server uses the [REST Countries API](https://restcountries.com/) v5 to fetch country data.
v5 requires an API key, sent as `Authorization: Bearer <key>` and read from
`RESTCOUNTRIES_API_KEY` in `.env`.

**Base URL:** `https://api.restcountries.com/countries/v5`

**Endpoints used:**
- `GET /name?q={name}` - search common, official, alternate and native names

**Notes:**
- The older `v1`–`v4` endpoints were retired and now return a deprecation notice
  for every request.
- Rate limit is roughly 20 requests per 10 seconds.
- Requests use `response_fields` to fetch only the fields this server formats.

For more information, visit: https://restcountries.com/

## License

This project is open source and available for use and modification.

## Contributing

Feel free to extend this server with additional tools and features. When adding new tools:

1. Follow the existing code style
2. Add clear docstrings
3. Handle errors appropriately
4. Test your changes
5. Update this README if adding significant features

## Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [REST Countries API](https://restcountries.com/)
- [Cursor MCP Integration](https://docs.cursor.com/context/model-context-protocol)
- [Claude Code MCP Integration](https://docs.claude.com/en/docs/claude-code/mcp)
- [PROMPT_USAGE.md](PROMPT_USAGE.md) — prompt and shawarma-tool usage in this repo

