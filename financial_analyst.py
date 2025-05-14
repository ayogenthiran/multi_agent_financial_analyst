import streamlit as st
# Set page config first, before any other Streamlit commands
st.set_page_config(page_title="Multi-Agent AI Financial Analyst", layout="wide")

import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel, Field
import json

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage

# Import custom tools
from tools.financial_tools import YFinanceStockTool

# Improved environment loading
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    st.stop()

# Define Pydantic models for structured output
class StockAnalysis(BaseModel):
    symbol: str
    company_name: str
    current_price: float
    market_cap: float
    pe_ratio: float
    recommendation: str
    analysis_summary: str
    risk_assessment: str
    technical_indicators: dict
    fundamental_metrics: dict

# Initialize OpenAI LLM 
@st.cache_resource
def load_llm():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found in environment variables. Please check your .env file.")
        st.stop()
    
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )

# Create financial tools
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

# Define the Stock Analysis Agent
def create_stock_analysis_agent(symbol):
    llm = load_llm()
    
    tools = [get_stock_tool()]
    
    # Using the exact same backstory and task description from the CrewAI implementation
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

# Define the Report Writer Chain
def create_report_writer_chain():
    llm = load_llm()
    
    # Using the exact same backstory and task description from the CrewAI implementation
    template = """You are an expert financial writer with a track record of creating institutional-grade research reports.
    You excel at presenting complex financial data in a clear, structured format.
    You always maintain professional standards while making reports accessible and actionable.
    You're known for your clear data presentation, trend analysis, and risk assessment capabilities.

    Transform the following financial analysis into a professional investment report:

    {analysis}

    The report must:

    1. Structure:
       - Begin with an executive summary
       - Use clear section headers
       - Include tables for data presentation
       - Add emoji indicators for trends (📈 📉)

    2. Content Requirements:
       - Include timestamps for all data points
       - Present key metrics in tables
       - Use bullet points for key insights
       - Compare metrics to industry averages
       - Explain technical terms
       - Highlight potential risks

    3. Sections:
       - Executive Summary
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
    - Maintain professional tone
    - Clearly state all data sources
    - Include risk disclaimers
    - Format in clean, readable markdown"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["analysis"]
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True
    )
    
    return chain

# Orchestrate the analysis and report generation
def analyze_stock(symbol):
    # Step 1: Create the stock analysis agent
    analysis_agent = create_stock_analysis_agent(symbol)
    
    # Step 2: Run the analysis
    analysis_result = analysis_agent.run(f"Perform a comprehensive analysis of {symbol} stock.")
    
    # Step 3: Create the report writer chain
    report_writer = create_report_writer_chain()
    
    # Step 4: Generate the report
    report = report_writer.run(analysis=analysis_result)
    
    return report

# Streamlit UI
st.title("🎯 Multi-Agent AI Financial Analyst")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    # Debug info for API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        pass
    else:
        st.error("OpenAI API key is not set ✗")
        st.info("Please check your .env file format: OPENAI_API_KEY=your_key_here")
    
    # Stock Symbol input
    symbol = st.text_input(
        "Stock Symbol",
        value="AAPL",
        help="Enter a stock symbol (e.g., AAPL, GOOGL)"
    ).upper()

    # Analysis button
    analyze_button = st.button("Analyze Stock", type="primary")

# Main content area
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
    st.session_state.report = None

if analyze_button:
    try:
        with st.spinner(f'Analyzing {symbol}... This may take a few minutes.'):
            # Run the analysis
            result = analyze_stock(symbol)
            st.session_state.report = result
            st.session_state.analysis_complete = True

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if st.session_state.analysis_complete and st.session_state.report:
    st.markdown("### Analysis Report")
    st.markdown(st.session_state.report)
    
    # Download button
    st.download_button(
        label="Download Report",
        data=st.session_state.report,
        file_name=f"stock_analysis_{symbol}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )

# Footer
st.markdown("---") 