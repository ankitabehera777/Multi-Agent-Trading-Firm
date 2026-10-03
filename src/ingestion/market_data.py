import yfinance as yf
import pandas as pd
from src.ingestion.cache_config import retry_with_backoff, session

class MarketDataClient:
    def __init__(self):
        # Bind the cached session to the client instance
        self.session = session

    @retry_with_backoff()
    def fetch_historical_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches OHLCV data using the cached session.
        """
        # Pass the session into the Ticker object here
        stock = yf.Ticker(ticker, session=self.session)
        df = stock.history(start=start_date, end=end_date, auto_adjust=False)
        
        if df.empty:
            raise ValueError(f"No data found for {ticker} between {start_date} and {end_date}.")
            
        # Clean and normalize
        df = df[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
        df.reset_index(inplace=True)
        
        df.rename(columns={'Date': 'date', 'Adj Close': 'adj_close'}, inplace=True)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        return df

if __name__ == "__main__":
    client = MarketDataClient()
    # First run will fetch from the internet; subsequent runs within 24 hours will load instantly from SQLite
    aapl_data = client.fetch_historical_data("AAPL", "2023-01-01", "2023-12-31")
    print(aapl_data.head())