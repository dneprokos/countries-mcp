"""MCP server for fetching country information from REST Countries API."""
import json
import httpx
from pathlib import Path
from fastmcp import FastMCP


# Initialize the FastMCP server
mcp = FastMCP("countries-mcp")


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


@mcp.tool()
def get_country_info(country_name: str) -> str:
    """Get detailed information about a country by its name.
    
    Args:
        country_name: The name of the country to get information about (e.g., 'Ukraine', 'United States')
    
    Returns:
        A formatted string containing country information including name, capital, region, 
        population, area, languages, currencies, and flag.
    """
    if not country_name:
        return "Error: country_name parameter is required"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"https://restcountries.com/v3.1/name/{country_name}"
            )
            
            if response.status_code == 404:
                return f"Error: Country '{country_name}' not found"
            
            response.raise_for_status()
            countries = response.json()
            
            if not countries:
                return f"Error: No data found for country '{country_name}'"
            
            country = countries[0]
            
            # Format the response
            info_parts = [
                f"Country: {country.get('name', {}).get('common', 'N/A')}",
                f"Official Name: {country.get('name', {}).get('official', 'N/A')}",
            ]
            
            if capital := country.get('capital'):
                info_parts.append(f"Capital: {', '.join(capital) if isinstance(capital, list) else capital}")
            
            if region := country.get('region'):
                info_parts.append(f"Region: {region}")
            
            if subregion := country.get('subregion'):
                info_parts.append(f"Subregion: {subregion}")
            
            if population := country.get('population'):
                info_parts.append(f"Population: {population:,}")
            
            if area := country.get('area'):
                info_parts.append(f"Area: {area:,.2f} km²")
            
            if languages := country.get('languages'):
                lang_list = ', '.join(languages.values()) if isinstance(languages, dict) else str(languages)
                info_parts.append(f"Languages: {lang_list}")
            
            if currencies := country.get('currencies'):
                currency_list = []
                for code, details in currencies.items():
                    if isinstance(details, dict):
                        currency_list.append(f"{code} ({details.get('name', '')})")
                    else:
                        currency_list.append(code)
                info_parts.append(f"Currencies: {', '.join(currency_list)}")
            
            if flags := country.get('flags'):
                if png_flag := flags.get('png'):
                    info_parts.append(f"Flag: {png_flag}")
            
            return "\n".join(info_parts)
            
    except httpx.HTTPError as e:
        return f"Error fetching country data: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


if __name__ == "__main__":
    mcp.run()
