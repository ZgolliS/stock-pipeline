import yfinance as yf
import pandas as pd
from google.cloud import storage
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Config
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Actions qu'on va tracker
TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]


def fetch_stock_data(ticker: str) -> pd.DataFrame:
    """Récupère les données historiques d'une action"""
    print(f"Fetching data for {ticker}...")
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    df["ticker"] = ticker
    df.reset_index(inplace=True)
    return df


def upload_to_gcs(df: pd.DataFrame, ticker: str):
    """Upload le CSV brut dans GCS"""
    client = storage.Client.from_service_account_json(CREDENTIALS)
    bucket = client.bucket(BUCKET_NAME)

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"raw/{ticker}_{date_str}.csv"

    blob = bucket.blob(filename)
    blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
    print(f"Uploaded {filename} to GCS ✅")


def main():
    for ticker in TICKERS:
        df = fetch_stock_data(ticker)
        upload_to_gcs(df, ticker)
    print("Ingestion terminée 🎉")


if __name__ == "__main__":
    main()