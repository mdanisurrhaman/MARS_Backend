import requests
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from datetime import datetime
import json


class CompanyNewsInput(BaseModel):
    """Input schema for Company News tool."""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL, GOOGL)")
    limit: int = Field(default=5, description="Number of news articles to fetch (max 50)")


class AlphaVantageNewsTool(BaseTool):
    name: str = "Alpha Vantage Company News Tool"
    description: str = (
        "Get the latest news articles for a specific company using Alpha Vantage API. "
        "Returns recent news with titles, summaries, and publication dates."
    )
    args_schema: Type[BaseModel] = CompanyNewsInput
    api_key: str = Field(..., description="Alpha Vantage API key")
    base_url: str = "https://www.alphavantage.co/query"

    def _run(self, symbol: str, limit: int = 5) -> str:
        """Fetch latest news for a company."""
        try:
            # Validate inputs
            symbol = symbol.upper().strip()
            limit = min(max(limit, 1), 50)  # Ensure limit is between 1-50
            
            if not symbol:
                return "Error: Symbol cannot be empty"

            # API parameters
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol,
                'limit': limit,
                'apikey': self.api_key
            }

            # Make API request
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()

            # Check for API errors
            if 'Error Message' in data:
                return f"API Error: {data['Error Message']}"
            
            if 'Note' in data:
                return f"API Limit: {data['Note']}"

            # Extract news articles
            articles = data.get('feed', [])
            
            if not articles:
                return f"No recent news found for {symbol}"

            # Format news output
            result = f"**Latest News for {symbol}:**\n\n"
            
            for i, article in enumerate(articles[:limit], 1):
                title = article.get('title', 'No title available')
                summary = article.get('summary', 'No summary available')
                published = article.get('time_published', 'Unknown date')
                source = article.get('source', 'Unknown source')
                
                # Get sentiment data
                sentiment_score = article.get('overall_sentiment_score', 0)
                sentiment_label = article.get('overall_sentiment_label', 'Neutral')
                
                # Format date if available
                formatted_date = self._format_date(published)
                
                # Truncate summary if too long
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                
                # Format sentiment color/indicator
                sentiment_indicator = self._get_sentiment_indicator(sentiment_label)
                
                result += f"**{i}. {title}**\n"
                result += f"*Source: {source} | Date: {formatted_date}*\n"
                result += f"*Sentiment: {sentiment_indicator} {sentiment_label} ({sentiment_score:.3f})*\n"
                result += f"{summary}\n\n"

            return result.strip()

        except requests.RequestException as e:
            return f"Network error fetching news for {symbol}: {str(e)}"
        except Exception as e:
            return f"Error fetching news for {symbol}: {str(e)}"

    def _format_date(self, date_str: str) -> str:
        """Format the date string from Alpha Vantage format."""
        try:
            if len(date_str) >= 8:
                # Alpha Vantage format: YYYYMMDDTHHMISS
                dt = datetime.strptime(date_str[:8], '%Y%m%d')
                return dt.strftime('%Y-%m-%d')
            return date_str
        except:
            return date_str

    def _get_sentiment_indicator(self, sentiment_label: str) -> str:
        """Get emoji/indicator for sentiment."""
        sentiment_indicators = {
            'Bearish': '🔴',
            'Somewhat-Bearish': '🟠',
            'Neutral': '🟡',
            'Somewhat-Bullish': '🟢',
            'Bullish': '💚'
        }
        return sentiment_indicators.get(sentiment_label, '⚪')


# Factory function to create tool with API key
def create_news_tool(api_key: str) -> AlphaVantageNewsTool:
    """Factory function to create news tool with API key."""
    return AlphaVantageNewsTool(api_key=api_key, base_url="https://www.alphavantage.co/query")



