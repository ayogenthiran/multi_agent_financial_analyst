# 🚀 AI Financial Analyst

A web application that performs comprehensive stock analysis and generates professional financial reports using AI.

## 🌟 Features

- **Real-time Stock Analysis**: Get detailed analysis of any publicly traded stock
- **Professional Report Generation**: AI-generated investment reports with executive summaries, market position, financial metrics, and more
- **Modern Web Interface**: Clean, responsive UI with intuitive controls
- **Real-time Market Data**: Integration with Yahoo Finance for the latest stock information
- **Automatic Caching**: Prevents redundant API calls and improves performance
- **One-click Report Download**: Download reports in markdown format
- **Data Transparency**: View raw stock data alongside the analysis

## 🔧 Tech Stack

- **Backend**: FastAPI
- **Frontend**: HTML, CSS, JavaScript
- **AI**: LangChain + OpenAI's GPT-4o mini
- **Data Source**: Yahoo Finance API
- **Design**: Responsive UI with modern CSS

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ayogenthiran/multi_agent_financial_analyst.git
   cd multi_agent_financial_analyst
   ```

2. **Set up a virtual environment:**
   ```bash
   # For macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # For Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **API Key Setup:**
   Create a `.env` file in the root directory:
   ```bash
   # .env file
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   
   Important: The `.env` file is included in `.gitignore` and should never be committed to the repository to protect your API keys.

## 🚀 Usage

1. **Start the FastAPI server:**
   ```bash
   # Make sure your virtual environment is activated
   python api.py
   ```

2. **Access the web interface:**
   Open your browser and go to `http://localhost:8000`

3. **Analyze a stock:**
   - Enter a stock symbol (e.g., AAPL, MSFT, GOOGL)
   - Click "Analyze Stock"
   - Wait for the analysis to complete
   - View the comprehensive report or download it

## 🧠 How It Works

The application uses a multi-stage AI pipeline:

### 1. Stock Analysis Agent

- Fetches real-time stock data using YFinance
- Performs comprehensive analysis including:
  - Latest price and trading information
  - 52-week high/low performance
  - Financial metrics (P/E ratio, market cap, etc.)
  - Technical analysis and price trends
  - Market context and business summary

### 2. Report Writer

- Transforms raw analysis into structured financial reports
- Creates professional investment recommendations
- Generates markdown-formatted content with:
  - Executive summary
  - Market position overview
  - Financial metrics analysis
  - Technical indicators
  - Risk assessment
  - Future outlook

## 📊 Features Added

- **Responsive UI**: Works on desktop and mobile devices
- **Real-time Date Handling**: Reports always show the current date
- **Loading Indicators**: Visual feedback during analysis
- **Error Handling**: Clear error messages for users
- **Data Refresh**: One-click updating of stock data
- **Raw Data Access**: Toggle to view the underlying JSON data
- **Download Reports**: Save analysis as markdown files

## 🔒 Environment Variables

The application requires the following environment variables to be set in your `.env` file:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key for GPT model access |

## 📝 License

This project is for demonstration purposes only. Not intended for actual investment decisions.

## 🙏 Acknowledgements

- OpenAI for the GPT models
- LangChain for the agent framework
- Yahoo Finance for market data
- FastAPI for the backend framework
