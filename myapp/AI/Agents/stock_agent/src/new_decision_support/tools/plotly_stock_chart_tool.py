import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import pandas as pd
from datetime import datetime
import os


class LinePlotInput(BaseModel):
    """Input schema for Stock Line Plot tool."""
    symbols: str = Field(..., description="Comma-separated stock symbols (e.g., 'AAPL,MSFT,GOOGL')")
    period: str = Field(default="6mo", description="Time period (1mo, 3mo, 6mo, 1y, 2y, 5y)")


class StockLinePlotTool(BaseTool):
    name: str = "Stock Line Plot Tool"
    description: str = (
        "Create attractive combined line plot chart with dark theme and neon colors for stock price analysis. "
        "Shows all stocks on one chart with MA20 and MA50 moving averages with lightning neon effects."
    )
    args_schema: Type[BaseModel] = LinePlotInput

    def _run(self, symbols: str, period: str = "6mo") -> str:
        """Create combined line plot chart with dark theme and neon colors."""
        try:
            # Parse symbols
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            if not symbol_list:
                return "Error: No symbols provided"

            # Validate period
            valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
            if period not in valid_periods:
                period = "6mo"

            # Create folder for charts
            folder_name = f"stock_line_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            return self._create_combined_neon_chart(symbol_list, period, folder_name)

        except Exception as e:
            return f"Error creating line plot charts: {str(e)}"

    def _create_combined_neon_chart(self, symbol_list: list, period: str, folder_name: str) -> str:
        """Create a combined neon-themed line chart with all stocks and moving averages."""
        try:
            fig = go.Figure()
            
            # Neon color palette for lightning effect
            neon_colors = [
                '#00FFFF',  # Cyan lightning
                '#FF1493',  # Deep pink lightning  
                '#00FF00',  # Lime lightning
                '#FF4500',  # Orange red lightning
                '#9370DB',  # Medium purple lightning
                '#FFD700',  # Gold lightning
                '#FF69B4',  # Hot pink lightning
                '#32CD32'   # Lime green lightning
            ]
            
            # MA colors for neon effect
            ma20_color = '#FFFF00'  # Yellow neon
            ma50_color = '#FF6600'  # Orange neon
            
            successful_symbols = []
            all_ma20_data = []
            all_ma50_data = []
            
            for i, symbol in enumerate(symbol_list):
                try:
                    # Get stock data
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period=period)
                    
                    # Skip if no data
                    if hist.empty:
                        continue

                    # Get company info
                    try:
                        info = stock.info
                        company_name = info.get('longName', symbol)
                        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
                    except:
                        company_name = symbol
                        current_price = hist['Close'].iloc[-1]

                    # Calculate performance
                    start_price = hist['Close'].iloc[0]
                    performance = ((current_price - start_price) / start_price) * 100

                    # Add main stock line with neon glow effect
                    neon_color = neon_colors[i % len(neon_colors)]
                    fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=hist['Close'],
                        mode='lines',
                        name=f'{symbol} (${current_price:.2f}) {performance:+.1f}%',
                        line=dict(
                            color=neon_color, 
                            width=3,
                            # Add glow effect with shadow
                        ),
                        # Add glow effect by adding multiple traces with decreasing opacity
                        hovertemplate=f'<b>{symbol}</b><br>' +
                                    'Date: %{x}<br>' +
                                    'Price: $%{y:.2f}<br>' +
                                    f'Performance: {performance:+.2f}%<br>' +
                                    '<extra></extra>'
                    ))
                    
                    # Add subtle glow effect
                    fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=hist['Close'],
                        mode='lines',
                        line=dict(color=neon_color, width=6),
                        opacity=0.3,
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=hist.index,
                        y=hist['Close'],
                        mode='lines',
                        line=dict(color=neon_color, width=10),
                        opacity=0.1,
                        showlegend=False,
                        hoverinfo='skip'
                    ))

                    # Calculate moving averages
                    if len(hist) >= 20:
                        ma20 = hist['Close'].rolling(window=20).mean()
                        all_ma20_data.append({'symbol': symbol, 'dates': hist.index, 'ma20': ma20})
                    
                    if len(hist) >= 50:
                        ma50 = hist['Close'].rolling(window=50).mean()
                        all_ma50_data.append({'symbol': symbol, 'dates': hist.index, 'ma50': ma50})
                    
                    successful_symbols.append(symbol)
                    
                except Exception as e:
                    print(f"Error processing {symbol}: {str(e)}")
                    continue

            if not successful_symbols:
                return "❌ No valid stock data found for the provided symbols."

            # Add MA20 for all stocks
            if all_ma20_data:
                for ma_data in all_ma20_data:
                    fig.add_trace(go.Scatter(
                        x=ma_data['dates'],
                        y=ma_data['ma20'],
                        mode='lines',
                        name=f'{ma_data["symbol"]} MA20',
                        line=dict(color=ma20_color, width=1.5, dash='dot'),
                        opacity=0.8,
                        hovertemplate=f'<b>{ma_data["symbol"]} MA20</b><br>' +
                                    'Date: %{x}<br>' +
                                    'MA20: $%{y:.2f}<br>' +
                                    '<extra></extra>'
                    ))
                    
                    # Add glow for MA20
                    fig.add_trace(go.Scatter(
                        x=ma_data['dates'],
                        y=ma_data['ma20'],
                        mode='lines',
                        line=dict(color=ma20_color, width=4, dash='dot'),
                        opacity=0.2,
                        showlegend=False,
                        hoverinfo='skip'
                    ))

            # Add MA50 for all stocks  
            if all_ma50_data:
                for ma_data in all_ma50_data:
                    fig.add_trace(go.Scatter(
                        x=ma_data['dates'],
                        y=ma_data['ma50'],
                        mode='lines',
                        name=f'{ma_data["symbol"]} MA50',
                        line=dict(color=ma50_color, width=1.5, dash='dash'),
                        opacity=0.8,
                        hovertemplate=f'<b>{ma_data["symbol"]} MA50</b><br>' +
                                    'Date: %{x}<br>' +
                                    'MA50: $%{y:.2f}<br>' +
                                    '<extra></extra>'
                    ))
                    
                    # Add glow for MA50
                    fig.add_trace(go.Scatter(
                        x=ma_data['dates'],
                        y=ma_data['ma50'],
                        mode='lines',
                        line=dict(color=ma50_color, width=4, dash='dash'),
                        opacity=0.2,
                        showlegend=False,
                        hoverinfo='skip'
                    ))

            # Calculate date range for title
            sample_stock = yf.Ticker(successful_symbols[0])
            sample_hist = sample_stock.history(period=period)
            start_date = sample_hist.index[0].strftime('%Y-%m-%d')
            end_date = sample_hist.index[-1].strftime('%Y-%m-%d')

            # Update layout with neon dark theme
            fig.update_layout(
                title=dict(
                    text=f"<b> STOCK LINE CHART </b><br>"
                         f"<span style='font-size:16px; color:#00FFFF'>{', '.join(successful_symbols)} | "
                         f"Period: {period.upper()} | {start_date} → {end_date}</span>",
                    x=0.5,
                    font=dict(size=24, color='#FFFFFF')
                ),
                
                # Dark neon theme colors
                paper_bgcolor='#000000',  # Pure black background
                plot_bgcolor='#0a0a0a',   # Dark gray plot area
                
                # Neon grid and axes
                xaxis=dict(
                    gridcolor='#1a1a1a',
                    gridwidth=1,
                    color='#00FFFF',
                    showgrid=True,
                    title=dict(text="DATE", font=dict(color='#00FFFF', size=14)),
                    tickfont=dict(color='#FFFFFF')
                ),
                yaxis=dict(
                    gridcolor='#1a1a1a',
                    gridwidth=1,
                    color='#00FFFF',
                    showgrid=True,
                    title=dict(text=" STOCK PRICE ($)", font=dict(color='#00FFFF', size=14)),
                    tickfont=dict(color='#FFFFFF')
                ),
                
                # Chart dimensions
                width=1200,
                height=600,
                
                # Neon legend styling
                legend=dict(
                    bgcolor='rgba(0,0,0,0.9)',
                    bordercolor='#00FFFF',
                    borderwidth=2,
                    font=dict(color='#FFFFFF', size=11),
                    x=0.02,
                    y=0.98
                ),
                
                # Hover styling with neon colors
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor='#000000',
                    bordercolor='#00FFFF',
                    font=dict(color='#FFFFFF', size=12)
                )
            )

            # Save chart
            filename = f"stocks_line_plot{period}.html"
            filepath = os.path.join(folder_name, filename)
            fig.write_html(filepath)
            
            return f"CHART CREATED! \n Folder: {folder_name}\n Stocks: {', '.join(successful_symbols)}"

        except Exception as e:
            return f"Error creating chart: {str(e)}"


# Create tool instance
stock_line_plot = StockLinePlotTool()