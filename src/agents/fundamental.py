import yfinance as yf
import pandas as pd
from src.agents.schemas import FundamentalReport
from src.agents.llm_client import generate_structured_analysis

def fetch_fundamental_data(ticker_symbol: str) -> str:
    """Fetches the latest income statements and balance sheets using yfinance."""
    print(f"Fetching financial statements for {ticker_symbol}...")
    ticker = yf.Ticker(ticker_symbol)
    
    try:
        # Grab the two most recent annual reporting periods
        income_stmt = ticker.financials.iloc[:, 0:2] if not ticker.financials.empty else pd.DataFrame()
        balance_sheet = ticker.balance_sheet.iloc[:, 0:2] if not ticker.balance_sheet.empty else pd.DataFrame()
        
        # Format into a clean text block for the LLM
        data_str = "--- INCOME STATEMENT (Last 2 Years) ---\n"
        data_str += income_stmt.dropna(how="all").to_string() + "\n\n"
        
        data_str += "--- BALANCE SHEET (Last 2 Years) ---\n"
        data_str += balance_sheet.dropna(how="all").to_string() + "\n"
        
        return data_str
    except Exception as e:
        return f"Error fetching fundamental data: {str(e)}"

def run_fundamental_agent(ticker: str):
    raw_financials = fetch_fundamental_data(ticker)
    
    sys_prompt = "You are an expert Fundamental Analyst. Review the provided income statements and balance sheets. Assess the company's profitability trend and debt risk."
    user_prompt = f"Ticker: {ticker}\n\nFinancial Data:\n{raw_financials}"
    
    print("Analyzing fundamentals...")
    report = generate_structured_analysis(sys_prompt, user_prompt, FundamentalReport)
    return report

if __name__ == "__main__":
    # Test the agent in isolation
    report = run_fundamental_agent("AAPL")
    print("\n=== FUNDAMENTAL REPORT ===")
    print(report.model_dump_json(indent=2))