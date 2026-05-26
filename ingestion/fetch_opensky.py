import os
import requests
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import bigquery


load_dotenv()

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# India bounding box
PARAMS = {
    "lamin": 6.0,
    "lomin": 68.0,
    "lamax": 37.0,
    "lomax": 97.0
}

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET")
BQ_TABLE = os.getenv("BQ_TABLE")

COLUMNS = [
    "icao24",
    "callsign",
    "origin_country",
    "time_position",
    "last_contact",
    "longitude",
    "latitude",
    "baro_altitude",
    "on_ground",
    "velocity",
    "true_track",
    "vertical_rate",
    "sensors",
    "geo_altitude",
    "squawk",
    "spi",
    "position_source"
]


def fetch_opensky_data():
    response = requests.get(OPENSKY_URL, params=PARAMS, timeout=30)

    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

    return response.json()


def convert_to_dataframe(data):
    states = data.get("states", [])

    if not states:
        print("No aircraft data received.")
        return pd.DataFrame(columns=COLUMNS)

    normalized_states = []

    for state in states:
        if len(state) < len(COLUMNS):
            state = state + [None] * (len(COLUMNS) - len(state))
        elif len(state) > len(COLUMNS):
            state = state[:len(COLUMNS)]

        normalized_states.append(state)

    df = pd.DataFrame(normalized_states, columns=COLUMNS)

    df["api_time"] = pd.to_datetime(
        data.get("time"),
        unit="s",
        utc=True,
        errors="coerce"
    )

    df["ingestion_time"] = datetime.now(timezone.utc)

    return df


def clean_data(df):
    if df.empty:
        return df

    df = df.dropna(subset=["latitude", "longitude"]).copy()

    df["callsign"] = df["callsign"].fillna("").astype(str).str.strip()

    df["time_position"] = pd.to_datetime(
        df["time_position"],
        unit="s",
        utc=True,
        errors="coerce"
    )

    df["last_contact"] = pd.to_datetime(
        df["last_contact"],
        unit="s",
        utc=True,
        errors="coerce"
    )

    numeric_columns = [
        "longitude",
        "latitude",
        "baro_altitude",
        "velocity",
        "true_track",
        "vertical_rate",
        "geo_altitude",
        "position_source"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["on_ground"] = df["on_ground"].astype(bool)
    df["spi"] = df["spi"].astype(bool)

    df["region"] = "India"

    df["speed_kmh"] = df["velocity"] * 3.6
    df["baro_altitude_ft"] = df["baro_altitude"] * 3.28084
    df["geo_altitude_ft"] = df["geo_altitude"] * 3.28084

    df["altitude_band"] = pd.cut(
        df["baro_altitude"],
        bins=[-1, 0, 5000, 10000, 12000, 20000],
        labels=[
            "Ground/Unknown",
            "0-5,000 m",
            "5,000-10,000 m",
            "10,000-12,000 m",
            "12,000+ m"
        ]
    )
    
    df["altitude_band"] = df["altitude_band"].astype(str)

    # BigQuery can later convert this WKT string into GEOGRAPHY
    df["aircraft_location_wkt"] = df.apply(
        lambda row: f"POINT({row['longitude']} {row['latitude']})",
        axis=1
    )

    final_columns = [
        "ingestion_time",
        "api_time",
        "icao24",
        "callsign",
        "origin_country",
        "time_position",
        "last_contact",
        "longitude",
        "latitude",
        "baro_altitude",
        "geo_altitude",
        "on_ground",
        "velocity",
        "speed_kmh",
        "true_track",
        "vertical_rate",
        "squawk",
        "spi",
        "position_source",
        "region",
        "baro_altitude_ft",
        "geo_altitude_ft",
        "altitude_band",
        "aircraft_location_wkt"
    ]

    return df[final_columns]


def save_to_csv(df):
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    file_name = f"opensky_india_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_path = output_dir / file_name

    df.to_csv(file_path, index=False)

    print(f"Saved CSV: {file_path}")
    print(f"Total records saved: {len(df)}")


def load_to_bigquery(df):
    if df.empty:
        print("No data to load into BigQuery.")
        return

    if not GCP_PROJECT_ID or not BQ_DATASET or not BQ_TABLE:
        raise ValueError("Missing GCP_PROJECT_ID, BQ_DATASET, or BQ_TABLE in .env file")

    client = bigquery.Client(project=GCP_PROJECT_ID)

    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True
    )

    load_job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=job_config
    )

    load_job.result()

    table = client.get_table(table_id)

    print(f"Loaded {len(df)} rows into BigQuery table: {table_id}")
    print(f"Total rows currently in table: {table.num_rows}")


def main():
    print("Fetching OpenSky data...")

    raw_data = fetch_opensky_data()

    print(f"API response time: {raw_data.get('time')}")
    print(f"Aircraft rows received from API: {len(raw_data.get('states', []))}")

    df = convert_to_dataframe(raw_data)
    clean_df = clean_data(df)

    print("\nSample data:")
    print(clean_df.head())

    save_to_csv(clean_df)

    print("\nLoading data to BigQuery...")
    load_to_bigquery(clean_df)

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()