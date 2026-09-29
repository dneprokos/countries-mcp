"""MCP server for fetching country information from REST Countries API."""
import base64
import json
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP


# Load .env next to this file, regardless of the directory the MCP client
# launches the server from.
load_dotenv(Path(__file__).parent / ".env")

# The old public v3.1 endpoints were retired and now answer every request with a
# deprecation notice, so all calls go to v5, which requires an API key.
API_BASE = "https://api.restcountries.com/countries/v5"

# Public demo key: real data, no account needed, does not consume a quota. Used
# as a fallback so a missing key degrades to "works, with a notice" over a 401.
DEMO_API_KEY = "rc_live_demo"

REQUEST_TIMEOUT = 15.0

# Only request the fields we format. A full record carries 90+ fields.
RESPONSE_FIELDS = ",".join([
    "names.common",
    "names.official",
    "names.native",
    "capitals",
    "region",
    "subregion",
    "population",
    "area",
    "languages",
    "currencies",
    "flag",
    "codes",
])

# Initialize the FastMCP server
mcp = FastMCP("countries-mcp")


def _error_for_status(status_code: int, payload: dict) -> str:
    """Turn a non-200 v5 response into a message worth showing the caller."""
    # v5 reports failures as {"errors": [{"message": ...}, ...]}.
    messages = [
        entry.get("message", "")
        for entry in payload.get("errors", [])
        if isinstance(entry, dict)
    ]
    detail = " ".join(m for m in messages if m)

    hints = {
        400: "Bad request (empty or invalid search term)",
        401: "API key missing, invalid, or revoked - check RESTCOUNTRIES_API_KEY in .env",
        403: "Access denied (account frozen, or a paid-plan-only field was requested)",
        404: "Endpoint not found",
        429: "Rate limited (the API allows about 20 requests per 10 seconds) - retry shortly",
        410: "This API version is no longer active",
    }
    hint = hints.get(status_code, f"HTTP {status_code}")
    return f"Error: {hint}." + (f" API said: {detail}" if detail else "")


def _best_match(countries: list, query: str) -> dict:
    """Pick the closest record. The v5 `q` search is a substring match, so
    'Ukraine' and 'India' can both return several countries."""
    wanted = query.strip().casefold()

    for country in countries:
        names = country.get("names", {})
        if names.get("common", "").casefold() == wanted:
            return country

    for country in countries:
        names = country.get("names", {})
        if names.get("official", "").casefold() == wanted:
            return country

    for country in countries:
        alternates = country.get("names", {}).get("alternates") or []
        if any(alt.casefold() == wanted for alt in alternates):
            return country

    return countries[0]


def _format_country(country: dict) -> list:
    """Render one v5 country record as display lines."""
    names = country.get("names", {})
    flag = country.get("flag", {}) or {}

    heading = names.get("common", "N/A")
    if emoji := flag.get("emoji"):
        heading = f"{heading} {emoji}"

    lines = [
        f"Country: {heading}",
        f"Official Name: {names.get('official', 'N/A')}",
    ]

    # names.native is keyed by ISO 639-3, e.g. {"ukr": {"common": "Україна"}}.
    native_names = []
    for native in (names.get("native") or {}).values():
        if isinstance(native, dict) and (common := native.get("common")):
            if common != names.get("common"):
                native_names.append(common)
    if native_names:
        lines.append(f"Native Name: {', '.join(dict.fromkeys(native_names))}")

    # v5 capitals are objects with a name and coordinates, not plain strings.
    if capitals := country.get("capitals"):
        capital_names = [
            capital.get("name", "") for capital in capitals
            if isinstance(capital, dict) and capital.get("name")
        ]
        if capital_names:
            lines.append(f"Capital: {', '.join(capital_names)}")

    if region := country.get("region"):
        lines.append(f"Region: {region}")

    if subregion := country.get("subregion"):
        lines.append(f"Subregion: {subregion}")

    if (population := country.get("population")) is not None:
        lines.append(f"Population: {population:,}")

    # v5 splits area into kilometers/miles instead of a single number.
    if area := country.get("area"):
        if (km := area.get("kilometers")) is not None:
            lines.append(f"Area: {km:,.2f} km²")

    # v5 languages are a list of objects, not a code-keyed dict.
    if languages := country.get("languages"):
        language_names = [
            language.get("name", "") for language in languages
            if isinstance(language, dict) and language.get("name")
        ]
        if language_names:
            lines.append(f"Languages: {', '.join(language_names)}")

    # v5 currencies are a list of objects carrying their own code.
    if currencies := country.get("currencies"):
        currency_parts = []
        for currency in currencies:
            if not isinstance(currency, dict):
                continue
            label = currency.get("code", "")
            details = ", ".join(
                part for part in (currency.get("name"), currency.get("symbol")) if part
            )
            currency_parts.append(f"{label} ({details})" if details else label)
        if currency_parts:
            lines.append(f"Currencies: {', '.join(currency_parts)}")

    if codes := country.get("codes"):
        code_parts = [
            code for code in (codes.get("alpha_2"), codes.get("alpha_3")) if code
        ]
        if code_parts:
            lines.append(f"Country Codes: {' / '.join(code_parts)}")

    if png_flag := flag.get("url_png"):
        lines.append(f"Flag: {png_flag}")

    return lines


