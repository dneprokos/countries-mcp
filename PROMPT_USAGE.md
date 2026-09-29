# How to Use MCP Prompts

This guide explains how to use the prompts available in the Countries MCP Server.

## Understanding MCP Prompts

MCP prompts are reusable templates that provide structured instructions to AI agents. They help guide the AI to perform specific tasks in a consistent, organized manner.

## Available Prompts

### 1. Compare Countries Prompt (`compare_countries_prompt`)

**Purpose:** Systematically compare two countries across multiple dimensions.

**Parameters:**
- `country1` (required): Name of the first country
- `country2` (required): Name of the second country

**How to Use in Cursor:**

**Method 1: Direct Request**
```
Use the compare countries prompt to compare Ukraine and Poland
```

**Method 2: Natural Language**
```
Compare France and Germany using the comparison prompt
```

**Method 3: Explicit Invocation**
```
Run compare_countries_prompt with country1="United States" and country2="Canada"
```

**What Happens:**
1. The prompt template is invoked with your country names
2. The AI receives structured instructions to:
   - Fetch information for both countries using `get_country_info`
   - Compare population, area, capitals, languages, currencies, and regions
   - Highlight differences and similarities
   - Provide a summary

**Example Output Structure:**
```
Comparison: Ukraine vs Poland

Population:
- Ukraine: 41,167,336
- Poland: 37,846,611

Capital Cities:
- Ukraine: Kyiv
- Poland: Warsaw

Languages:
- Ukraine: Ukrainian
- Poland: Polish

[Additional comparisons...]

Summary: [Key differences and similarities]
```

### 2. Country Research Prompt (`country_research_prompt`)

**Purpose:** Conduct comprehensive research on a country with optional focus areas.

**Parameters:**
- `country_name` (required): Name of the country to research
- `focus_areas` (optional): Comma-separated focus areas or "all" (default)

**How to Use in Cursor:**

**Basic Research:**
```
Use the country research prompt for Japan
```

**Focused Research:**
```
Research Germany using the research prompt, focusing on population and currency
```

**With Specific Focus Areas:**
```
Use country_research_prompt for Brazil with focus_areas="geography,population,languages"
```

**What Happens:**
1. The prompt template is invoked with your parameters
2. The AI receives instructions to:
   - Access the country codes resource to verify the country name
   - Fetch detailed information using `get_country_info`
   - Provide comprehensive information
   - Add extra detail on requested focus areas
   - Format information clearly

## Programmatic Usage

If you're building an MCP client, you can invoke prompts programmatically:

```python
# Example: Using the MCP SDK to invoke a prompt
from mcp import ClientSession, StdioServerParameters

async with ClientSession(StdioServerParameters(...)) as session:
    result = await session.get_prompt(
        name="compare_countries_prompt",
        arguments={
            "country1": "Ukraine",
            "country2": "Poland"
        }
    )
    print(result.messages[0].content.text)
```

## Tips for Best Results

1. **Use Full Country Names:** Always use complete, official country names (e.g., "United States" not "US")

2. **Be Specific:** When using focus areas, be clear about what you want:
   - Good: "focusing on population,currency,area"
   - Avoid: "focusing on stuff"

3. **Natural Language Works:** You don't need to use exact function names - natural language requests work:
   - ✅ "Compare Ukraine and Poland"
   - ✅ "Use the comparison prompt for France and Germany"

4. **Combine with Resources:** Prompts automatically use available tools and resources, so you don't need to manually fetch data first.

## Troubleshooting

**Prompt Not Found:**
- Ensure the MCP server is properly configured in Cursor
- Restart Cursor after adding new prompts
- Check that the server is running without errors

**Prompt Not Working:**
- Verify country names are spelled correctly
- Use the country codes resource to check available countries
- Try using the `get_country_info` tool directly first to verify connectivity

**Unexpected Results:**
- Prompts guide the AI but don't guarantee exact output format
- The AI may interpret instructions slightly differently each time
- For consistent results, use tools directly instead of prompts

### 3. Shawarma Tool (`shawarma_with_or_without_potatoes`) — жартівливий тул

**Purpose:** Однозначно відповідає: яка шаурма краща — з картоплею чи без (з картоплею краща) і показує фото кебабу.

**Parameters:** None.

**Important for AI/Agent:** When the user asks about shawarma with or without potatoes (in any language), you **must** call the MCP tool `shawarma_with_or_without_potatoes` from server `user-countries-mcp`. Do not answer from general knowledge — the tool returns the canonical answer and the kebab image. Use `call_mcp_tool` with `server: "user-countries-mcp"`, `toolName: "shawarma_with_or_without_potatoes"`, and empty or no arguments.

**How to Use in Cursor:**

Just ask in natural language. Examples:

```
Яка шаурма краще — з картоплею чи без?
```

```
Which shawarma is better, with potatoes or without?
```

```
Шаурма з картоплею чи без — що краще?
```

**What Happens:** The AI calls the tool and you get the answer "з картоплею краща!" plus the kebab image from `images/kebab.png`.

### 4. Country Borders Tool (`get_country_borders`)

**Purpose:** List the countries that share a land border with the given country, each with capital, population and flag emoji.

**Parameters:**
- `country_name` (required): Name of the country (e.g. `Ukraine`, `Canada`)

**How to Use in Cursor:**

```
Which countries border Poland?
```

**What Happens:** The tool looks up the country's alpha-3 code, then calls `/borders/{code}`. Island nations return "has no land borders". Useful alongside `compare_countries_prompt` or `country_research_prompt` for geography context.

---

## Differences: Prompts vs Tools

| Feature | Prompts | Tools |
|---------|---------|-------|
| Purpose | Guide AI behavior | Execute specific actions |
| Output | Instructions/templates | Direct results |
| Flexibility | High (AI interprets) | Low (deterministic) |
| Use Case | Structured workflows | Direct data fetching |
| Parameters | Template variables | Function arguments |

**When to Use Prompts:**
- You want structured, multi-step analysis
- You need consistent workflow guidance
- You want the AI to perform complex reasoning

**When to Use Tools:**
- You need direct, immediate results
- You want deterministic output
- You're building automated workflows
