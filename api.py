from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os
import json
import time
from typing import Optional
from datetime import datetime

# Import the financial analyst functionality
from tools.financial_tools import YFinanceStockTool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage

# Load environment variables
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
    print(f"Found .env file at: {dotenv_path}")
else:
    print("No .env file found. Please create one in the project root.")
    exit(1)

# Check if API key exists
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("OpenAI API key not found in environment variables. Please check your .env file.")
    exit(1)

# Initialize FastAPI
app = FastAPI(
    title="Financial Analyst API",
    description="API for analyzing stocks and generating financial reports",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Request models
class StockAnalysisRequest(BaseModel):
    symbol: str
    force_refresh: bool = False

# Response models
class StockAnalysisResponse(BaseModel):
    symbol: str
    report: str
    raw_data: Optional[dict] = None

# Cache for stock analysis to prevent repeated API calls
analysis_cache = {}
# Cache expiry time (10 minutes)
CACHE_EXPIRY = 600  

# Initialize tools
stock_tool = YFinanceStockTool()

def get_stock_tool():
    return Tool(
        name="stock_data_tool",
        func=stock_tool._run,
        description="""
        A tool for getting real-time and historical stock market data.
        Use this tool when you need specific stock information like:
        - Latest stock price from most recent trading day
        - Current price and trading volume
        - Historical price data
        - Company financials and metrics
        - Company information and business summary
        """
    )

# Initialize LLM
def load_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )

# Create the stock analysis agent
def create_stock_analysis_agent(symbol):
    llm = load_llm()
    
    tools = [get_stock_tool()]
    
    system_message = f"""You are a seasoned Wall Street analyst with 15+ years of experience in equity research.
    You're known for your meticulous analysis and data-driven insights.
    You ALWAYS base your analysis on real-time market data, never relying solely on pre-existing knowledge.
    You're an expert at interpreting financial metrics, market trends, and providing actionable insights.
    
    Your task is to analyze {symbol} stock using the stock_data_tool to fetch real-time data. Your analysis must include:

    1. Latest Trading Information (HIGHEST PRIORITY)
       - Latest stock price with specific date
       - Percentage change
       - Trading volume
       - Market status (open/closed)
       - Highlight if this is from the most recent trading session

    2. 52-Week Performance (CRITICAL)
       - 52-week high with exact date
       - 52-week low with exact date
       - Current price position relative to 52-week range
       - Calculate percentage from highs and lows

    3. Financial Deep Dive
       - Market capitalization
       - P/E ratio and other key metrics
       - Revenue growth and profit margins
       - Dividend information (if applicable)

    4. Technical Analysis
       - Recent price movements
       - Volume analysis
       - Key technical indicators

    5. Market Context
       - Business summary
       - Analyst recommendations
       - Key risk factors

    IMPORTANT: 
    - ALWAYS use the stock_data_tool to fetch real-time data
    - Begin your analysis with the latest price and 52-week data
    - Include specific dates for all price points
    - Clearly indicate when each price point was recorded
    - Calculate and show percentage changes
    - Verify all numbers with live data
    - Compare current metrics with historical trends"""
    
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        system_message=system_message
    )
    
    return agent