@mcp.tool()
def get_country_info(country_name: str) -> str:
    """Get detailed information about a country by its name.

    Args:
        country_name: The name of the country to get information about (e.g., 'Ukraine', 'United States')

    Returns:
        A formatted string containing country information including name, capital, region,
        population, area, languages, currencies, and flag.
    """
    if not country_name or not country_name.strip():
        return "Error: country_name parameter is required"

    api_key = os.getenv("RESTCOUNTRIES_API_KEY", "").strip() or DEMO_API_KEY

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            response = client.get(
                # The `name` aggregate searches common, official, alternate and
                # native names in one call.
                f"{API_BASE}/name",
                params={
                    "q": country_name.strip(),
                    "response_fields": RESPONSE_FIELDS,
                },
                headers={"Authorization": f"Bearer {api_key}"},
            )

            try:
                payload = response.json()
            except ValueError:
                return f"Error: Unexpected non-JSON response (HTTP {response.status_code})"

            if response.status_code != 200:
                return _error_for_status(response.status_code, payload)

            data = payload.get("data", {})
            countries = data.get("objects", [])

            if not countries:
                return f"Error: Country '{country_name}' not found"

            country = _best_match(countries, country_name)
            info_parts = _format_country(country)

            # Substring search can match several countries; name the rest so the
            # caller can re-query instead of silently trusting the top hit.
            if len(countries) > 1:
                others = [
                    other.get("names", {}).get("common", "")
                    for other in countries
                    if other is not country
                ]
                others = [name for name in others if name]
                if others:
                    shown = ", ".join(others[:9])
                    suffix = ", ..." if len(others) > 9 else ""
                    info_parts.append(f"\nOther matches: {shown}{suffix}")

            if api_key == DEMO_API_KEY:
                info_parts.append(
                    "\nWarning: no RESTCOUNTRIES_API_KEY is set, so this used the public demo key, "
                    "which returns a fixed sample country and ignores the search term. "
                    "Set RESTCOUNTRIES_API_KEY in .env to get real results.")

            return "\n".join(info_parts)

    except httpx.HTTPError as e:
        return f"Error fetching country data: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@mcp.tool()
def shawarma_with_or_without_potatoes() -> str:
    """Відповідає на питання: яка шаурма краще — з картоплею чи без?

    Однозначна відповідь з фото кебабу. Викликай цей тул, коли хтось питає про шаурму з картоплею чи без.

    Returns:
        Відповідь "з картоплею краща" та шлях до фото кебабу (зображення в папці images).
    """
    image_path = Path(__file__).parent / "images" / "kebab.png"
    answer = (
        "🍟 **З картоплею краща!** Однозначно.\n\n"
        "Шаурма з картоплею фри — це класика: хрустка картопля, соковите м’ясо, свіжі овочі. "
        "Без картоплі шаурма теж смачна, але з картоплею вона повніша і задовольняє краще.\n\n"
    )
    if image_path.exists():
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            answer += f'\n![kebab](data:image/png;base64,{b64})\n\n*Фото: {image_path}*'
        except Exception:
            answer += f"\n*Фото кебабу: {image_path}*"
    else:
        answer += f"\n*Фото кебабу (файл не знайдено): {image_path}*"
    return answer


@mcp.resource("countries://country-codes")
def get_country_codes() -> str:
    """Get a list of country codes and names.

    This resource provides a JSON file with common country codes
    that can be used as a reference when working with country data.
    """
    try:
        data_file = Path(__file__).parent / "data" / "country_codes.json"

        if not data_file.exists():
            return json.dumps({"error": "Country codes file not found"}, indent=2)

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to load country codes: {str(e)}"}, indent=2)


@mcp.prompt()
def compare_countries_prompt(country1: str, country2: str) -> str:
    """Generate a prompt template for comparing two countries.

    This prompt helps guide the AI to compare two countries by fetching their information
    and highlighting key differences and similarities.

    Args:
        country1: The name of the first country to compare
        country2: The name of the second country to compare

    Returns:
        A formatted prompt string that guides country comparison
    """
    return f"""Compare the following two countries: {country1} and {country2}.

Please:
1. Fetch detailed information for both countries using the get_country_info tool
2. Compare their key attributes:
   - Population and area
   - Capital cities
   - Languages spoken
   - Currencies used
   - Geographic regions
3. Highlight the main differences and similarities
4. Provide a summary of the comparison"""


