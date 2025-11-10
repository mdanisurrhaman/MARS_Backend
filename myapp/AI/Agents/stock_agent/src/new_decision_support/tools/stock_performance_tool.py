import yfinance as yf
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class CompanyResearchInput(BaseModel):
    """Input schema for Company Research tool."""
    symbol: str = Field(..., description="Stock symbol of the company (e.g., AAPL, GOOGL, MSFT)")


class CompanyResearchTool(BaseTool):
    name: str = "Company Research Tool"
    description: str = (
        "Get comprehensive company information including name, sector, industry, market cap, "
        "current price, financial metrics, business summary, and stock performance. "
        "Perfect for detailed company analysis and investment research."
    )
    args_schema: Type[BaseModel] = CompanyResearchInput

    def _run(self, symbol: str) -> str:
        """Get comprehensive company information and stock performance."""
        try:
            # Validate and clean symbol
            symbol = symbol.upper().strip()
            if not symbol:
                return "Error: Symbol cannot be empty"

            # Get ticker data
            stock = yf.Ticker(symbol)
            info = stock.info

            if not info:
                return f"No company info found for symbol: {symbol}"

            # Extract basic company information
            name = info.get("longName", "N/A")
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")
            market_cap = info.get("marketCap", "N/A")
            summary = info.get("longBusinessSummary", "N/A")
            
            # Extract financial metrics
            current_price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
            pe_ratio = info.get("trailingPE", "N/A")
            dividend_yield = info.get("dividendYield", "N/A")
            revenue = info.get("totalRevenue", "N/A")
            employees = info.get("fullTimeEmployees", "N/A")
            website = info.get("website", "N/A")

            # Format values for better readability
            formatted_market_cap = self._format_large_number(market_cap)
            formatted_revenue = self._format_large_number(revenue)
            formatted_dividend = self._format_percentage(dividend_yield)
            formatted_employees = self._format_number(employees)
            
            # Truncate summary if too long
            if isinstance(summary, str) and len(summary) > 600:
                summary = summary[:600] + "..."

            # Get stock performance
            performance_info = self._get_stock_performance(symbol)

            # Format the complete output
            result = f"""**Company Name:** {name}
**Sector:** {sector}
**Industry:** {industry}
**Website:** {website}
**Market Cap:** {formatted_market_cap}
**Current Price:** ${current_price}
**P/E Ratio:** {pe_ratio}
**Dividend Yield:** {formatted_dividend}
**Annual Revenue:** {formatted_revenue}
**Employees:** {formatted_employees}

**Business Summary:** {summary}

{performance_info}"""

            return result

        except Exception as e:
            return f"Error retrieving info for {symbol}: {str(e)}"

    def _get_stock_performance(self, symbol: str) -> str:
        """Get stock performance over 6 months."""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="6mo")
            
            if hist.empty:
                return "**6-Month Stock Performance:** Data not available"
            
            start_price = hist['Close'].iloc[0]
            current_price = hist['Close'].iloc[-1]
            performance = ((current_price - start_price) / start_price) * 100
            
            return f"**6-Month Stock Performance:** {performance:+.2f}%"
        
        except Exception as e:
            return f"**6-Month Stock Performance:** Error calculating - {str(e)}"

    def _format_large_number(self, value):
        """Format large numbers for better readability."""
        if isinstance(value, (int, float)) and value > 0:
            if value >= 1e12:
                return f"${value/1e12:.2f}T"
            elif value >= 1e9:
                return f"${value/1e9:.2f}B"
            elif value >= 1e6:
                return f"${value/1e6:.2f}M"
            else:
                return f"${value:,.0f}"
        return "N/A"
    
    def _format_percentage(self, value):
        """Format percentage values."""
        if isinstance(value, (int, float)):
            return f"{value*100:.2f}%"
        return "N/A"
    
    def _format_number(self, value):
        """Format regular numbers with commas."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return "N/A"


# Create tool instance for import
company_research_tool = CompanyResearchTool()


# Alternative: Stock Performance Tool (separate tool if needed)
class StockPerformanceInput(BaseModel):
    """Input schema for Stock Performance tool."""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL, GOOGL)")
    period: str = Field(default="6mo", description="Time period (1mo, 3mo, 6mo, 1y, 2y, 5y)")


class StockPerformanceTool(BaseTool):
    name: str = "Stock Performance Tool"
    description: str = (
        "Get detailed stock performance analysis over specified time periods. "
        "Returns percentage change, price trends, and performance metrics."
    )
    args_schema: Type[BaseModel] = StockPerformanceInput

    def _run(self, symbol: str, period: str = "6mo") -> str:
        """Get stock performance analysis."""
        try:
            symbol = symbol.upper().strip()
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            
            if hist.empty:
                return f"No stock data available for {symbol} over {period}"
            
            start_price = hist['Close'].iloc[0]
            current_price = hist['Close'].iloc[-1]
            high_price = hist['High'].max()
            low_price = hist['Low'].min()
            
            performance = ((current_price - start_price) / start_price) * 100
            high_change = ((high_price - start_price) / start_price) * 100
            low_change = ((low_price - start_price) / start_price) * 100
            
            result = f"""**Stock Performance Analysis for {symbol} ({period.upper()})**
**Start Price:** ${start_price:.2f}
**Current Price:** ${current_price:.2f}
**Performance:** {performance:+.2f}%
**Highest Price:** ${high_price:.2f} ({high_change:+.2f}%)
**Lowest Price:** ${low_price:.2f} ({low_change:+.2f}%)"""
            
            return result
            
        except Exception as e:
            return f"Error analyzing performance for {symbol}: {str(e)}"


# Create performance tool instance
stock_performance_tool = StockPerformanceTool()


# Basic Company Info Tool (lightweight version)
class BasicCompanyInfoInput(BaseModel):
    """Input schema for Basic Company Info tool."""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL, GOOGL)")


class BasicCompanyInfoTool(BaseTool):
    name: str = "Basic Company Info Tool"
    description: str = (
        "Get essential company information including name, sector, current price, "
        "and market cap. Lightweight version for quick company lookups."
    )
    args_schema: Type[BaseModel] = BasicCompanyInfoInput

    def _run(self, symbol: str) -> str:
        """Get basic company information."""
        try:
            symbol = symbol.upper().strip()
            stock = yf.Ticker(symbol)
            info = stock.info

            if not info:
                return f"No company info found for symbol: {symbol}"

            name = info.get("longName", "N/A")
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")
            current_price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
            market_cap = info.get("marketCap", "N/A")
            
            formatted_market_cap = self._format_large_number(market_cap)
            
            result = f"""**{name}** ({symbol})
**Sector:** {sector} | **Industry:** {industry}
**Current Price:** ${current_price}
**Market Cap:** {formatted_market_cap}"""
            
            return result

        except Exception as e:
            return f"Error retrieving basic info for {symbol}: {str(e)}"

    def _format_large_number(self, value):
        """Format large numbers for better readability."""
        if isinstance(value, (int, float)) and value > 0:
            if value >= 1e12:
                return f"${value/1e12:.2f}T"
            elif value >= 1e9:
                return f"${value/1e9:.2f}B"
            elif value >= 1e6:
                return f"${value/1e6:.2f}M"
            else:
                return f"${value:,.0f}"
        return "N/A"


# Create basic info tool instance
basic_company_info_tool = BasicCompanyInfoTool()










