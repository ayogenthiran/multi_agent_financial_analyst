import yfinance as yf
from datetime import datetime, timedelta
import json
import time
import random

class YFinanceStockTool:
    """Tool for getting real-time stock market data using YFinance."""
    name = "stock_data_tool"
    description = """
    A tool for getting real-time and historical stock market data.
    Use this tool when you need specific stock information like:
    - Latest stock price from most recent trading day
    - Current price and trading volume
    - Historical price data
    - Company financials and metrics
    - Company information and business summary
    """
    
    def _run(self, symbol: str) -> str:
        """Run the tool with the given stock symbol."""
        # Add retry mechanism for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stock = yf.Ticker(symbol)
                
                # Get basic info
                info = stock.info
                
                # Get recent market data (force refresh to get most current data)
                hist = stock.history(period="1mo", interval="1d", proxy=None, rounding=True, auto_adjust=True)
                
                # Add a small delay to avoid rate limiting
                time.sleep(random.uniform(0.5, 1.5))
                
                # Get the latest trading day's data
                if len(hist) > 0:
                    latest_data = hist.iloc[-1]
                    
                    # Fix date formatting to ensure we're using the current year
                    try:
                        latest_date_raw = latest_data.name
                        # If the date is a pandas Timestamp, convert it to a Python datetime
                        if hasattr(latest_date_raw, 'to_pydatetime'):
                            latest_date_raw = latest_date_raw.to_pydatetime()
                        
                        # Ensure the year is not in the future
                        current_year = datetime.now().year
                        if latest_date_raw.year > current_year:
                            # Adjust the date to use the current year
                            latest_date_raw = latest_date_raw.replace(year=current_year)
                        
                        latest_date = latest_date_raw.strftime('%Y-%m-%d')
                    except (AttributeError, TypeError):
                        # Fallback to today's date if there's any issue
                        latest_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # Calculate percent change from previous day
                    if len(hist) > 1:
                        prev_close = hist.iloc[-2]['Close']
                        percent_change = ((latest_data['Close'] - prev_close) / prev_close) * 100
                    else:
                        percent_change = ((latest_data['Close'] - latest_data['Open']) / latest_data['Open']) * 100
                else:
                    return f"No recent trading data available for {symbol}"
                
                # Get 1-year data for 52-week high/low
                time.sleep(random.uniform(0.5, 1.5))  # Add delay before another API call
                hist_1y = stock.history(period="1y")
                
                # Get dates for 52-week high and low
                if len(hist_1y) > 0:
                    fifty_two_week_high = hist_1y['High'].max()
                    fifty_two_week_low = hist_1y['Low'].min()
                    
                    # Fix high date
                    high_date_raw = hist_1y['High'].idxmax()
                    if hasattr(high_date_raw, 'to_pydatetime'):
                        high_date_raw = high_date_raw.to_pydatetime()
                    if high_date_raw.year > current_year:
                        high_date_raw = high_date_raw.replace(year=current_year)
                    fifty_two_week_high_date = high_date_raw.strftime('%Y-%m-%d')
                    
                    # Fix low date
                    low_date_raw = hist_1y['Low'].idxmin()
                    if hasattr(low_date_raw, 'to_pydatetime'):
                        low_date_raw = low_date_raw.to_pydatetime()
                    if low_date_raw.year > current_year:
                        low_date_raw = low_date_raw.replace(year=current_year)
                    fifty_two_week_low_date = low_date_raw.strftime('%Y-%m-%d')
                else:
                    fifty_two_week_high = info.get("fiftyTwoWeekHigh", "N/A")
                    fifty_two_week_low = info.get("fiftyTwoWeekLow", "N/A")
                    fifty_two_week_high_date = "N/A"
                    fifty_two_week_low_date = "N/A"
                
                # Get quarterly financials if available
                time.sleep(random.uniform(0.5, 1.5))  # Add delay before another API call
                try:
                    financials = stock.quarterly_financials
                    if financials is not None and not financials.empty:
                        revenue = financials.loc["Total Revenue"].iloc[0] if "Total Revenue" in financials.index else "N/A"
                        net_income = financials.loc["Net Income"].iloc[0] if "Net Income" in financials.index else "N/A"
                    else:
                        revenue = "N/A"
                        net_income = "N/A"
                except Exception:
                    revenue = "N/A"
                    net_income = "N/A"
                
                # Calculate current position relative to 52-week range
                if fifty_two_week_high != "N/A" and fifty_two_week_low != "N/A" and latest_data['Close'] != "N/A":
                    try:
                        range_position = (latest_data['Close'] - fifty_two_week_low) / (fifty_two_week_high - fifty_two_week_low) * 100
                        range_position_str = f"{range_position:.2f}%"
                    except (TypeError, ZeroDivisionError):
                        range_position_str = "N/A"
                else:
                    range_position_str = "N/A"
                
                # Get current date and time
                current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Prepare the response with more comprehensive data
                response = {
                    "data_timestamp": current_datetime,
                    "company_name": info.get("longName", "N/A"),
                    "latest_trading_data": {
                        "date": latest_date,
                        "price": round(latest_data['Close'], 2),
                        "volume": int(latest_data['Volume']),
                        "open": round(latest_data['Open'], 2),
                        "high": round(latest_data['High'], 2),
                        "low": round(latest_data['Low'], 2),
                        "change_percent": f"{percent_change:.2f}%",
                        "trading_status": "Market Closed" if datetime.now().time() < datetime.strptime("09:30", "%H:%M").time() or datetime.now().time() > datetime.strptime("16:00", "%H:%M").time() else "Market Open"
                    },
                    "52_week_data": {
                        "high": {
                            "price": fifty_two_week_high if fifty_two_week_high != "N/A" else "N/A",
                            "date": fifty_two_week_high_date
                        },
                        "low": {
                            "price": fifty_two_week_low if fifty_two_week_low != "N/A" else "N/A",
                            "date": fifty_two_week_low_date
                        },
                        "current_position_in_range": range_position_str
                    },
                    "financial_metrics": {
                        "market_cap": info.get("marketCap", "N/A"),
                        "pe_ratio": info.get("forwardPE", "N/A"),
                        "eps": info.get("trailingEPS", "N/A"),
                        "dividend_yield": f"{info.get('dividendYield', 0) * 100:.2f}%" if info.get('dividendYield') is not None else "N/A",
                        "beta": info.get("beta", "N/A"),
                        "revenue": revenue,
                        "net_income": net_income,
                        "profit_margin": info.get("profitMargins", "N/A")
                    },
                    "company_info": {
                        "sector": info.get("sector", "N/A"),
                        "industry": info.get("industry", "N/A"),
                        "website": info.get("website", "N/A"),
                        "full_time_employees": info.get("fullTimeEmployees", "N/A"),
                        "business_summary": info.get("longBusinessSummary", "N/A")
                    },
                    "analyst_data": {
                        "recommendation": info.get("recommendationKey", "N/A"),
                        "target_mean_price": info.get("targetMeanPrice", "N/A"),
                        "number_of_analyst_opinions": info.get("numberOfAnalystOpinions", "N/A")
                    }
                }
                
                return json.dumps(response, indent=2)
            
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    # If rate limited, wait longer before retrying
                    time.sleep(5 + random.uniform(1, 5) * attempt)
                    continue
                else:
                    return f"Error fetching data for {symbol}: {str(e)}"
        
        return f"Failed to fetch data for {symbol} after {max_retries} attempts due to rate limiting."

    def _arun(self, symbol: str) -> str:
        # Async implementation if needed
        raise NotImplementedError("Async version not implemented") 