@mcp.prompt()
def country_research_prompt(country_name: str, focus_areas: str = "all") -> str:
    """Generate a prompt template for researching a country with specific focus areas.

    This prompt helps guide comprehensive country research with optional focus on
    specific aspects like geography, economy, culture, etc.

    Args:
        country_name: The name of the country to research
        focus_areas: Comma-separated list of focus areas (e.g., "geography,population,currency")
                    or "all" for comprehensive information

    Returns:
        A formatted prompt string that guides country research
    """
    focus_text = "all aspects" if focus_areas.lower(
    ) == "all" else f"the following areas: {focus_areas}"

    return f"""Research {country_name} with a focus on {focus_text}.

Please:
1. Access the country codes resource to verify the country name
2. Fetch detailed information using the get_country_info tool
3. Provide comprehensive information about {country_name}
4. If specific focus areas were requested, provide extra detail on those topics
5. Format the information in a clear, organized manner"""

# Fields for neighbor records returned by /borders/{code}.
BORDER_FIELDS = ",".join([
    "names.common",
    "capitals",
    "population",
    "flag",
    "codes",
])


@mcp.tool()
def get_country_borders(country_name: str) -> str:
    """Get the countries that share a land border with the given country.

    Args:
        country_name: The name of the country to look up (e.g., 'Ukraine', 'Canada')

    Returns:
        A formatted list of neighboring countries with their capital, population and
        flag, or a note that the country has no land borders.
    """
    if not country_name or not country_name.strip():
        return "Error: country_name parameter is required"

    api_key = os.getenv("RESTCOUNTRIES_API_KEY", "").strip() or DEMO_API_KEY
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            # /borders needs an alpha-3 code, and answers an unknown code with an
            # empty list, so resolve the name first to tell "island" from "typo".
            lookup = client.get(
                f"{API_BASE}/name",
                params={"q": country_name.strip(), "response_fields": "names,codes,flag"},
                headers=headers,
            )
            try:
                lookup_payload = lookup.json()
            except ValueError:
                return f"Error: Unexpected non-JSON response (HTTP {lookup.status_code})"

            if lookup.status_code != 200:
                return _error_for_status(lookup.status_code, lookup_payload)

            matches = lookup_payload.get("data", {}).get("objects", [])
            if not matches:
                return f"Error: Country '{country_name}' not found"

            country = _best_match(matches, country_name)
            name = country.get("names", {}).get("common", country_name)
            alpha_3 = (country.get("codes") or {}).get("alpha_3")
            if not alpha_3:
                return f"Error: No country code available for '{name}'"

            response = client.get(
                f"{API_BASE}/borders/{alpha_3}",
                params={"response_fields": BORDER_FIELDS},
                headers=headers,
            )
            try:
                payload = response.json()
            except ValueError:
                return f"Error: Unexpected non-JSON response (HTTP {response.status_code})"

            if response.status_code != 200:
                return _error_for_status(response.status_code, payload)

            neighbors = payload.get("data", {}).get("objects", [])

    except httpx.HTTPError as e:
        return f"Error fetching country data: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

    emoji = (country.get("flag") or {}).get("emoji", "")
    heading = f"{name} {emoji}".strip()

    if not neighbors:
        return f"{heading} has no land borders."

    noun = "country" if len(neighbors) == 1 else "countries"
    lines = [f"{heading} borders {len(neighbors)} {noun}:"]
    for neighbor in sorted(neighbors, key=lambda n: n.get("names", {}).get("common", "")):
        neighbor_name = neighbor.get("names", {}).get("common", "N/A")
        neighbor_emoji = (neighbor.get("flag") or {}).get("emoji", "")
        details = []
        capitals = [
            capital.get("name") for capital in neighbor.get("capitals") or []
            if isinstance(capital, dict) and capital.get("name")
        ]
        if capitals:
            details.append(f"capital {', '.join(capitals)}")
        if (population := neighbor.get("population")) is not None:
            details.append(f"population {population:,}")
        suffix = f" ({'; '.join(details)})" if details else ""
        label = " ".join(part for part in (neighbor_emoji, neighbor_name) if part)
        lines.append(f"- {label}{suffix}")

    if api_key == DEMO_API_KEY:
        lines.append(
            "\nWarning: no RESTCOUNTRIES_API_KEY is set, so this used the public demo key, "
            "which returns a fixed sample country and ignores the search term. "
            "Set RESTCOUNTRIES_API_KEY in .env to get real results.")

    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run()
