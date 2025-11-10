# src/new_decision_support/tools/ticker_lookup_tool.py
# This file defines a tool for looking up ticker symbols for company names.

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any, Optional
import yfinance as yf
import requests
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def search_yahoo_ticker(query: str) -> Optional[str]:
    """Search for ticker symbol using Yahoo Finance API"""
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": query, "quotes_count": 1}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if data.get("quotes"):
            return data["quotes"][0]["symbol"]
    except Exception as e:
        logger.error(f"Yahoo search error for '{query}': {e}")
    return None


class TickerLookupInput(BaseModel):
    """Input schema for Ticker Lookup tool."""
    query: str = Field(
        ..., 
        description="Company names separated by commas (e.g., 'Apple Inc, Microsoft Corporation')"
    )

class TickerLookupTool(BaseTool):
    """CrewAI tool for finding ticker symbols for company names."""
    
    name: str = "ticker_lookup"
    description: str = "Finds best matching ticker symbols for given company names. Input should be company names separated by commas."
    args_schema: Type[BaseModel] = TickerLookupInput

    def _run(self, query: str, **kwargs: Any) -> str:
        """Execute the ticker lookup for given company names."""
        names = [name.strip() for name in query.split(",")]
        
        # Step 1: Validate input
        if not names or not any(name for name in names):
            return "Error: Please provide at least one company name."
        
        # Step 2: Resolve tickers
        results = []
        invalid_names = []
        
        for name in names:
            if not name:  # Skip empty names
                continue
                
            try:
                ticker_found = False
                
                # Try yfinance search first
                try:
                    search = yf.Search(name, max_results=1)
                    if hasattr(search, 'quotes') and search.quotes:
                        ticker = search.quotes[0]["symbol"]
                        results.append(f"{name}: {ticker}")
                        ticker_found = True
                        logger.info(f"Found ticker for '{name}': {ticker}")
                except Exception as yf_error:
                    logger.warning(f"yfinance search failed for '{name}': {yf_error}")

                # Fallback to Yahoo search if yfinance failed
                if not ticker_found:
                    ticker = search_yahoo_ticker(name)
                    if ticker:
                        results.append(f"{name}: {ticker}")
                        ticker_found = True
                        logger.info(f"Found ticker via Yahoo for '{name}': {ticker}")

                # If no ticker found
                if not ticker_found:
                    logger.warning(f"No ticker found for '{name}'. Skipping...")
                    invalid_names.append(name)
                    
            except Exception as e:
                logger.error(f"Error finding ticker for '{name}': {str(e)}")
                invalid_names.append(name)

        # Step 3: Format results
        result_parts = []
        
        if results:
            result_parts.append("Found tickers:")
            result_parts.extend(results)
        
        if invalid_names:
            result_parts.append(f"Could not find tickers for: {', '.join(invalid_names)}")
        
        if not results and not invalid_names:
            return "No valid company names provided."
        
        return "\n".join(result_parts)

ticker_lookup = TickerLookupTool()
