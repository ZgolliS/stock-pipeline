import pandas as pd
from google.cloud import storage, bigquery
import os
from dotenv import load_dotenv
from io import StringIO

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BQ_DATASET = os.getenv("BQ_DATASET")
BQ_TABLE = "stock_prices"


def read_from_gcs(ticker: str, date_str: str) -> pd.DataFrame:
    """Lit un CSV depuis GCS"""
    client = storage.Client.from_service_account_json(CREDENTIALS)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"raw/{ticker}_{date_str}.csv")
    content = blob.download_as_text()
    return pd.read_csv(StringIO(content))


def transform(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Nettoie et enrichit les données"""
    df = df[["Date", "Open", "High", "Low", "Close", "Volume", "ticker"]]
    df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.date
    df.columns = ["date", "open", "high", "low", "close", "volume", "ticker"]
    df["daily_return"] = ((df["close"] - df["open"]) / df["open"] * 100).round(2)
    df = df.dropna()
    return df


def load_to_bigquery(df: pd.DataFrame):
    """Charge les données dans BigQuery"""
    client = bigquery.Client.from_service_account_json(CREDENTIALS)
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True
    )

    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"Chargé {len(df)} lignes dans BigQuery ✅")


def main():
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]

    all_data = []
    for ticker in tickers:
        print(f"Transformation {ticker}...")
        df = read_from_gcs(ticker, date_str)
        df = transform(df, ticker)
        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)
    load_to_bigquery(final_df)
    print("Transformation terminée 🎉")


if __name__ == "__main__":
    main()