# Create the report writer chain
def create_report_writer_chain():
    llm = load_llm()
    
    # Get the current date
    current_date = datetime.now().strftime('%B %d, %Y')
    
    template = """You are an expert financial writer with a track record of creating institutional-grade research reports.
    You excel at presenting complex financial data in a clear, structured format.
    You always maintain professional standards while making reports accessible and actionable.
    You're known for your clear data presentation, trend analysis, and risk assessment capabilities.

    Transform the following financial analysis into a professional investment report:

    {analysis}

    Today's date is: {current_date}
    
    The report must:

    1. Structure:
       - Begin with an executive summary that explicitly mentions today's date ({current_date}) as the date of analysis
       - Use clear section headers
       - Include tables for data presentation
       - Add emoji indicators for trends (📈 📉)

    2. Content Requirements:
       - Include today's date ({current_date}) for any references to the current trading day
       - Present key metrics in tables
       - Use bullet points for key insights
       - Compare metrics to industry averages
       - Explain technical terms
       - Highlight potential risks

    3. Sections:
       - Executive Summary (start with "As of {current_date}, [company] is trading at...")
       - Market Position Overview
       - Financial Metrics Analysis
       - Technical Analysis
       - Risk Assessment
       - Future Outlook

    4. Formatting:
       - Use markdown formatting
       - Create tables for data comparison
       - Include trend emojis
       - Use bold for key metrics
       - Add bullet points for key takeaways

    IMPORTANT:
    - Always include today's date ({current_date}) in the executive summary
    - NEVER use placeholders like [Insert Date] - always use the actual date provided
    - Maintain professional tone
    - Clearly state all data sources
    - Include risk disclaimers
    - Format in clean, readable markdown"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["analysis", "current_date"]
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True
    )
    
    return chain, current_date

# Analyze stock and generate report
def analyze_stock(symbol, force_refresh=False):
    # Check cache first
    cache_key = symbol.upper()
    current_time = time.time()
    
    # If force refresh, remove from cache
    if force_refresh and cache_key in analysis_cache:
        print(f"Forcing refresh for {symbol} - clearing cache")
        del analysis_cache[cache_key]
    
    if not force_refresh and cache_key in analysis_cache:
        cached_time, cached_report, raw_data = analysis_cache[cache_key]
        # Return cached result if it's still valid
        if current_time - cached_time < CACHE_EXPIRY:
            print(f"Using cached result for {symbol}")
            return cached_report, raw_data

    try:
        print(f"Fetching fresh data for {symbol}")
        # Get raw stock data
        raw_data_json = stock_tool._run(symbol)
        raw_data = json.loads(raw_data_json)
        
        # Step 1: Create the stock analysis agent
        analysis_agent = create_stock_analysis_agent(symbol)
        
        # Step 2: Run the analysis
        analysis_result = analysis_agent.run(f"Perform a comprehensive analysis of {symbol} stock.")
        
        # Step 3: Create the report writer chain
        report_writer, current_date = create_report_writer_chain()
        
        # Step 4: Generate the report
        report = report_writer.run(analysis=analysis_result, current_date=current_date)
        
        # Step 5: Post-process the report to replace any remaining date placeholders
        report = report.replace("[Insert Date]", current_date)
        report = report.replace("[insert date]", current_date)
        report = report.replace("[TODAY'S DATE]", current_date)
        report = report.replace("[Current Date]", current_date)
        
        # Store in cache
        analysis_cache[cache_key] = (current_time, report, raw_data)
        
        return report, raw_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing stock: {str(e)}")

# API endpoints
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock_endpoint(request: StockAnalysisRequest):
    try:
        print(f"Received request: {request}")
        
        symbol = request.symbol.strip().upper()
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Stock symbol is required")
        
        print(f"Processing stock symbol: {symbol}")
        report, raw_data = analyze_stock(symbol, request.force_refresh)
        
        return StockAnalysisResponse(
            symbol=symbol,
            report=report,
            raw_data=raw_data
        )
    except Exception as e:
        print(f"Error in analyze_stock_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing stock: {str(e)}")

@app.post("/analyze2")
async def analyze_stock_direct(request: Request):
    try:
        # Get the raw JSON body
        body = await request.json()
        print(f"Raw request body: {body}")
        
        # Extract values manually
        symbol = body.get("symbol", "").strip().upper()
        force_refresh = body.get("force_refresh", False)
        
        print(f"Symbol: {symbol}, Force refresh: {force_refresh}")
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Stock symbol is required")
        
        # Process the stock
        report, raw_data = analyze_stock(symbol, force_refresh)
        
        # Return the response
        return {
            "symbol": symbol,
            "report": report,
            "raw_data": raw_data
        }
    except Exception as e:
        print(f"Error in analyze_stock_direct: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing stock: {str(e)}")

@app.get("/stock/{symbol}/data")
async def get_stock_data(symbol: str):
    try:
        raw_data_json = stock_tool._run(symbol)
        return JSONResponse(content=json.loads(raw_data_json))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")

@app.get("/stock/{symbol}/report")
async def get_stock_report(symbol: str):
    report, _ = analyze_stock(symbol)
    return {"symbol": symbol, "report": report}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 