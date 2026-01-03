# Countries MCP Server

A Model Context Protocol (MCP) server built with FastMCP that provides country information from the REST Countries API. This server exposes tools that can be used within Cursor IDE and other MCP-compatible applications.

## Features

- **Get Country Information**: Retrieve detailed information about any country by name
  - Country name (common and official)
  - Capital city
  - Region and subregion
  - Population
  - Area
  - Languages
  - Currencies
  - Flag image URL

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
   uv pip install --python .venv/Scripts/python.exe fastmcp httpx
   ```

   Or if you prefer using the requirements file:
   ```bash
   uv pip install --python .venv/Scripts/python.exe -r requirements.txt
   ```

## Configuration in Cursor

### Step 1: Locate Your MCP Configuration File

The MCP configuration file is located at:
- **Windows**: `C:\Users\<YourUsername>\.cursor\mcp.json`
- **macOS/Linux**: `~/.cursor/mcp.json`

### Step 2: Add the Server Configuration

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

### Step 3: Restart Cursor

After saving `mcp.json`, restart Cursor IDE completely for the changes to take effect.

### Step 4: Verify Installation

After restarting, you can verify the server is working by asking in Cursor's chat:
- "Get information about Ukraine"
- "What's the capital of France?"

If the server is configured correctly, Cursor will use the tool to fetch country information.

## Usage

Once configured, you can use the country information tool in Cursor's chat interface:

### Example Prompts

- "Get information about Ukraine"
- "What are the details for the United States?"
- "Show me country information for Japan"
- "Get country info for Brazil"
- "What's the capital of France?"

The AI will automatically detect your request and use the `get_country_info` tool to fetch the information.

## Project Structure

```
countries-mcp/
├── server.py              # Main MCP server implementation
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
├── .venv/                # Virtual environment (created during setup)
└── README.md            # This file
```

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
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"https://restcountries.com/v3.1/alpha/{country_code}"
            )
            response.raise_for_status()
            country = response.json()
            # Format and return country information
            return f"Country: {country.get('name', {}).get('common', 'N/A')}"
    except httpx.HTTPError as e:
        return f"Error: {str(e)}"
```

3. **Restart the server** - After adding new tools, restart Cursor for the changes to take effect.

### Best Practices for Extending

- **Use type hints**: FastMCP uses type hints to generate tool schemas automatically
- **Write clear docstrings**: The docstring becomes the tool description in MCP
- **Handle errors gracefully**: Return user-friendly error messages
- **Follow the existing pattern**: Keep code style consistent with existing tools
- **Test your tools**: Verify new tools work before committing

## Dependencies

- **fastmcp**: FastMCP framework for building MCP servers
- **httpx**: HTTP client for making API requests

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

## API Reference

### REST Countries API

This server uses the [REST Countries API](https://restcountries.com/) to fetch country data. The API is free and doesn't require authentication.

**Endpoints used:**
- `GET /v3.1/name/{name}` - Get country by name

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

